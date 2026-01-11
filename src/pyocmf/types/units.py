import enum


class ResistanceUnit(enum.StrEnum):
    MOHM = "mOhm"
    OHM = "Ohm"


class EnergyUnit(enum.StrEnum):
    KWH = "kWh"
    WH = "Wh"


class TimeUnit(enum.StrEnum):
    SEC = "sec"
    MIN = "min"
    H = "h"


OCMFUnit = ResistanceUnit | EnergyUnit | TimeUnit
