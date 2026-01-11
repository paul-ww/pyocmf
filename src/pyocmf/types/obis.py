from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Annotated

import pydantic
from pydantic import BeforeValidator


class OBISCategory(enum.StrEnum):
    IMPORT = "import"
    EXPORT = "export"
    POWER = "power"
    OTHER = "other"


@dataclass
class OBISInfo:
    code: str
    description: str
    billing_relevant: bool
    category: OBISCategory

    @staticmethod
    def normalize(obis_code: str) -> str:
        # Remove asterisk and everything after it
        return obis_code.split("*")[0]

    @staticmethod
    def from_code(obis_code: str) -> OBISInfo | None:
        normalized = OBISInfo.normalize(obis_code)
        return ALL_KNOWN_OBIS.get(normalized)

    def is_accumulation_register(self) -> bool:
        return bool(re.match(r"01-00:[BC][0-3]\.08\.00$", self.code))

    def is_transaction_register(self) -> bool:
        return bool(re.match(r"01-00:[BC][23]\.08\.00$", self.code))


# OCMF v1.4.0+ Reserved OBIS Codes for Billing (Table 25)
BILLING_RELEVANT_OBIS = {
    # Import Energy Registers (measured in kWh typically)
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
    # Export Energy Registers (for bidirectional charging)
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

# Common non-billing OBIS codes (for reference)
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

# Legacy OBIS codes (from older OCMF versions)
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

# Combine all known OBIS codes
ALL_KNOWN_OBIS = {**BILLING_RELEVANT_OBIS, **COMMON_OBIS, **LEGACY_OBIS}


# Module-level convenience functions for backward compatibility and ease of use


def normalize_obis_code(obis_code: str) -> str:
    return OBISInfo.normalize(obis_code)


def get_obis_info(obis_code: str) -> OBISInfo | None:
    return OBISInfo.from_code(obis_code)


def is_billing_relevant(obis_code: str) -> bool:
    normalized = normalize_obis_code(obis_code)

    # Check exact match first
    if normalized in ALL_KNOWN_OBIS:
        return ALL_KNOWN_OBIS[normalized].billing_relevant

    # Check pattern match for OCMF accumulation registers (B0-B3, C0-C3)
    if re.match(r"01-00:[BC][0-3]\.08\.00$", normalized):
        return True

    # Check standard IEC energy registers
    if re.match(r"01-00:0[12]\.08\.00$", normalized):
        return True

    return False


def is_accumulation_register(obis_code: str) -> bool:
    info = get_obis_info(obis_code)
    if info:
        return info.is_accumulation_register()

    # Fallback to pattern matching if code is unknown
    normalized = normalize_obis_code(obis_code)
    return bool(re.match(r"01-00:[BC][0-3]\.08\.00$", normalized))


def is_transaction_register(obis_code: str) -> bool:
    info = get_obis_info(obis_code)
    if info:
        return info.is_transaction_register()

    # Fallback to pattern matching if code is unknown
    normalized = normalize_obis_code(obis_code)
    return bool(re.match(r"01-00:[BC][23]\.08\.00$", normalized))


def validate_obis_for_billing(obis_code: str | None) -> tuple[bool, str | None]:
    if obis_code is None:
        return False, "OBIS code (RI) is required for billing-relevant readings"

    normalized = normalize_obis_code(obis_code)

    if not is_billing_relevant(obis_code):
        return False, f"OBIS code '{normalized}' is not billing-relevant"

    return True, None


class OBIS(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    code: str
    suffix: str | None = None

    @classmethod
    def from_string(cls, obis_str: str) -> OBIS:
        if not isinstance(obis_str, str):
            return obis_str  # Already an OBIS object

        parts = obis_str.split("*", 1)
        return cls(
            code=parts[0],
            suffix=parts[1] if len(parts) > 1 else None,
        )

    @property
    def info(self) -> OBISInfo | None:
        return get_obis_info(self.code)

    @property
    def is_billing_relevant(self) -> bool:
        return is_billing_relevant(self.code)

    @property
    def is_accumulation_register(self) -> bool:
        return is_accumulation_register(self.code)

    @property
    def is_transaction_register(self) -> bool:
        return is_transaction_register(self.code)

    def __str__(self) -> str:
        return f"{self.code}*{self.suffix}" if self.suffix else self.code

    def __repr__(self) -> str:
        if self.suffix:
            return f"OBIS('{self.code}*{self.suffix}')"
        return f"OBIS('{self.code}')"


# Type annotation for Pydantic fields that accept OBIS codes
# This allows both string input (which gets converted) and OBIS objects
OBISCode = Annotated[
    OBIS,
    BeforeValidator(lambda v: OBIS.from_string(v) if isinstance(v, str) else v),
]
