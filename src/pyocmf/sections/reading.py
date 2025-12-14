"""OCMF meter reading types and models.

This module defines the various enums and models used for representing
meter readings in OCMF format, including reading types, statuses, and values.
"""

import decimal
import enum
from typing import Annotated

import pydantic

from pyocmf.types.units import OCMFUnit


class ReadingType(enum.StrEnum):
    """Type of electrical current in the meter reading."""

    AC = "AC"
    DC = "DC"


class MeterReadingReason(enum.StrEnum):
    """Reason or trigger for a meter reading."""

    BEGIN = "B"
    CHARGING = "C"
    EXCEPTION = "X"
    END = "E"
    TERMINATION_LOCAL = "L"
    TERMINATION_REMOTE = "R"
    TERMINATION_ABORT = "A"
    TERMINATION_POWER_FAILURE = "P"
    SUSPENDED = "S"
    TARIFF_CHANGE = "T"


class MeterStatus(enum.StrEnum):
    """Status of the meter at the time of reading."""

    NOT_PRESENT = "N"
    OK = "G"
    TIMEOUT = "T"
    DISCONNECTED = "D"
    NOT_FOUND = "R"
    MANIPULATED = "M"
    EXCHANGED = "X"
    INCOMPATIBLE = "I"
    OUT_OF_RANGE = "O"
    SUBSTITUTE = "S"
    OTHER_ERROR = "E"
    READ_ERROR = "F"


class TimeStatus(enum.StrEnum):
    """Synchronization status of the timestamp."""

    UNKNOWN_OR_UNSYNCHRONIZED = "U"
    INFORMATIVE = "I"
    SYNCHRONIZED = "S"
    RELATIVE = "R"


# OCMF time format: ISO 8601 with milliseconds, timezone, and status flag
# (e.g., "2023-06-15T14:30:45,123+0200 S" where S=Synchronized, U=Unknown, I=Informative, R=Relative)
OCMFTimeFormat = Annotated[
    str,
    pydantic.constr(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2},\d{3}[+-]\d{4} [UISR]$"),
]

# Error flags: Empty string or combination of 'E' (error) and 't' (test/tariff change)
# (e.g., "", "E", "t", "Et")
ErrorFlags = Annotated[str, pydantic.constr(pattern=r"^[Et]*$")]

# OBIS code: 6 hex byte pairs with specific separators (e.g., "01-00:01.08.00*FF")
ObisCode = Annotated[
    str,
    pydantic.constr(
        pattern=r"^[0-9A-F]{2}-[0-9A-F]{2}:[0-9A-F]{2}\.[0-9A-F]{2}\.[0-9A-F]{2}\*[0-9A-F]{2}$"
    ),
]


class Reading(pydantic.BaseModel):
    """A single meter reading with timestamp and associated metadata.

    Represents one meter reading taken during a charging session, including
    the meter value, timestamp, status, and other relevant information.
    """

    TM: OCMFTimeFormat = pydantic.Field(description="Time (ISO 8601 + time status) - REQUIRED")
    TX: MeterReadingReason | None = pydantic.Field(default=None, description="Transaction")
    RV: decimal.Decimal | None = pydantic.Field(
        default=None,
        description="Reading Value - Conditional (required when RI present)",
    )
    RI: ObisCode | None = pydantic.Field(
        default=None, description="Reading Identification (OBIS code) - Conditional"
    )
    RU: OCMFUnit = pydantic.Field(description="Reading Unit - REQUIRED")
    RT: ReadingType | None = pydantic.Field(default=None, description="Reading Current Type")
    CL: decimal.Decimal | None = pydantic.Field(default=None, description="Cumulated Losses")
    EF: ErrorFlags | None = pydantic.Field(
        default=None, description="Error Flags (can contain 'E', 't', or both)"
    )
    ST: MeterStatus = pydantic.Field(description="Status - REQUIRED")

    @pydantic.field_validator("EF", mode="before")
    @classmethod
    def ef_empty_string_to_none(cls, v: str | None) -> ErrorFlags | None:
        """Convert empty error flag strings to None."""
        if v == "":
            return None
        return v
