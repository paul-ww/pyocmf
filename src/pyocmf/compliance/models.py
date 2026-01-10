"""Eichrecht compliance issue models and types.

This module defines the data structures used for representing compliance
validation issues in the context of German calibration law (Eichrecht).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


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
    ID_LEVEL_INVALID = "ID_LEVEL_INVALID"
    PAGINATION_INCONSISTENT = "PAGINATION_INCONSISTENT"


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
