"""OBIS code type for Pydantic models with semantic information.

This module provides a Pydantic-compatible OBIS code type that handles
parsing and provides semantic information about OBIS codes according to
IEC 62056-6-1/6-2 standards and OCMF specification Table 25.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Annotated

import pydantic
from pydantic import BeforeValidator


class OBISCategory(enum.StrEnum):
    """Category of OBIS code measurement."""

    IMPORT = "import"
    EXPORT = "export"
    POWER = "power"
    OTHER = "other"


@dataclass
class OBISInfo:
    """Information about an OBIS code."""

    code: str
    description: str
    billing_relevant: bool
    category: OBISCategory

    @staticmethod
    def normalize(obis_code: str) -> str:
        """Normalize an OBIS code to canonical format (without asterisk suffix).

        Args:
            obis_code: OBIS code string (e.g., "01-00:B0.08.00*FF" or "1-b:1.8.0")

        Returns:
            Normalized OBIS code without asterisk suffix

        Examples:
            >>> OBISInfo.normalize("01-00:B0.08.00*FF")
            "01-00:B0.08.00"
            >>> OBISInfo.normalize("1-b:1.8.0")
            "1-b:1.8.0"
        """
        # Remove asterisk and everything after it
        return obis_code.split("*")[0]

    @staticmethod
    def from_code(obis_code: str) -> OBISInfo | None:
        """Get information about an OBIS code.

        Args:
            obis_code: OBIS code string

        Returns:
            OBISInfo object if code is known, None otherwise

        Examples:
            >>> info = OBISInfo.from_code("01-00:B2.08.00*FF")
            >>> info.description
            "Transaction Import Mains Energy (session energy at meter)"
        """
        normalized = OBISInfo.normalize(obis_code)
        return ALL_KNOWN_OBIS.get(normalized)

    def is_accumulation_register(self) -> bool:
        """Check if this OBIS code represents an accumulation register.

        Per OCMF v1.4.0+ Table 25, accumulation registers are:
        - Import Energy: B0 (Total Mains), B1 (Total Device), B2 (Transaction Mains), B3 (Transaction Device)
        - Export Energy: C0 (Total Mains), C1 (Total Device), C2 (Transaction Mains), C3 (Transaction Device)

        Returns:
            True if the OBIS code represents an accumulation register

        Examples:
            >>> info = OBISInfo.from_code("01-00:B2.08.00*FF")
            >>> info.is_accumulation_register()
            True
        """
        return bool(re.match(r"01-00:[BC][0-3]\.08\.00$", self.code))

    def is_transaction_register(self) -> bool:
        """Check if this OBIS code represents a transaction-scoped register.

        Transaction registers (B2, B3, C2, C3) measure energy for a specific charging session,
        while total registers (B0, B1, C0, C1) measure cumulative energy across all sessions.

        Returns:
            True if the OBIS code represents a transaction register

        Examples:
            >>> info = OBISInfo.from_code("01-00:B2.08.00*FF")
            >>> info.is_transaction_register()
            True
            >>> info = OBISInfo.from_code("01-00:B0.08.00*FF")
            >>> info.is_transaction_register()
            False
        """
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
    """Normalize an OBIS code to canonical format (without asterisk suffix).

    Args:
        obis_code: OBIS code string (e.g., "01-00:B0.08.00*FF" or "1-b:1.8.0")

    Returns:
        Normalized OBIS code without asterisk suffix

    Examples:
        >>> normalize_obis_code("01-00:B0.08.00*FF")
        "01-00:B0.08.00"
    """
    return OBISInfo.normalize(obis_code)


def get_obis_info(obis_code: str) -> OBISInfo | None:
    """Get information about an OBIS code.

    Args:
        obis_code: OBIS code string

    Returns:
        OBISInfo object if code is known, None otherwise

    Examples:
        >>> info = get_obis_info("01-00:B2.08.00*FF")
        >>> info.description
        "Transaction Import Mains Energy (session energy at meter)"
    """
    return OBISInfo.from_code(obis_code)


def is_billing_relevant(obis_code: str) -> bool:
    """Check if an OBIS code is billing-relevant.

    Args:
        obis_code: OBIS code string

    Returns:
        True if the code is known to be billing-relevant

    Examples:
        >>> is_billing_relevant("01-00:B2.08.00*FF")
        True
        >>> is_billing_relevant("01-00:00.08.06*FF")
        False
    """
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
    """Check if OBIS code represents an accumulation register.

    Per OCMF v1.4.0+ Table 25, accumulation registers are:
    - Import Energy: B0 (Total Mains), B1 (Total Device), B2 (Transaction Mains), B3 (Transaction Device)
    - Export Energy: C0 (Total Mains), C1 (Total Device), C2 (Transaction Mains), C3 (Transaction Device)

    Args:
        obis_code: OBIS code string to check

    Returns:
        True if the OBIS code represents an accumulation register

    Examples:
        >>> is_accumulation_register("01-00:B2.08.00*FF")
        True
        >>> is_accumulation_register("01-00:00.08.06*FF")
        False
    """
    info = get_obis_info(obis_code)
    if info:
        return info.is_accumulation_register()

    # Fallback to pattern matching if code is unknown
    normalized = normalize_obis_code(obis_code)
    return bool(re.match(r"01-00:[BC][0-3]\.08\.00$", normalized))


def is_transaction_register(obis_code: str) -> bool:
    """Check if OBIS code represents a transaction-scoped register.

    Transaction registers (B2, B3, C2, C3) measure energy for a specific charging session,
    while total registers (B0, B1, C0, C1) measure cumulative energy across all sessions.

    Args:
        obis_code: OBIS code string to check

    Returns:
        True if the OBIS code represents a transaction register

    Examples:
        >>> is_transaction_register("01-00:B2.08.00*FF")
        True
        >>> is_transaction_register("01-00:B0.08.00*FF")
        False
    """
    info = get_obis_info(obis_code)
    if info:
        return info.is_transaction_register()

    # Fallback to pattern matching if code is unknown
    normalized = normalize_obis_code(obis_code)
    return bool(re.match(r"01-00:[BC][23]\.08\.00$", normalized))


def validate_obis_for_billing(obis_code: str | None) -> tuple[bool, str | None]:
    """Validate that an OBIS code is suitable for billing purposes.

    Args:
        obis_code: OBIS code to validate (or None)

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if code is suitable for billing
        - error_message: Description of issue if not valid, None otherwise

    Examples:
        >>> validate_obis_for_billing("01-00:B2.08.00*FF")
        (True, None)
        >>> validate_obis_for_billing("01-00:00.08.06*FF")
        (False, "OBIS code '01-00:00.08.06' is not billing-relevant")
    """
    if obis_code is None:
        return False, "OBIS code (RI) is required for billing-relevant readings"

    normalized = normalize_obis_code(obis_code)

    if not is_billing_relevant(obis_code):
        return False, f"OBIS code '{normalized}' is not billing-relevant"

    return True, None


class OBIS(pydantic.BaseModel):
    """OBIS code with semantic validation and information.

    OBIS (Object Identification System) codes identify specific meter readings
    according to IEC 62056-6-1/6-2 standards. This class provides parsing,
    validation, and semantic information about OBIS codes.

    The OBIS code format is: XX-XX:XX.XX.XX*XX where:
    - The main code identifies the measurement type
    - The asterisk suffix (*XX) is optional metadata

    Examples:
        >>> obis = OBIS.from_string("01-00:B2.08.00*FF")
        >>> obis.code
        "01-00:B2.08.00"
        >>> obis.suffix
        "FF"
        >>> obis.is_billing_relevant
        True
    """

    model_config = pydantic.ConfigDict(frozen=True)

    code: str
    """Normalized OBIS code without asterisk suffix."""

    suffix: str | None = None
    """Optional asterisk suffix (the part after '*')."""

    @classmethod
    def from_string(cls, obis_str: str) -> OBIS:
        """Parse an OBIS code string.

        Args:
            obis_str: OBIS code string (e.g., "01-00:B2.08.00*FF")

        Returns:
            OBIS instance with parsed code and suffix

        Examples:
            >>> OBIS.from_string("01-00:B2.08.00*FF")
            OBIS(code='01-00:B2.08.00', suffix='FF')
            >>> OBIS.from_string("1-b:1.8.0")
            OBIS(code='1-b:1.8.0', suffix=None)
        """
        if not isinstance(obis_str, str):
            return obis_str  # Already an OBIS object

        parts = obis_str.split("*", 1)
        return cls(
            code=parts[0],
            suffix=parts[1] if len(parts) > 1 else None,
        )

    @property
    def info(self) -> OBISInfo | None:
        """Get semantic information about this OBIS code.

        Returns:
            OBISInfo object if code is known, None otherwise

        Examples:
            >>> obis = OBIS.from_string("01-00:B2.08.00*FF")
            >>> obis.info.description
            "Transaction Import Mains Energy (session energy at meter)"
        """
        return get_obis_info(self.code)

    @property
    def is_billing_relevant(self) -> bool:
        """Check if this OBIS code is billing-relevant.

        Returns:
            True if the code is known to be billing-relevant

        Examples:
            >>> OBIS.from_string("01-00:B2.08.00*FF").is_billing_relevant
            True
            >>> OBIS.from_string("01-00:00.08.06*FF").is_billing_relevant
            False
        """
        return is_billing_relevant(self.code)

    @property
    def is_accumulation_register(self) -> bool:
        """Check if this represents an accumulation register (B0-B3, C0-C3).

        Returns:
            True if this is an accumulation register

        Examples:
            >>> OBIS.from_string("01-00:B2.08.00*FF").is_accumulation_register
            True
        """
        return is_accumulation_register(self.code)

    @property
    def is_transaction_register(self) -> bool:
        """Check if this represents a transaction-scoped register (B2-B3, C2-C3).

        Transaction registers measure energy for a specific charging session,
        while total registers (B0-B1, C0-C1) measure cumulative energy.

        Returns:
            True if this is a transaction register

        Examples:
            >>> OBIS.from_string("01-00:B2.08.00*FF").is_transaction_register
            True
            >>> OBIS.from_string("01-00:B0.08.00*FF").is_transaction_register
            False
        """
        return is_transaction_register(self.code)

    def __str__(self) -> str:
        """String representation with suffix if present.

        Returns:
            OBIS code string with optional asterisk suffix

        Examples:
            >>> str(OBIS.from_string("01-00:B2.08.00*FF"))
            "01-00:B2.08.00*FF"
            >>> str(OBIS.from_string("1-b:1.8.0"))
            "1-b:1.8.0"
        """
        return f"{self.code}*{self.suffix}" if self.suffix else self.code

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        if self.suffix:
            return f"OBIS('{self.code}*{self.suffix}')"
        return f"OBIS('{self.code}')"


# Type annotation for Pydantic fields that accept OBIS codes
# This allows both string input (which gets converted) and OBIS objects
OBISCode = Annotated[
    OBIS,
    BeforeValidator(lambda v: OBIS.from_string(v) if isinstance(v, str) else v),
]
