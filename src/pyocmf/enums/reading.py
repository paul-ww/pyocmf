from __future__ import annotations

import enum
from typing import Annotated

from pydantic.types import StringConstraints


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

    def is_end_reading(self) -> bool:
        return self in {
            MeterReadingReason.END,
            MeterReadingReason.TERMINATION_LOCAL,
            MeterReadingReason.TERMINATION_REMOTE,
            MeterReadingReason.TERMINATION_ABORT,
            MeterReadingReason.TERMINATION_POWER_FAILURE,
        }


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


ErrorFlags = Annotated[str, StringConstraints(pattern=r"^[Et]*$")]
