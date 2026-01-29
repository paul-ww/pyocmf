from __future__ import annotations

from pyocmf.compliance.models import EichrechtIssue, IssueCode, IssueSeverity
from pyocmf.core.reading import Reading
from pyocmf.enums.reading import MeterStatus, TimeStatus


def check_eichrecht_reading(reading: Reading, is_begin: bool = False) -> list[EichrechtIssue]:
    """Check a single reading for Eichrecht compliance.

    Args:
        reading: The reading to check
        is_begin: Whether this is a transaction begin reading (affects CL checking)

    Returns:
        List of compliance issues (empty if compliant)

    """
    issues: list[EichrechtIssue] = []

    if reading.ST != MeterStatus.OK:
        issues.append(
            EichrechtIssue(
                code=IssueCode.METER_STATUS,
                message=(
                    f"Meter status must be 'G' (OK) for billing-relevant readings, "
                    f"got '{reading.ST}'"
                ),
                field="ST",
            )
        )

    if reading.EF and reading.EF.strip():
        issues.append(
            EichrechtIssue(
                code=IssueCode.ERROR_FLAGS,
                message=(
                    f"Error flags must be empty for billing-relevant readings, got '{reading.EF}'"
                ),
                field="EF",
            )
        )

    if reading.time_status != TimeStatus.SYNCHRONIZED:
        issues.append(
            EichrechtIssue(
                code=IssueCode.TIME_SYNC,
                message=(
                    f"Time should be synchronized (status 'S') for billing, "
                    f"got '{reading.time_status.value}'"
                ),
                field="TM",
                severity=IssueSeverity.WARNING,
            )
        )

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
