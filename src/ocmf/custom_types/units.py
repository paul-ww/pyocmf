from typing import Literal

ResistanceUnit = Literal[
    "mOhm",
    "Ohm",
]

EnergyUnit = Literal[
    "kWh",
    "Wh",
]

OCMFUnit = ResistanceUnit | EnergyUnit
