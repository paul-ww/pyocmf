"""German Eichrecht (calibration law) compliance checking.

This module provides compliance checkers for ensuring OCMF data complies with
German calibration law requirements (MID 2014/32/EU and PTB requirements).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pyocmf.ocmf import OCMF

if TYPE_CHECKING:
    from pyocmf.sections.payload import Payload
    from pyocmf.sections.reading import Reading

from pyocmf.sections.reading import MeterReadingReason, MeterStatus


class IssueSeverity(enum.StrEnum):
    """Severity level of a compliance issue."""

    ERROR = "error"
    WARNING = "warning"


class IssueCode(enum.StrEnum):
    """Eichrecht compliance issue codes."""

    # Reading-level issues
    METER_STATUS = "METER_STATUS"
    ERROR_FLAGS = "ERROR_FLAGS"
    TIME_SYNC = "TIME_SYNC"
    CL_BEGIN = "CL_BEGIN"
    CL_NEGATIVE = "CL_NEGATIVE"

    # Transaction-level issues
    NO_READINGS = "NO_READINGS"
    BEGIN_TX = "BEGIN_TX"
    END_TX = "END_TX"
    SERIAL_MISMATCH = "SERIAL_MISMATCH"
    OBIS_MISMATCH = "OBIS_MISMATCH"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    VALUE_REGRESSION = "VALUE_REGRESSION"
    TIME_REGRESSION = "TIME_REGRESSION"
    ID_MISMATCH = "ID_MISMATCH"


@dataclass
class EichrechtIssue:
    """Represents a calibration law compliance issue."""

    code: IssueCode
    message: str
    field: str | None = None
    severity: IssueSeverity = IssueSeverity.ERROR

    def __str__(self) -> str:
        """String representation of the issue."""
        prefix = f"[{self.field}] " if self.field else ""
        return f"{prefix}{self.message} ({self.code})"


def check_eichrecht_reading(reading: Reading, is_begin: bool = False) -> list[EichrechtIssue]:
    """Check a single reading for Eichrecht compliance.

    Args:
        reading: The reading to check
        is_begin: Whether this is a transaction begin reading (affects CL checking)

    Returns:
        List of compliance issues (empty if compliant)
    """
    issues: list[EichrechtIssue] = []

    # 1. Meter status must be OK ("G" = good)
    if reading.ST != MeterStatus.OK:
        issues.append(
            EichrechtIssue(
                code=IssueCode.METER_STATUS,
                message=f"Meter status must be 'G' (OK) for billing-relevant readings, got '{reading.ST}'",
                field="ST",
            )
        )

    # 2. Error flags must be empty for billing
    if reading.EF and reading.EF.strip():
        issues.append(
            EichrechtIssue(
                code=IssueCode.ERROR_FLAGS,
                message=f"Error flags must be empty for billing-relevant readings, got '{reading.EF}'",
                field="EF",
            )
        )

    # 3. Time synchronization check (informational)
    from pyocmf.sections.reading import TimeStatus

    if reading.time_status != TimeStatus.SYNCHRONIZED:
        # S = synchronized time (required for legal certainty)
        # U/I/R = unsynchronized/informative/relative (warnings only)
        issues.append(
            EichrechtIssue(
                code=IssueCode.TIME_SYNC,
                message=f"Time should be synchronized (status 'S') for billing, got '{reading.time_status.value}'",
                field="TM",
                severity=IssueSeverity.WARNING,
            )
        )

    # 4. Cumulated loss (CL) compliance check
    if reading.CL is not None:
        if is_begin and reading.CL != 0:
            issues.append(
                EichrechtIssue(
                    code=IssueCode.CL_BEGIN,
                    message=f"Cumulated loss (CL) must be 0 at transaction begin, got {reading.CL}",
                    field="CL",
                )
            )
        if reading.CL < 0:
            issues.append(
                EichrechtIssue(
                    code=IssueCode.CL_NEGATIVE,
                    message=f"Cumulated loss (CL) must be non-negative, got {reading.CL}",
                    field="CL",
                )
            )

    return issues


def _check_timestamp_ordering(
    begin_reading: Reading, end_reading: Reading
) -> EichrechtIssue | None:
    """Check that end timestamp is >= begin timestamp."""
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

    # 2. Find the billing-relevant readings (first for begin, last for end)
    begin_reading = begin.RD[0]
    end_reading = end.RD[-1]

    # 3. Verify transaction types
    if begin_reading.TX != MeterReadingReason.BEGIN:
        issues.append(
            EichrechtIssue(
                code=IssueCode.BEGIN_TX,
                message=f"Begin reading must have TX='B', got '{begin_reading.TX}'",
                field="RD[0].TX",
            )
        )

    if not end_reading.TX.is_end_reading():
        issues.append(
            EichrechtIssue(
                code=IssueCode.END_TX,
                message=f"'{end_reading.TX}' is not a valid end reading type",
                field=f"RD[{len(end.RD) - 1}].TX",
            )
        )

    # 4. Check individual readings
    issues.extend(check_eichrecht_reading(begin_reading, is_begin=True))
    issues.extend(check_eichrecht_reading(end_reading, is_begin=False))

    # 5. Verify serial numbers match
    begin_serial = begin.GS or begin.MS
    end_serial = end.GS or end.MS
    if begin_serial != end_serial:
        issues.append(
            EichrechtIssue(
                code=IssueCode.SERIAL_MISMATCH,
                message=f"Serial numbers must match: begin='{begin_serial}', end='{end_serial}'",
                field="GS/MS",
            )
        )

    # 6. Verify OBIS codes match
    # Compare OBIS objects by their string representation
    begin_obis = str(begin_reading.RI) if begin_reading.RI else None
    end_obis = str(end_reading.RI) if end_reading.RI else None
    if begin_obis != end_obis:
        issues.append(
            EichrechtIssue(
                code=IssueCode.OBIS_MISMATCH,
                message=f"OBIS codes must match: begin='{begin_obis}', end='{end_obis}'",
                field="RI",
            )
        )

    # 7. Verify units match
    if begin_reading.RU != end_reading.RU:
        issues.append(
            EichrechtIssue(
                code=IssueCode.UNIT_MISMATCH,
                message=f"Units must match: begin='{begin_reading.RU}', end='{end_reading.RU}'",
                field="RU",
            )
        )

    # 8. Verify reading value progression (end >= begin)
    if begin_reading.RV is not None and end_reading.RV is not None:
        if end_reading.RV < begin_reading.RV:
            issues.append(
                EichrechtIssue(
                    code=IssueCode.VALUE_REGRESSION,
                    message=f"End value ({end_reading.RV}) must be >= begin value ({begin_reading.RV})",
                    field="RV",
                )
            )

    # 9. Verify timestamp ordering
    if timestamp_issue := _check_timestamp_ordering(begin_reading, end_reading):
        issues.append(timestamp_issue)

    # 10. Verify identification consistency (if present)
    if begin.ID != end.ID:
        issues.append(
            EichrechtIssue(
                code=IssueCode.ID_MISMATCH,
                message=f"Identification data should match: begin='{begin.ID}', end='{end.ID}'",
                field="ID",
                severity=IssueSeverity.WARNING,
            )
        )

    return issues


def validate_transaction_pair(begin: OCMF, end: OCMF) -> bool:
    """Validate that two OCMF records form a valid transaction pair.

    This performs structural validation to ensure the records can be
    treated as a begin/end pair. It checks for Eichrecht compliance errors
    (warnings are ignored) plus additional structural requirements like
    consecutive pagination.

    For detailed issue reporting, use check_eichrecht_transaction() directly.

    Args:
        begin: OCMF record with transaction begin (TX=B)
        end: OCMF record with transaction end (TX=E/L/R/A/P)

    Returns:
        True if the records form a valid transaction pair (no errors)

    Examples:
        >>> begin = OCMF.from_string("OCMF|{...TX:B...}|...")
        >>> end = OCMF.from_string("OCMF|{...TX:E...}|...")
        >>> validate_transaction_pair(begin, end)
        True
    """
    # Check Eichrecht compliance (ignore warnings)
    issues = check_eichrecht_transaction(begin.payload, end.payload)
    if any(issue.severity == IssueSeverity.ERROR for issue in issues):
        return False

    # Additional structural check: pagination should be consecutive (if present)
    if begin.payload.PG and end.payload.PG:
        try:
            # Extract pagination numbers (e.g., "T1" -> 1, "T2" -> 2)
            begin_num = int(begin.payload.PG[1:])
            end_num = int(end.payload.PG[1:])
            # End should be begin + 1 for a proper pair
            if end_num != begin_num + 1:
                return False
        except (ValueError, IndexError):
            # If we can't parse pagination, skip this check
            pass

    return True
