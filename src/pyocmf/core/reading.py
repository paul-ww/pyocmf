from __future__ import annotations

import decimal
import warnings

import pydantic

from pyocmf.enums.reading import (
    ErrorFlags,
    MeterReadingReason,
    MeterStatus,
    ReadingType,
    TimeStatus,
)
from pyocmf.enums.units import EnergyUnit, OCMFUnit, ResistanceUnit
from pyocmf.models.obis import OBIS, OBISCode
from pyocmf.models.timestamp import OCMFTimestamp
from pyocmf.registries.obis import is_accumulation_register
from pyocmf.types.numbers import OCMFNumber


class Reading(pydantic.BaseModel):
    TM: OCMFTimestamp = pydantic.Field(description="Time (ISO 8601 + time status) - REQUIRED")
    TX: MeterReadingReason | None = pydantic.Field(default=None, description="Transaction")
    RV: OCMFNumber | None = pydantic.Field(
        default=None,
        description="Reading Value - omitted only for pure error-event readings",
    )
    RI: OBISCode | None = pydantic.Field(
        default=None, description="Reading Identification (OBIS code) - Conditional"
    )
    RU: OCMFUnit | str | None = pydantic.Field(
        default=None,
        description="Reading Unit (e.g. kWh, Wh, mOhm per OCMF spec Table 20)",
    )
    RT: ReadingType | None = pydantic.Field(
        default=None, description="Reading Current Type (AC/DC per OCMF spec Table 21)"
    )
    CL: OCMFNumber | None = pydantic.Field(default=None, description="Cumulated Losses")
    EF: ErrorFlags | None = pydantic.Field(
        default=None, description="Error Flags (can contain 'E', 't', or both)"
    )
    ST: MeterStatus = pydantic.Field(description="Status - REQUIRED")

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
    def ef_empty_string_to_none(cls, v: str | None) -> ErrorFlags | None:
        if v == "":
            return None
        return v

    @pydantic.field_validator("RU")
    @classmethod
    def validate_reading_unit(cls, v: OCMFUnit | str | None) -> OCMFUnit | str | None:
        """Validate RU is spec-compliant, warn if not."""
        if v is None:
            return v
        spec_units = {unit.value for unit in EnergyUnit} | {unit.value for unit in ResistanceUnit}
        value_str = str(v)
        if value_str not in spec_units:
            warnings.warn(
                f"Reading Unit '{value_str}' is not in OCMF spec Table 20 "
                f"({', '.join(sorted(spec_units))}). "
                f"This may indicate a vendor-specific or extended unit. "
                f"Data will be accepted.",
                UserWarning,
                stacklevel=2,
            )
        return v

    @pydantic.field_validator("CL")
    @classmethod
    def validate_cl(
        cls, v: decimal.Decimal | None, info: pydantic.ValidationInfo
    ) -> decimal.Decimal | None:
        if v is None:
            return v

        ri = info.data.get("RI")
        cl_register_error = (
            "CL (Cumulated Loss) can only appear when RI indicates an "
            "accumulation register (B0-B3, C0-C3)"
        )
        if not ri:
            raise ValueError(cl_register_error)
        if isinstance(ri, OBIS) and not ri.is_accumulation_register:
            raise ValueError(cl_register_error)
        if isinstance(ri, str) and not is_accumulation_register(ri):
            raise ValueError(cl_register_error)

        if v != 0:
            tx = info.data.get("TX")
            if tx == MeterReadingReason.BEGIN:
                msg = "CL (Cumulated Loss) must be 0 when TX=B (transaction begin)"
                raise ValueError(msg)

        if v < 0:
            msg = "CL (Cumulated Loss) must be non-negative"
            raise ValueError(msg)

        return v

    @pydantic.model_validator(mode="after")
    def validate_ri_ru_group(self) -> Reading:
        """RI and RU form a group per OCMF spec Table 7.

        RV/RI/RU/RT may all be omitted only when the reading merely signals an
        error event of the meter.
        """
        ri_present = self.RI is not None
        ru_present = self.RU is not None

        if ri_present != ru_present:
            msg = (
                "RI (Reading Identification) and RU (Reading Unit) must both be "
                "present or both absent"
            )
            raise ValueError(msg)

        if self.RV is not None and not ru_present:
            msg = "RU (Reading Unit) is required when RV (Reading Value) is present"
            raise ValueError(msg)

        return self

    @property
    def timestamp(self):
        return self.TM.timestamp

    @property
    def time_status(self) -> TimeStatus:
        return self.TM.status
