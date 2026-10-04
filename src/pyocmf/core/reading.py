from __future__ import annotations

import datetime
import re

import pydantic

from pyocmf.enums.reading import MeterReadingReason, MeterStatus, TimeStatus
from pyocmf.models.obis import OBISCode
from pyocmf.models.timestamp import OCMFTimestamp
from pyocmf.types.lenient import (
    LenientMeterReadingReason,
    LenientMeterStatus,
    LenientReadingType,
    LenientUnit,
    warn_spec,
)
from pyocmf.types.numbers import OCMFNumber

# OCMF spec Table 7: E (energy) and t (time) are the only defined error flags
_ERROR_FLAGS_PATTERN = re.compile(r"^[Et]*$")


class Reading(pydantic.BaseModel):
    """A meter reading (OCMF spec Table 7)."""

    # Re-validate on assignment so mutated readings keep parsed types (e.g. TM).
    # Extra keys (e.g. EI from pre-1.0 formats) survive parse/serialize roundtrips.
    model_config = pydantic.ConfigDict(validate_assignment=True, extra="allow")

    TM: OCMFTimestamp = pydantic.Field(description="Time (ISO 8601 + time status) - REQUIRED")
    TX: LenientMeterReadingReason | None = pydantic.Field(default=None, description="Transaction")
    RV: OCMFNumber | None = pydantic.Field(
        default=None,
        description="Reading Value - omitted only for pure error-event readings",
    )
    RI: OBISCode | None = pydantic.Field(
        default=None, description="Reading Identification (OBIS code) - Conditional"
    )
    RU: LenientUnit | None = pydantic.Field(
        default=None,
        description="Reading Unit (e.g. kWh, Wh, mOhm per OCMF spec Table 20)",
    )
    RT: LenientReadingType | None = pydantic.Field(
        default=None, description="Reading Current Type (AC/DC per OCMF spec Table 21)"
    )
    CL: OCMFNumber | None = pydantic.Field(default=None, description="Cumulated Losses")
    EF: str | None = pydantic.Field(
        default=None, description="Error Flags (can contain 'E', 't', or both)"
    )
    ST: LenientMeterStatus | None = pydantic.Field(default=None, description="Status - REQUIRED")

    @pydantic.field_validator("TM", mode="before")
    @classmethod
    def parse_timestamp(cls, v: str | OCMFTimestamp) -> OCMFTimestamp:
        if isinstance(v, OCMFTimestamp):
            return v
        if isinstance(v, str):
            return OCMFTimestamp.from_string(v)
        msg = f"TM must be a string or OCMFTimestamp, got {type(v)}"
        raise TypeError(msg)

    @pydantic.field_serializer("TM")
    def serialize_timestamp(self, tm: OCMFTimestamp) -> str:
        return str(tm)

    @pydantic.field_validator("EF", mode="before")
    @classmethod
    def ef_empty_string_to_none(cls, v: str | None) -> str | None:
        if v == "":
            return None
        if v is not None and not _ERROR_FLAGS_PATTERN.match(v):
            warn_spec(f"Error flags (EF) '{v}' contain characters other than 'E' and 't'")
        return v

    @pydantic.model_validator(mode="after")
    def warn_on_missing_fields(self) -> Reading:
        """Warn about OCMF spec Table 7 violations the Transparenzsoftware tolerates.

        RV/RI/RU/RT may all be omitted only when the reading merely signals an
        error event of the meter.
        """
        if self.ST is None:
            warn_spec("Status (ST) is mandatory")
        if (self.RI is None) != (self.RU is None):
            warn_spec(
                "RI (Reading Identification) and RU (Reading Unit) must both be "
                "present or both absent"
            )
        if self.RV is not None and self.RU is None:
            warn_spec("RU (Reading Unit) is required when RV (Reading Value) is present")
        return self

    @property
    def timestamp(self) -> datetime.datetime:
        """Reading time (TM) without its time status."""
        return self.TM.timestamp

    @property
    def time_status(self) -> TimeStatus | str:
        """Time status of TM; an unknown status stays a plain string."""
        return self.TM.status


__all__ = ["MeterReadingReason", "MeterStatus", "OCMFTimestamp", "Reading"]
