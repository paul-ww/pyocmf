import pydantic
import datetime
import enum
import decimal
from typing import Literal
from ocmf.custom_types.units import EnergyUnit


ObisCode = str  # TODO: replace with regex

ReadingType = Literal["AC", "DC"]


class MeterReadingReason(str, enum.Enum):
    begin = "B"
    charging = "C"
    exception = "X"
    end = "E"
    termination_local = "L"
    termination_remote = "R"
    termination_abort = "A"
    termination_power_failure = "P"
    suspended = "S"
    tariff_change = "T"


class ErrorFlag(str, enum.Enum):
    energy = "E"
    time = "t"


class MeterStatus(str, enum.Enum):
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


class TimeStatus(str, enum.Enum):
    UNKNOWN_OR_UNSYNCHRONIZED = "U"
    INFORMATIVE = "I"
    SYNCHRONIZED = "S"
    RELATIVE = "R"


OCMFTimeFormat = (
    str  # TODO: combine pydantic datetime validation with time status into custom type
)


class Reading(pydantic.BaseModel):
    TM: OCMFTimeFormat = pydantic.Field(description="Time (ISO 8601 + time status)")
    TX: MeterReadingReason | None = pydantic.Field(description="Transaction")
    RV: decimal.Decimal = pydantic.Field(description="Reading Value")
    RI: ObisCode = pydantic.Field(description="Reading Identification (OBIS code)")
    RU: EnergyUnit = pydantic.Field(description="Reading Unit")
    RT: ReadingType | None = pydantic.Field(description="Reading Current Type")
    CL: decimal.Decimal | None = pydantic.Field(description="Cumulated Losses")
    EF: ErrorFlag = pydantic.Field(description="Error Flag")
    ST: MeterStatus = pydantic.Field(description="Status")
