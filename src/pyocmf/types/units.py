"""Measurement units used in OCMF meter readings.

This module defines the various units of measurement that can be used
in OCMF meter readings, including resistance, energy, and time units.
"""

import enum


class ResistanceUnit(enum.StrEnum):
    """Units for electrical resistance measurements."""

    MOHM = "mOhm"
    OHM = "Ohm"


class EnergyUnit(enum.StrEnum):
    """Units for electrical energy measurements."""

    KWH = "kWh"
    WH = "Wh"


class TimeUnit(enum.StrEnum):
    """Units for time duration measurements."""

    SEC = "sec"
    MIN = "min"
    H = "h"


OCMFUnit = ResistanceUnit | EnergyUnit | TimeUnit
