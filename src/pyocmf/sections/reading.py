"""OCMF meter reading types and models.

This module defines the various enums and models used for representing
meter readings in OCMF format, including reading types, statuses, and values.
"""

from __future__ import annotations

import decimal
import enum
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

import pydantic
from pydantic.types import StringConstraints

from pyocmf.types.obis import OBIS, OBISCode
from pyocmf.types.units import OCMFUnit


class ReadingType(enum.StrEnum):
    """Type of electrical current in the meter reading."""

    AC = "AC"
    DC = "DC"


class MeterReadingReason(enum.StrEnum):
    """Reason or trigger for a meter reading."""

    BEGIN = "B"
    CHARGING = "C"
    EXCEPTION = "X"
    END = "E"
    TERMINATION_LOCAL = "L"
    TERMINATION_REMOTE = "R"
    TERMINATION_ABORT = "A"
    TERMINATION_POWER_FAILURE = "P"
    SUSPENDED = "S"
    TARIFF_CHANGE = "T"

    def is_end_reading(self) -> bool:
        """Check if the reading reason indicates the end of a transaction."""
        return self in {
            MeterReadingReason.END,
            MeterReadingReason.TERMINATION_LOCAL,
            MeterReadingReason.TERMINATION_REMOTE,
            MeterReadingReason.TERMINATION_ABORT,
            MeterReadingReason.TERMINATION_POWER_FAILURE,
        }


class MeterStatus(enum.StrEnum):
    """Status of the meter at the time of reading."""

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


class TimeStatus(enum.StrEnum):
    """Synchronization status of the timestamp."""

    UNKNOWN_OR_UNSYNCHRONIZED = "U"
    INFORMATIVE = "I"
    SYNCHRONIZED = "S"
    RELATIVE = "R"


# OCMF time format: ISO 8601 with milliseconds, timezone, and status flag
# (e.g., "2023-06-15T14:30:45,123+0200 S" where S=Synchronized, U=Unknown, I=Informative, R=Relative)
OCMFTimeFormat = Annotated[
    str,
    StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2},\d{3}[+-]\d{4} [UISR]$"),
]


@dataclass(frozen=True)
class OCMFTimestamp:
    """Structured representation of an OCMF timestamp.

    Combines a timezone-aware datetime with a time synchronization status.
    Automatically serializes to/from OCMF string format.
    """

    timestamp: datetime
    status: TimeStatus

    def __str__(self) -> str:
        """Serialize to OCMF timestamp format."""
        return serialize_ocmf_timestamp(self.timestamp, self.status)

    @classmethod
    def from_string(cls, timestamp_str: str) -> OCMFTimestamp:
        """Parse from OCMF timestamp string."""
        dt, status = parse_ocmf_timestamp(timestamp_str)
        return cls(timestamp=dt, status=status)


# Error flags: Empty string or combination of 'E' (error) and 't' (test/tariff change)
# (e.g., "", "E", "t", "Et")
ErrorFlags = Annotated[str, StringConstraints(pattern=r"^[Et]*$")]


def parse_ocmf_timestamp(timestamp_str: str) -> tuple[datetime, TimeStatus]:
    """Parse an OCMF timestamp string to a datetime object and status.

    OCMF timestamps have the format: "2023-06-15T14:30:45,123+0200 S"
    Where the last character is the time status flag (S/U/I/R).

    Args:
        timestamp_str: OCMF timestamp string

    Returns:
        Tuple of (parsed datetime object, time status)

    Raises:
        ValueError: If the timestamp cannot be parsed
    """
    # Extract the status flag at the end (e.g., " S")
    if " " in timestamp_str:
        ts_part, status_part = timestamp_str.rsplit(" ", 1)
        status = TimeStatus(status_part)
    else:
        ts_part = timestamp_str
        status = TimeStatus.UNKNOWN_OR_UNSYNCHRONIZED

    # Replace comma with period for milliseconds (OCMF uses comma, ISO uses period)
    ts_normalized = ts_part.replace(",", ".")

    # Parse as ISO 8601
    dt = datetime.fromisoformat(ts_normalized)

    return dt, status


