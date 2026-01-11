from __future__ import annotations

from typing import TYPE_CHECKING

from pyocmf.compliance.models import EichrechtIssue, IssueCode, IssueSeverity
from pyocmf.compliance.reading_validator import (
    _get_billing_relevant_begin_reading,
    _get_billing_relevant_end_reading,
    check_eichrecht_reading,
)
from pyocmf.sections.reading import MeterReadingReason
from pyocmf.types.identifiers import UserAssignmentStatus

if TYPE_CHECKING:
    from pyocmf.ocmf import OCMF
    from pyocmf.sections.payload import Payload
    from pyocmf.sections.reading import Reading


def _check_field_match(
    begin_value: object,
    end_value: object,
    field_name: str,
    issue_code: IssueCode,
    description: str,
) -> EichrechtIssue | None:
    # Convert to strings for comparison (handles OBIS objects, enums, etc.)
    begin_str = str(begin_value) if begin_value is not None else None
    end_str = str(end_value) if end_value is not None else None

    if begin_str != end_str:
        return EichrechtIssue(
            code=issue_code,
            message=f"{description} must match: begin='{begin_value}', end='{end_value}'",
            field=field_name,
        )
    return None


def _check_timestamp_ordering(
    begin_reading: Reading, end_reading: Reading
) -> EichrechtIssue | None:
    if not (begin_reading.TM and end_reading.TM):
        return None

    try:
        if end_reading.timestamp < begin_reading.timestamp:
            return EichrechtIssue(
                code=IssueCode.TIME_REGRESSION,
                message=f"End timestamp ({end_reading.TM}) must be >= begin timestamp ({begin_reading.TM})",
                field="TM",
            )
    except ValueError as e:
        return EichrechtIssue(
            code=IssueCode.TIME_REGRESSION,
            message=f"Failed to parse timestamps for comparison: {e}",
            field="TM",
        )
    return None


def _validate_transaction_types(
    begin_reading: Reading,
    end_reading: Reading,
    end_reading_count: int,
) -> list[EichrechtIssue]:
    issues = []
    if begin_reading.TX != MeterReadingReason.BEGIN:
        issues.append(
            EichrechtIssue(
                code=IssueCode.BEGIN_TX,
                message=f"Begin reading must have TX='B', got '{begin_reading.TX}'",
                field="RD[0].TX",
            )
        )
    if end_reading.TX is None or not end_reading.TX.is_end_reading():
        issues.append(
            EichrechtIssue(
                code=IssueCode.END_TX,
                message=f"'{end_reading.TX}' is not a valid end reading type",
                field=f"RD[{end_reading_count - 1}].TX",
            )
        )
    return issues


def _validate_identification_level(payload: Payload, context: str) -> EichrechtIssue | None:
    if payload.IL is None:
        return None

    invalid_levels = {
        UserAssignmentStatus.UID_MISMATCH,
        UserAssignmentStatus.CERT_INCORRECT,
        UserAssignmentStatus.CERT_EXPIRED,
        UserAssignmentStatus.CERT_UNVERIFIED,
    }

    if payload.IL in invalid_levels:
        return EichrechtIssue(
            code=IssueCode.ID_LEVEL_INVALID,
            message=f"Identification level '{payload.IL}' indicates error and is not acceptable for billing ({context})",
            field="IL",
        )

    return None


def _validate_field_consistency(
    begin: Payload,
    end: Payload,
    begin_reading: Reading,
    end_reading: Reading,
) -> list[EichrechtIssue]:
    issues = []
    # Serial numbers
    begin_serial = begin.GS or begin.MS
    end_serial = end.GS or end.MS
    if issue := _check_field_match(
        begin_serial, end_serial, "GS/MS", IssueCode.SERIAL_MISMATCH, "Serial numbers"
    ):
        issues.append(issue)
    # OBIS codes
    if issue := _check_field_match(
        begin_reading.RI, end_reading.RI, "RI", IssueCode.OBIS_MISMATCH, "OBIS codes"
    ):
        issues.append(issue)
    # Units
    if issue := _check_field_match(
        begin_reading.RU, end_reading.RU, "RU", IssueCode.UNIT_MISMATCH, "Units"
    ):
        issues.append(issue)
    return issues


