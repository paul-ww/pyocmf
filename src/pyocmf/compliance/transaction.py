from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pyocmf.compliance.models import EichrechtIssue, IssueCode, IssueSeverity
from pyocmf.compliance.reading import check_eichrecht_reading
from pyocmf.enums.identifiers import UserAssignmentStatus
from pyocmf.enums.reading import MeterReadingReason, TimeStatus, is_end_reason

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pyocmf.core.ocmf import OCMF
    from pyocmf.core.payload import Payload
    from pyocmf.core.reading import Reading

_PAGINATION_PATTERN = re.compile(r"^([TF])([0-9]+)$")

_INVALID_ID_LEVELS = {
    UserAssignmentStatus.UID_MISMATCH,
    UserAssignmentStatus.CERT_INCORRECT,
    UserAssignmentStatus.CERT_EXPIRED,
    UserAssignmentStatus.CERT_UNVERIFIED,
}


def _check_field_match(
    begin_value: object,
    end_value: object,
    field_name: str,
    issue_code: IssueCode,
    description: str,
) -> EichrechtIssue | None:
    begin_str = str(begin_value) if begin_value is not None else None
    end_str = str(end_value) if end_value is not None else None

    if begin_str != end_str:
        return EichrechtIssue(
            code=issue_code,
            message=f"{description} must match: begin='{begin_value}', end='{end_value}'",
            field=field_name,
        )
    return None


def _law_relevant_readings(readings: Sequence[Reading]) -> list[Reading]:
    """Select the readings a transaction is billed on, as the Transparenzsoftware does.

    Loss-compensated registers take precedence over the other law-relevant energy
    registers. Falls back to all readings when no register is recognised, so
    readings with unknown OBIS codes are still checked.
    """
    compensated = [r for r in readings if r.RI is not None and r.RI.is_loss_compensated]
    if compensated:
        return compensated
    law_relevant = [r for r in readings if r.RI is not None and r.RI.is_law_relevant]
    return law_relevant or list(readings)


def _select_transaction_readings(
    readings: Sequence[Reading],
) -> tuple[Reading | None, Reading | None, list[EichrechtIssue]]:
    relevant = _law_relevant_readings(readings)
    begins = [r for r in relevant if r.TX == MeterReadingReason.BEGIN]
    ends = [r for r in relevant if is_end_reason(r.TX)]

    issues = []
    if not begins:
        issues.append(
            EichrechtIssue(
                code=IssueCode.BEGIN_TX,
                message="No begin reading (TX='B') found",
                field="TX",
            )
        )
    elif len(begins) > 1:
        issues.append(
            EichrechtIssue(
                code=IssueCode.MULTIPLE_BEGIN,
                message=f"Expected exactly one begin reading, found {len(begins)}",
                field="TX",
            )
        )
    if not ends:
        issues.append(
            EichrechtIssue(
                code=IssueCode.END_TX,
                message="No end reading (TX in 'E', 'L', 'R', 'A', 'P') found",
                field="TX",
            )
        )
    elif len(ends) > 1:
        issues.append(
            EichrechtIssue(
                code=IssueCode.MULTIPLE_END,
                message=f"Expected exactly one end reading, found {len(ends)}",
                field="TX",
            )
        )

    begin = begins[0] if begins else None
    end = ends[-1] if ends else None
    return begin, end, issues


def _check_timestamp_ordering(
    begin_reading: Reading, end_reading: Reading
) -> EichrechtIssue | None:
    try:
        regressed = end_reading.timestamp < begin_reading.timestamp
    except TypeError:
        return EichrechtIssue(
            code=IssueCode.TIME_REGRESSION,
            message=(
                f"Cannot compare timestamps with and without UTC offset: "
                f"begin='{begin_reading.timestamp}', end='{end_reading.timestamp}'"
            ),
            field="TM",
        )
    if regressed:
        return EichrechtIssue(
            code=IssueCode.TIME_REGRESSION,
            message=(
                f"End timestamp ({end_reading.TM}) must be >= begin timestamp ({begin_reading.TM})"
            ),
            field="TM",
        )
    return None


def _check_transaction_readings(begin: Reading, end: Reading) -> list[EichrechtIssue]:
    issues = []
    if issue := _check_field_match(begin.RI, end.RI, "RI", IssueCode.OBIS_MISMATCH, "OBIS codes"):
        issues.append(issue)
    if issue := _check_field_match(begin.RU, end.RU, "RU", IssueCode.UNIT_MISMATCH, "Units"):
        issues.append(issue)
    if begin.RV is not None and end.RV is not None and end.RV < begin.RV:
        issues.append(
            EichrechtIssue(
                code=IssueCode.VALUE_REGRESSION,
                message=f"End value ({end.RV}) must be >= begin value ({begin.RV})",
                field="RV",
            )
        )
    if issue := _check_timestamp_ordering(begin, end):
        issues.append(issue)
    if begin.time_status == TimeStatus.RELATIVE and end.time_status != TimeStatus.RELATIVE:
        issues.append(
            EichrechtIssue(
                code=IssueCode.TIME_SYNC,
                message=(f"Begin uses relative time ('R') but end does not ('{end.time_status}')"),
                field="TM",
            )
        )
    return issues


