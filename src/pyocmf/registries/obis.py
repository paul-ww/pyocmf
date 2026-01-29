from __future__ import annotations

import enum
import re
from dataclasses import dataclass


class OBISCategory(enum.StrEnum):
    IMPORT = "import"
    EXPORT = "export"
    POWER = "power"
    OTHER = "other"


# Regex patterns for OBIS code classification
_ACCUMULATION_REGISTER_PATTERN = re.compile(r"01-00:[BC][0-3]\.08\.00$")
_TRANSACTION_REGISTER_PATTERN = re.compile(r"01-00:[BC][23]\.08\.00$")
_ACTIVE_ENERGY_PATTERN = re.compile(r"01-00:0[12]\.08\.00$")


def _normalize(obis_code: str) -> str:
    return obis_code.split("*")[0]


@dataclass
class OBISInfo:
    code: str
    description: str
    billing_relevant: bool
    category: OBISCategory

    @staticmethod
    def normalize(obis_code: str) -> str:
        return _normalize(obis_code)

    @staticmethod
    def from_code(obis_code: str) -> OBISInfo | None:
        normalized = _normalize(obis_code)
        return ALL_KNOWN_OBIS.get(normalized)

    def is_accumulation_register(self) -> bool:
        return bool(_ACCUMULATION_REGISTER_PATTERN.match(self.code))

    def is_transaction_register(self) -> bool:
        return bool(_TRANSACTION_REGISTER_PATTERN.match(self.code))


BILLING_RELEVANT_OBIS = {
    "01-00:B0.08.00": OBISInfo(
        "01-00:B0.08.00",
        "Total Import Mains Energy (energy at meter)",
        billing_relevant=True,
        category=OBISCategory.IMPORT,
    ),
    "01-00:B1.08.00": OBISInfo(
        "01-00:B1.08.00",
        "Total Import Device Energy (energy at device/car)",
        billing_relevant=True,
        category=OBISCategory.IMPORT,
    ),
    "01-00:B2.08.00": OBISInfo(
        "01-00:B2.08.00",
        "Transaction Import Mains Energy (session energy at meter)",
        billing_relevant=True,
        category=OBISCategory.IMPORT,
    ),
    "01-00:B3.08.00": OBISInfo(
        "01-00:B3.08.00",
        "Transaction Import Device Energy (session energy at device)",
        billing_relevant=True,
        category=OBISCategory.IMPORT,
    ),
    "01-00:C0.08.00": OBISInfo(
        "01-00:C0.08.00",
        "Total Export Mains Energy",
        billing_relevant=True,
        category=OBISCategory.EXPORT,
    ),
    "01-00:C1.08.00": OBISInfo(
        "01-00:C1.08.00",
        "Total Export Device Energy",
        billing_relevant=True,
        category=OBISCategory.EXPORT,
    ),
    "01-00:C2.08.00": OBISInfo(
        "01-00:C2.08.00",
        "Transaction Export Mains Energy",
        billing_relevant=True,
        category=OBISCategory.EXPORT,
    ),
    "01-00:C3.08.00": OBISInfo(
        "01-00:C3.08.00",
        "Transaction Export Device Energy",
        billing_relevant=True,
        category=OBISCategory.EXPORT,
    ),
}

COMMON_OBIS = {
    "01-00:00.08.06": OBISInfo(
        "01-00:00.08.06",
        "Charging duration (time-based)",
        billing_relevant=False,
        category=OBISCategory.OTHER,
    ),
    "01-00:01.08.00": OBISInfo(
        "01-00:01.08.00",
        "Active energy import (+A) total",
        billing_relevant=True,
        category=OBISCategory.IMPORT,
    ),
    "01-00:02.08.00": OBISInfo(
        "01-00:02.08.00",
        "Active energy export (-A) total",
        billing_relevant=True,
        category=OBISCategory.EXPORT,
    ),
    "01-00:16.07.00": OBISInfo(
        "01-00:16.07.00",
        "Sum active power (total)",
        billing_relevant=False,
        category=OBISCategory.POWER,
    ),
}

LEGACY_OBIS = {
    "1-b:1.8.0": OBISInfo(
        "1-b:1.8.0",
        "Active energy import (+A) - legacy format",
        billing_relevant=True,
        category=OBISCategory.IMPORT,
    ),
    "1-b:2.8.0": OBISInfo(
        "1-b:2.8.0",
        "Active energy export (-A) - legacy format",
        billing_relevant=True,
        category=OBISCategory.EXPORT,
    ),
}

ALL_KNOWN_OBIS = {**BILLING_RELEVANT_OBIS, **COMMON_OBIS, **LEGACY_OBIS}


def normalize_obis_code(obis_code: str) -> str:
    return _normalize(obis_code)


def get_obis_info(obis_code: str) -> OBISInfo | None:
    return OBISInfo.from_code(obis_code)


def is_billing_relevant(obis_code: str) -> bool:
    normalized = _normalize(obis_code)

    if normalized in ALL_KNOWN_OBIS:
        return ALL_KNOWN_OBIS[normalized].billing_relevant

    if _ACCUMULATION_REGISTER_PATTERN.match(normalized):
        return True

    if _ACTIVE_ENERGY_PATTERN.match(normalized):
        return True

    return False


def is_accumulation_register(obis_code: str) -> bool:
    normalized = _normalize(obis_code)
    return bool(_ACCUMULATION_REGISTER_PATTERN.match(normalized))


def is_transaction_register(obis_code: str) -> bool:
    normalized = _normalize(obis_code)
    return bool(_TRANSACTION_REGISTER_PATTERN.match(normalized))


def validate_obis_for_billing(obis_code: str | None) -> tuple[bool, str | None]:
    if obis_code is None:
        return False, "OBIS code (RI) is required for billing-relevant readings"

    normalized = _normalize(obis_code)

    if not is_billing_relevant(obis_code):
        return False, f"OBIS code '{normalized}' is not billing-relevant"

    return True, None