def _validate_value_progression(
    begin_reading: Reading,
    end_reading: Reading,
) -> list[EichrechtIssue]:
    issues = []
    # Value progression
    if begin_reading.RV is not None and end_reading.RV is not None:
        if end_reading.RV < begin_reading.RV:
            issues.append(
                EichrechtIssue(
                    code=IssueCode.VALUE_REGRESSION,
                    message=f"End value ({end_reading.RV}) must be >= begin value ({begin_reading.RV})",
                    field="RV",
                )
            )
    # Timestamp ordering
    if timestamp_issue := _check_timestamp_ordering(begin_reading, end_reading):
        issues.append(timestamp_issue)
    return issues


def _validate_pagination_consistency(
    begin: Payload,
    end: Payload,
) -> EichrechtIssue | None:
    if not (begin.PG and end.PG):
        return None

    try:
        begin_num = int(begin.PG[1:])
        end_num = int(end.PG[1:])
        if end_num != begin_num + 1:
            return EichrechtIssue(
                code=IssueCode.PAGINATION_INCONSISTENT,
                message=f"Pagination must be consecutive: begin='{begin.PG}', end='{end.PG}'",
                field="PG",
            )
    except (ValueError, IndexError):
        return EichrechtIssue(
            code=IssueCode.PAGINATION_INCONSISTENT,
            message=f"Failed to parse pagination numbers: begin='{begin.PG}', end='{end.PG}'",
            field="PG",
        )

    return None


def check_eichrecht_transaction(
    begin: Payload,
    end: Payload,
) -> list[EichrechtIssue]:
    """Check a complete charging transaction for Eichrecht compliance.

    Args:
        begin: Transaction begin payload (TX=B)
        end: Transaction end payload (TX=E/L/R/A/P)

    Returns:
        List of compliance issues (empty if compliant)
    """
    issues: list[EichrechtIssue] = []

    # 1. Check that we have readings
    if not begin.RD or not end.RD:
        issues.append(
            EichrechtIssue(
                code=IssueCode.NO_READINGS,
                message="Both begin and end payloads must contain readings (RD)",
                field="RD",
            )
        )
        return issues

    # 2. Find the billing-relevant readings
    begin_reading = _get_billing_relevant_begin_reading(begin)
    end_reading = _get_billing_relevant_end_reading(end)

    # Validate transaction types
    issues.extend(_validate_transaction_types(begin_reading, end_reading, len(end.RD)))

    # Individual reading validation
    issues.extend(check_eichrecht_reading(begin_reading, is_begin=True))
    issues.extend(check_eichrecht_reading(end_reading, is_begin=False))

    # Cross-reading validations
    issues.extend(_validate_field_consistency(begin, end, begin_reading, end_reading))
    issues.extend(_validate_value_progression(begin_reading, end_reading))

    # Identification level validation
    if issue := _validate_identification_level(begin, "begin"):
        issues.append(issue)
    if issue := _validate_identification_level(end, "end"):
        issues.append(issue)

    # Pagination consistency
    if issue := _validate_pagination_consistency(begin, end):
        issues.append(issue)

    # Informational checks (warnings only)
    if issue := _check_field_match(
        begin.ID, end.ID, "ID", IssueCode.ID_MISMATCH, "Identification data"
    ):
        # Override severity to WARNING (ID mismatch is informational)
        issue.severity = IssueSeverity.WARNING
        issues.append(issue)

    return issues


def validate_transaction_pair(begin: OCMF, end: OCMF) -> bool:
    """Validate transaction pair compliance (errors only, warnings ignored)."""
    issues = check_eichrecht_transaction(begin.payload, end.payload)
    return not any(issue.severity == IssueSeverity.ERROR for issue in issues)