def serialize_ocmf_timestamp(dt: datetime, status: TimeStatus = TimeStatus.SYNCHRONIZED) -> str:
    """Serialize a datetime object to OCMF timestamp format.

    Args:
        dt: Datetime object (must be timezone-aware)
        status: Time synchronization status

    Returns:
        OCMF-formatted timestamp string

    Raises:
        ValueError: If datetime is not timezone-aware
    """
    if dt.tzinfo is None:
        error_message = "Datetime must be timezone-aware for OCMF format"
        raise ValueError(error_message)

    # Format as ISO 8601 with timezone
    iso_str = dt.isoformat(timespec="milliseconds")

    # Replace period with comma for milliseconds (OCMF requirement)
    ocmf_str = iso_str.replace(".", ",")

    # Add status flag
    return f"{ocmf_str} {status.value}"


# OBIS code formats: Accept either strict OCMF format or flexible IEC 62056 format
# Strict OCMF format per spec Figure 1: 6 zero-padded hex byte pairs with asterisk
# Example: 01-0B:01.08.00*FF
ObisCodeOCMF = Annotated[
    str,
    StringConstraints(
        pattern=r"^[0-9A-F]{2}-[0-9A-F]{2}:[0-9A-F]{2}\.[0-9A-F]{2}\.[0-9A-F]{2}\*[0-9A-F]{2}$"
    ),
]

# IEC 62056-6-1/6-2 flexible format: 1-2 hex digits per group, case-insensitive, optional asterisk
# Example: 1-b:1.8.0 or 1-0:1.8.0*198
ObisCodeIEC = Annotated[
    str,
    StringConstraints(
        pattern=r"^[0-9A-Fa-f]{1,2}-[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}\.[0-9A-Fa-f]{1,2}\.[0-9A-Fa-f]{1,2}(\*[0-9A-Fa-f]{1,3})?$"
    ),
]

# Accept either format
ObisCode = ObisCodeOCMF | ObisCodeIEC

# OCMF v1.4.0+ Reserved OBIS Codes for Billing-Relevant Data (Table 25)
#
# To ensure clear identification of billing-relevant data, OCMF defines a range of
# manufacturer-specific OBIS codes in the 'C' field for use within OCMF, compliant
# with IEC62056-6-1. OBIS codes are represented in hexadecimal format and categorized
# as follows:
#
# Import Energy Registers (01-00:Bx.08.00*xx):
#   - B0: Total Import Mains Energy (energy measured at the meter)
#   - B1: Total Import Device Energy (energy measured at consuming device, e.g., car)
#   - B2: Transaction Import Mains Energy (energy during charging session at meter)
#   - B3: Transaction Import Device Energy (energy during charging session at device)
#
# Export Energy Registers (01-00:Cx.08.00*xx):
#   - C0: Total Export Mains Energy
#   - C1: Total Export Device Energy
#   - C2: Transaction Export Mains Energy
#   - C3: Transaction Export Device Energy
#
# Reserved for Future Use:
#   - B4-BF, C4-C7 ranges are reserved
#
# Define patterns for billing-relevant accumulation registers
ACCUMULATION_REGISTER_PATTERNS = [
    r"01-00:B[0-3]\.08\.00\*[0-9A-Fa-f]{2}",  # Import registers B0-B3
    r"01-00:C[0-3]\.08\.00\*[0-9A-Fa-f]{2}",  # Export registers C0-C3
]


def is_accumulation_register(obis_code: str) -> bool:
    """Check if OBIS code represents an accumulation register.

    Per OCMF v1.4.0+ Table 25, accumulation registers are:
    - Import Energy: B0 (Total Mains), B1 (Total Device), B2 (Transaction Mains), B3 (Transaction Device)
    - Export Energy: C0 (Total Mains), C1 (Total Device), C2 (Transaction Mains), C3 (Transaction Device)

    Args:
        obis_code: OBIS code string to check

    Returns:
        True if the OBIS code represents an accumulation register
    """
    return any(re.match(pattern, obis_code) for pattern in ACCUMULATION_REGISTER_PATTERNS)


