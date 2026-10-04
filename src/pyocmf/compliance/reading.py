from __future__ import annotations

from pyocmf.compliance.models import EichrechtIssue, IssueCode, IssueSeverity
from pyocmf.core.reading import Reading
from pyocmf.enums.reading import MeterReadingReason, MeterStatus, TimeStatus


def check_eichrecht_reading(reading: Reading) -> list[EichrechtIssue]:
    """Check a single reading for Eichrecht compliance.

    Args:
        reading: The reading to check

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

    if reading.EF and "E" in reading.EF:
        issues.append(
            EichrechtIssue(
                code=IssueCode.ERROR_FLAGS,
                message=f"Energy error flag ('E') set on billing-relevant reading: '{reading.EF}'",
                field="EF",
            )
        )
    # A time error does not invalidate the energy value, matching the Transparenzsoftware
    if reading.EF and "t" in reading.EF:
        issues.append(
            EichrechtIssue(
                code=IssueCode.ERROR_FLAGS,
                message=f"Time error flag ('t') set on reading: '{reading.EF}'",
                field="EF",
                severity=IssueSeverity.WARNING,
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

    issues.extend(_check_cumulated_loss(reading))

    return issues


def _check_cumulated_loss(reading: Reading) -> list[EichrechtIssue]:
    # OCMF spec rules for CL; warnings only because the Transparenzsoftware ignores
    # CL and still verifies such records
    if reading.CL is None:
        return []

    issues = []
    if reading.RI is None or not reading.RI.is_accumulation_register:
        issues.append(
            EichrechtIssue(
                code=IssueCode.CL_REGISTER,
                message=(
                    f"Cumulated loss (CL) should only appear on accumulation registers "
                    f"(B0-B3, C0-C3), got RI '{reading.RI}'"
                ),
                field="CL",
                severity=IssueSeverity.WARNING,
            )
        )
    if reading.TX == MeterReadingReason.BEGIN and reading.CL != 0:
        issues.append(
            EichrechtIssue(
                code=IssueCode.CL_BEGIN,
                message=f"Cumulated loss (CL) should be 0 at transaction begin, got {reading.CL}",
                field="CL",
                severity=IssueSeverity.WARNING,
            )
        )
    if reading.CL < 0:
        issues.append(
            EichrechtIssue(
                code=IssueCode.CL_NEGATIVE,
                message=f"Cumulated loss (CL) should be non-negative, got {reading.CL}",
                field="CL",
                severity=IssueSeverity.WARNING,
            )
        )
    return issues
