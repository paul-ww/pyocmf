import enum


class ResistanceUnit(enum.StrEnum):
    """Resistance units as defined in OCMF spec Table 20."""

    MOHM = "mOhm"
    UOHM = "uOhm"


class EnergyUnit(enum.StrEnum):
    """Energy units as defined in OCMF spec Table 20."""

    KWH = "kWh"
    WH = "Wh"


# OCMFUnit includes only units defined in OCMF spec Table 20
OCMFUnit = ResistanceUnit | EnergyUnit