class Reading(pydantic.BaseModel):
    """A single meter reading with timestamp and associated metadata.

    Represents one meter reading taken during a charging session, including
    the meter value, timestamp, status, and other relevant information.
    """

    TM: OCMFTimestamp = pydantic.Field(description="Time (ISO 8601 + time status) - REQUIRED")
    TX: MeterReadingReason | None = pydantic.Field(default=None, description="Transaction")
    RV: decimal.Decimal | None = pydantic.Field(
        default=None,
        description="Reading Value - Conditional (required when RI present)",
    )
    RI: OBISCode | None = pydantic.Field(
        default=None, description="Reading Identification (OBIS code) - Conditional"
    )
    RU: OCMFUnit = pydantic.Field(description="Reading Unit - REQUIRED")
    RT: ReadingType | None = pydantic.Field(default=None, description="Reading Current Type")
    CL: decimal.Decimal | None = pydantic.Field(default=None, description="Cumulated Losses")
    EF: ErrorFlags | None = pydantic.Field(
        default=None, description="Error Flags (can contain 'E', 't', or both)"
    )
    ST: MeterStatus = pydantic.Field(description="Status - REQUIRED")

    @pydantic.field_validator("TM", mode="before")
    @classmethod
    def parse_timestamp(cls, v: str | OCMFTimestamp) -> OCMFTimestamp:
        """Parse OCMF timestamp string to OCMFTimestamp object."""
        if isinstance(v, OCMFTimestamp):
            return v
        if isinstance(v, str):
            return OCMFTimestamp.from_string(v)
        msg = f"TM must be a string or OCMFTimestamp, got {type(v)}"
        raise TypeError(msg)

    @pydantic.field_serializer("TM")
    def serialize_timestamp(self, tm: OCMFTimestamp) -> str:
        """Serialize OCMFTimestamp to OCMF string format."""
        return str(tm)

    @pydantic.field_validator("EF", mode="before")
    @classmethod
    def ef_empty_string_to_none(cls, v: str | None) -> ErrorFlags | None:
        """Convert empty error flag strings to None."""
        if v == "":
            return None
        return v

    @pydantic.field_validator("CL")
    @classmethod
    def validate_cl_with_accumulation_register(
        cls, v: decimal.Decimal | None, info: pydantic.ValidationInfo
    ) -> decimal.Decimal | None:
        """CL can only appear with accumulation register readings.

        Per OCMF spec Table 7: CL (Cumulated Loss) parameter can only be added
        when RI is indicating an accumulation register reading (B0-B3, C0-C3).
        """
        if v is not None:
            ri = info.data.get("RI")
            if not ri:
                msg = "CL (Cumulated Loss) can only appear when RI indicates an accumulation register (B0-B3, C0-C3)"
                raise ValueError(msg)
            # RI is now an OBIS object, use its property
            if isinstance(ri, OBIS) and not ri.is_accumulation_register:
                msg = "CL (Cumulated Loss) can only appear when RI indicates an accumulation register (B0-B3, C0-C3)"
                raise ValueError(msg)
            # Fallback for string validation (shouldn't happen with OBISCode annotation)
            if isinstance(ri, str) and not is_accumulation_register(ri):
                msg = "CL (Cumulated Loss) can only appear when RI indicates an accumulation register (B0-B3, C0-C3)"
                raise ValueError(msg)
        return v

    @pydantic.field_validator("CL")
    @classmethod
    def validate_cl_reset_at_begin(
        cls, v: decimal.Decimal | None, info: pydantic.ValidationInfo
    ) -> decimal.Decimal | None:
        """CL must be 0 when TX=B (transaction begin).

        Per OCMF spec: CL must be reset at the beginning of a transaction.
        """
        if v is not None and v != 0:
            tx = info.data.get("TX")
            if tx == MeterReadingReason.BEGIN:
                msg = "CL (Cumulated Loss) must be 0 when TX=B (transaction begin)"
                raise ValueError(msg)
        return v

    @pydantic.field_validator("CL")
    @classmethod
    def validate_cl_non_negative(cls, v: decimal.Decimal | None) -> decimal.Decimal | None:
        """CL must be non-negative.

        Cumulated losses cannot be negative - they represent accumulated energy
        loss due to cable resistance.
        """
        if v is not None and v < 0:
            msg = "CL (Cumulated Loss) must be non-negative"
            raise ValueError(msg)
        return v

    @pydantic.model_validator(mode="after")
    def validate_ri_ru_group(self) -> Reading:
        """RI and RU must both be present or both absent (field group constraint).

        Per OCMF spec Table 7: "The fields RI and RU form a group. Fields of a
        group are either all present together or omitted together."
        """
        ri_present = self.RI is not None
        ru_present = self.RU is not None

        if ri_present != ru_present:
            msg = "RI (Reading Identification) and RU (Reading Unit) must both be present or both absent"
            raise ValueError(msg)

        return self

    @property
    def timestamp(self) -> datetime:
        """Get the parsed datetime from TM field.

        Returns:
            Timezone-aware datetime object
        """
        return self.TM.timestamp

    @property
    def time_status(self) -> TimeStatus:
        """Get the time synchronization status from TM field.

        Returns:
            Time status (SYNCHRONIZED, UNKNOWN_OR_UNSYNCHRONIZED, etc.)
        """
        return self.TM.status
