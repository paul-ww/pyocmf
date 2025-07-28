import enum

class ResistanceUnit(enum.StrEnum):
    MOHM = "mOhm"
    OHM = "Ohm"

class EnergyUnit(enum.StrEnum):
    KWH = "kWh"
    WH = "Wh"

OCMFUnit = ResistanceUnit | EnergyUnit
