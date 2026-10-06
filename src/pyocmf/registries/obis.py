from __future__ import annotations

import enum
import re
from dataclasses import dataclass


class OBISCategory(enum.StrEnum):
    IMPORT = "import"
    EXPORT = "export"
    POWER = "power"
    OTHER = "other"


# A-B:C.D.E with an optional F group after "*" or "."; OCMF spec section
# "Extension to Billing Relevant OBIS Representation" writes all groups in hex
_OBIS_PATTERN = re.compile(
    r"^(?P<a>[0-9a-f]{1,2})-(?P<b>[0-9a-f]{1,2}):(?P<c>[0-9a-f]{1,2})"
    r"\.(?P<d>[0-9a-f]{1,2})\.(?P<e>[0-9a-f]{1,2})(?:[.*](?P<f>[0-9a-f]+))?$",
    re.IGNORECASE,
)

_ELECTRICITY = 1
_CUMULATIVE_ENERGY = 8
_ACTIVE_EXPORT = 0x02
# OCMF spec Table 25 reserves B0-C7 for billing-relevant energy. 01 is active import;
# 98 (loss-compensated) and 9E are vendor registers the Transparenzsoftware accepts.
_LAW_RELEVANT_C = {0x01, 0x98, 0x9E, *range(0xB0, 0xC8)}
_LOSS_COMPENSATED_C = {0x98, 0xB1, 0xB3, 0xC1, 0xC3}
# F groups the Transparenzsoftware accepts for law-relevant registers. It reads F as hex
# like pyocmf, so the decimal spellings "200" and "255" become 0x200 and 0x255.
_LAW_RELEVANT_F = {0x00, 0x200, 0x255, 0xFF}
_ACCUMULATION_C = {*range(0xB0, 0xB4), *range(0xC0, 0xC4)}
_TRANSACTION_C = {0xB2, 0xB3, 0xC2, 0xC3}


@dataclass(frozen=True)
class OBISGroups:
    a: int
    b: int
    c: int
    d: int
    e: int
    f: int | None = None

    @property
    def key(self) -> str:
        """Canonical zero-padded form without the F group, e.g. ``01-00:B2.08.00``."""
        return f"{self.a:02X}-{self.b:02X}:{self.c:02X}.{self.d:02X}.{self.e:02X}"

    @property
    def is_cumulative_energy(self) -> bool:
        return self.a == _ELECTRICITY and self.d == _CUMULATIVE_ENERGY


def parse_obis(obis_code: str) -> OBISGroups | None:
    """Parse an OBIS code into its groups, read as hex as in the OCMF spec; None if malformed."""
    match = _OBIS_PATTERN.match(obis_code.strip())
    if match is None:
        return None
    f = match["f"]
    return OBISGroups(
        a=int(match["a"], 16),
        b=int(match["b"], 16),
        c=int(match["c"], 16),
        d=int(match["d"], 16),
        e=int(match["e"], 16),
        f=int(f, 16) if f is not None else None,
    )


def _normalize(obis_code: str) -> str:
    return obis_code.split("*")[0]


@dataclass
class OBISInfo:
    """Description and classification of a known OBIS code."""

    code: str
    description: str
    billing_relevant: bool
    category: OBISCategory

    @staticmethod
    def normalize(obis_code: str) -> str:
        return _normalize(obis_code)

    @staticmethod
    def from_code(obis_code: str) -> OBISInfo | None:
        return get_obis_info(obis_code)

    def is_accumulation_register(self) -> bool:
        return is_accumulation_register(self.code)

    def is_transaction_register(self) -> bool:
        return is_transaction_register(self.code)


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

_KNOWN_OBIS_BY_KEY = {
    groups.key: info
    for code, info in ALL_KNOWN_OBIS.items()
    if (groups := parse_obis(code)) is not None
}


def normalize_obis_code(obis_code: str) -> str:
    return _normalize(obis_code)


def get_obis_info(obis_code: str) -> OBISInfo | None:
    """Look up a known OBIS code; None for codes not in the registry."""
    groups = parse_obis(obis_code)
    return _KNOWN_OBIS_BY_KEY.get(groups.key) if groups else None


def is_billing_relevant(obis_code: str) -> bool:
    """Whether the register holds energy that can be billed.

    Known codes use the registry. Other cumulative energy registers count when they
    are law-relevant or hold active export energy, so this is broader than
    ``is_law_relevant``, which the Eichrecht checks use.
    """
    if (info := get_obis_info(obis_code)) is not None:
        return info.billing_relevant
    groups = parse_obis(obis_code)
    return (
        groups is not None
        and groups.is_cumulative_energy
        and (groups.c in _LAW_RELEVANT_C or groups.c == _ACTIVE_EXPORT)
    )


def is_law_relevant(obis_code: str) -> bool:
    """Whether the register is compared for a transaction, as in the Transparenzsoftware.

    These are cumulative energy registers for active import (01), the vendor registers
    98 (loss-compensated) and 9E, and the range B0-C7 that OCMF spec Table 25 reserves.
    An F group, if present, must be 0 or FF (or 200/255, which the Transparenzsoftware
    also accepts).
    """
    groups = parse_obis(obis_code)
    return (
        groups is not None
        and groups.is_cumulative_energy
        and groups.c in _LAW_RELEVANT_C
        and (groups.f is None or groups.f in _LAW_RELEVANT_F)
    )


def is_loss_compensated(obis_code: str) -> bool:
    groups = parse_obis(obis_code)
    return groups is not None and groups.is_cumulative_energy and groups.c in _LOSS_COMPENSATED_C


def _is_reserved_register(obis_code: str, c_values: set[int]) -> bool:
    groups = parse_obis(obis_code)
    return (
        groups is not None
        and groups.is_cumulative_energy
        and groups.b == 0
        and groups.e == 0
        and groups.c in c_values
    )


def is_accumulation_register(obis_code: str) -> bool:
    """Whether the code is an OCMF reserved energy register (B0-B3, C0-C3; spec Table 25)."""
    return _is_reserved_register(obis_code, _ACCUMULATION_C)


def is_transaction_register(obis_code: str) -> bool:
    """Whether the code is an OCMF reserved per-transaction register (B2, B3, C2, C3)."""
    return _is_reserved_register(obis_code, _TRANSACTION_C)


def validate_obis_for_billing(obis_code: str | None) -> tuple[bool, str | None]:
    if obis_code is None:
        return False, "OBIS code (RI) is required for billing-relevant readings"

    normalized = _normalize(obis_code)

    if not is_billing_relevant(obis_code):
        return False, f"OBIS code '{normalized}' is not billing-relevant"

    return True, None
