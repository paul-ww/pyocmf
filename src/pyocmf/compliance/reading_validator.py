"""Single reading validation for Eichrecht compliance.

This module provides validation functions for individual meter readings
according to German calibration law (Eichrecht) requirements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyocmf.compliance.models import EichrechtIssue, IssueCode, IssueSeverity
from pyocmf.sections.reading import MeterStatus, TimeStatus

if TYPE_CHECKING:
    from pyocmf.sections.payload import Payload
    from pyocmf.sections.reading import Reading


def _get_billing_relevant_begin_reading(payload: Payload) -> Reading:
    """Get the billing-relevant reading from a transaction begin payload.

    Per Eichrecht requirements, the first reading (RD[0]) in a begin payload
    is used for billing and compliance calculations.

    Args:
        payload: Transaction begin payload (must have RD)

    Returns:
        First reading from payload.RD
    """
    return payload.RD[0]


def _get_billing_relevant_end_reading(payload: Payload) -> Reading:
    """Get the billing-relevant reading from a transaction end payload.

    Per Eichrecht requirements, the last reading (RD[-1]) in an end payload
    is used for billing and compliance calculations.

    Args:
        payload: Transaction end payload (must have RD)

    Returns:
        Last reading from payload.RD
    """
    return payload.RD[-1]


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
