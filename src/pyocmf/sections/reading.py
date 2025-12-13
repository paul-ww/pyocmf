import decimal
import enum
from typing import Annotated

import pydantic

from pyocmf.types.units import OCMFUnit


class ReadingType(enum.StrEnum):
    AC = "AC"
    DC = "DC"


class MeterReadingReason(enum.StrEnum):
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
    UNKNOWN_OR_UNSYNCHRONIZED = "U"
    INFORMATIVE = "I"
    SYNCHRONIZED = "S"
    RELATIVE = "R"


# Time format: ISO 8601 with time status suffix
OCMFTimeFormat = Annotated[
    str,
    pydantic.constr(
        pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2},\d{3}[+-]\d{4} [UISR]$"
    ),
]

# Error flags can be a string containing 'E' and/or 't' characters
ErrorFlags = Annotated[str, pydantic.constr(pattern=r"^[Et]*$")]

# OBIS Code validation pattern according to spec
ObisCode = Annotated[
    str,
    pydantic.constr(
        pattern=r"^[0-9A-F]{2}-[0-9A-F]{2}:[0-9A-F]{2}\.[0-9A-F]{2}\.[0-9A-F]{2}\*[0-9A-F]{2}$"
    ),
]


class Reading(pydantic.BaseModel):
    TM: OCMFTimeFormat = pydantic.Field(
        description="Time (ISO 8601 + time status) - REQUIRED"
    )
    TX: MeterReadingReason | None = pydantic.Field(
        default=None, description="Transaction"
    )
    RV: decimal.Decimal | None = pydantic.Field(
        default=None,
        description="Reading Value - Conditional (required when RI present)",
    )
    RI: ObisCode | None = pydantic.Field(
        default=None, description="Reading Identification (OBIS code) - Conditional"
    )
    RU: OCMFUnit = pydantic.Field(description="Reading Unit - REQUIRED")
    RT: ReadingType | None = pydantic.Field(
        default=None, description="Reading Current Type"
    )
    CL: decimal.Decimal | None = pydantic.Field(
        default=None, description="Cumulated Losses"
    )
    EF: ErrorFlags | None = pydantic.Field(
        default=None, description="Error Flags (can contain 'E', 't', or both)"
    )
    ST: MeterStatus = pydantic.Field(description="Status - REQUIRED")

    @pydantic.field_validator("EF", mode="before")
    def ef_empty_string_to_none(cls, v: str | None) -> ErrorFlags | None:
        if v == "":
            return None
        return v