def _check_identification_level(payload: Payload, context: str) -> EichrechtIssue | None:
    if payload.IL not in _INVALID_ID_LEVELS:
        return None
    return EichrechtIssue(
        code=IssueCode.ID_LEVEL_INVALID,
        message=(
            f"Identification level '{payload.IL}' indicates error and is not "
            f"acceptable for billing ({context})"
        ),
        field="IL",
    )


def _check_pagination(begin: Payload, end: Payload) -> EichrechtIssue | None:
    begin_match = _PAGINATION_PATTERN.match(begin.PG or "")
    end_match = _PAGINATION_PATTERN.match(end.PG or "")
    # Malformed pagination is already reported as a SpecWarning when parsing
    if begin_match is None or end_match is None:
        return None

    begin_context, begin_number = begin_match.groups()
    end_context, end_number = end_match.groups()
    if begin_context != end_context:
        return EichrechtIssue(
            code=IssueCode.PAGINATION_INCONSISTENT,
            message=(
                f"Pagination context must match: begin='{begin.PG}', end='{end.PG}' "
                f"(different counters for transaction and fiscal contexts)"
            ),
            field="PG",
        )

    # The counter increments for every record, so intermediate records leave gaps
    if int(end_number) <= int(begin_number):
        return EichrechtIssue(
            code=IssueCode.PAGINATION_INCONSISTENT,
            message=f"End pagination should follow begin: begin='{begin.PG}', end='{end.PG}'",
            field="PG",
            severity=IssueSeverity.WARNING,
        )
    return None


def _contains_complete_transaction(payload: Payload) -> bool:
    return (
        payload.PG is not None
        and payload.PG.startswith("T")
        and any(r.TX == MeterReadingReason.BEGIN for r in payload.RD)
        and any(is_end_reason(r.TX) for r in payload.RD)
    )


def check_eichrecht_payload(payload: Payload) -> list[EichrechtIssue]:
    """Check a single payload for Eichrecht compliance.

    Every reading is checked individually. A payload holding a complete transaction
    (begin and end reading in the transaction context) is additionally checked like a
    begin/end pair.
    """
    if not payload.RD:
        return [
            EichrechtIssue(
                code=IssueCode.NO_READINGS,
                message="No readings (RD) present in payload",
                field="RD",
            )
        ]

    issues: list[EichrechtIssue] = []
    for reading in payload.RD:
        issues.extend(check_eichrecht_reading(reading))

    if _contains_complete_transaction(payload):
        begin, end, selection_issues = _select_transaction_readings(payload.RD)
        issues.extend(selection_issues)
        if begin is not None and end is not None:
            issues.extend(_check_transaction_readings(begin, end))
        if issue := _check_identification_level(payload, "transaction"):
            issues.append(issue)

    return issues


def check_eichrecht_transaction(
    begin: Payload,
    end: Payload,
) -> list[EichrechtIssue]:
    """Check a complete charging transaction for Eichrecht compliance."""
    if not begin.RD or not end.RD:
        return [
            EichrechtIssue(
                code=IssueCode.NO_READINGS,
                message="Both begin and end payloads must contain readings (RD)",
                field="RD",
            )
        ]

    begin_reading, end_reading, issues = _select_transaction_readings([*begin.RD, *end.RD])

    if begin_reading is not None:
        issues.extend(check_eichrecht_reading(begin_reading))
    if end_reading is not None:
        issues.extend(check_eichrecht_reading(end_reading))
    if begin_reading is not None and end_reading is not None:
        issues.extend(_check_transaction_readings(begin_reading, end_reading))

    if issue := _check_field_match(
        begin.GS or begin.MS, end.GS or end.MS, "GS/MS", IssueCode.SERIAL_MISMATCH, "Serial numbers"
    ):
        issues.append(issue)

    for payload, context in ((begin, "begin"), (end, "end")):
        if issue := _check_identification_level(payload, context):
            issues.append(issue)

    if issue := _check_pagination(begin, end):
        issues.append(issue)

    if issue := _check_field_match(
        begin.ID, end.ID, "ID", IssueCode.ID_MISMATCH, "Identification data"
    ):
        issue.severity = IssueSeverity.WARNING
        issues.append(issue)

    return issues


def validate_transaction_pair(begin: OCMF, end: OCMF) -> bool:
    """Validate transaction pair compliance (errors only, warnings ignored)."""
    issues = check_eichrecht_transaction(begin.payload, end.payload)
    return not any(issue.severity == IssueSeverity.ERROR for issue in issues)
