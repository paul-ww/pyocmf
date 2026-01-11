from __future__ import annotations

import decimal

import pydantic

from pyocmf.enums.reading import ErrorFlags, MeterReadingReason, MeterStatus, TimeStatus
from pyocmf.enums.units import OCMFUnit
from pyocmf.models.obis import OBIS, OBISCode
from pyocmf.models.timestamp import OCMFTimestamp
from pyocmf.registries.obis import is_accumulation_register


class Reading(pydantic.BaseModel):
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
    RT: str | None = pydantic.Field(default=None, description="Reading Current Type")
    CL: decimal.Decimal | None = pydantic.Field(default=None, description="Cumulated Losses")
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

    @pydantic.field_validator("CL")
    @classmethod
    def validate_cl_with_accumulation_register(
        cls, v: decimal.Decimal | None, info: pydantic.ValidationInfo
    ) -> decimal.Decimal | None:
        if v is not None:
            ri = info.data.get("RI")
            cl_error = (
                "CL (Cumulated Loss) can only appear when RI indicates an "
                "accumulation register (B0-B3, C0-C3)"
            )
            if not ri:
                raise ValueError(cl_error)
            if isinstance(ri, OBIS) and not ri.is_accumulation_register:
                raise ValueError(cl_error)
            if isinstance(ri, str) and not is_accumulation_register(ri):
                raise ValueError(cl_error)
        return v

    @pydantic.field_validator("CL")
    @classmethod
    def validate_cl_reset_at_begin(
        cls, v: decimal.Decimal | None, info: pydantic.ValidationInfo
    ) -> decimal.Decimal | None:
        if v is not None and v != 0:
            tx = info.data.get("TX")
            if tx == MeterReadingReason.BEGIN:
                msg = "CL (Cumulated Loss) must be 0 when TX=B (transaction begin)"
                raise ValueError(msg)
        return v

    @pydantic.field_validator("CL")
    @classmethod
    def validate_cl_non_negative(cls, v: decimal.Decimal | None) -> decimal.Decimal | None:
        if v is not None and v < 0:
            msg = "CL (Cumulated Loss) must be non-negative"
            raise ValueError(msg)
        return v

    @pydantic.model_validator(mode="after")
    def validate_ri_ru_group(self) -> Reading:
        ri_present = self.RI is not None
        ru_present = self.RU is not None

        if ri_present != ru_present:
            msg = (
                "RI (Reading Identification) and RU (Reading Unit) must both be "
                "present or both absent"
            )
            raise ValueError(msg)

        return self

    @property
    def timestamp(self):
        return self.TM.timestamp

    @property
    def time_status(self) -> TimeStatus:
        return self.TM.status
