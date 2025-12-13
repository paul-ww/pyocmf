from __future__ import annotations

import pydantic

from pyocmf.exceptions import ValidationError
from pyocmf.sections.reading import Reading
from pyocmf.types.cable_loss import CableLossCompensation
from pyocmf.types.identifiers import (
    ChargePointIdentificationType,
    IdentificationData,
    IdentificationFlag,
    IdentificationType,
    PaginationString,
    UserAssignmentStatus,
)


class Payload(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="allow")

    FV: str | None = pydantic.Field(default=None, description="Format Version")
    GI: str | None = pydantic.Field(default=None, description="Gateway Identification")
    GS: str | None = pydantic.Field(default=None, description="Gateway Serial")
    GV: str | None = pydantic.Field(default=None, description="Gateway Version")

    PG: PaginationString = pydantic.Field(description="Pagination")

    MV: str | None = pydantic.Field(default=None, description="Meter Vendor")
    MM: str | None = pydantic.Field(default=None, description="Meter Model")
    MS: str | None = pydantic.Field(default=None, description="Meter Serial")
    MF: str | None = pydantic.Field(default=None, description="Meter Firmware")

    IS: bool = pydantic.Field(description="Identification Status")
    IL: UserAssignmentStatus | None = pydantic.Field(
        default=None, description="Identification Level"
    )
    IF: list[IdentificationFlag] = pydantic.Field(default=[], description="Identification Flags")
    IT: IdentificationType | None = pydantic.Field(
        default=IdentificationType.NONE, description="Identification Type"
    )
    ID: IdentificationData | None = pydantic.Field(default=None, description="Identification Data")
    TT: str | None = pydantic.Field(default=None, description="Tariff Text")

    CF: str | None = pydantic.Field(
        default=None, max_length=25, description="Charge Controller Firmware Version"
    )
    LC: CableLossCompensation | None = pydantic.Field(default=None, description="Loss Compensation")

    CT: ChargePointIdentificationType | str | None = pydantic.Field(
        default=None, description="Charge Point Identification Type"
    )
    CI: str | None = pydantic.Field(default=None, description="Charge Point Identification")

    RD: list[Reading] = pydantic.Field(description="Readings")

    @pydantic.model_validator(mode="after")
    def validate_serial_numbers(self) -> Payload:
        """Either GS or MS must be present for signature component identification"""
        if not self.GS and not self.MS:
            msg = "Either Gateway Serial (GS) or Meter Serial (MS) must be provided"
            raise ValidationError(msg)
        return self

    @pydantic.field_validator("FV", mode="before")
    @classmethod
    def convert_fv_to_string(cls, v: int | float | str | None) -> str | None:
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @pydantic.field_validator("CT", mode="before")
    @classmethod
    def convert_ct_empty_to_none(cls, v: str | int | None) -> str | None:
        if v == "" or v == 0:
            return None
        if isinstance(v, int):
            return str(v)
        return v

    @classmethod
    def from_flat_dict(cls, data: dict) -> Payload:
        readings_data = data.get("RD", [])
        readings = []

        inheritable_fields = ["TM", "TX", "RI", "RU", "RT", "EF", "ST"]
        last_values: dict[str, str] = {}

        for rd in readings_data:
            reading_dict = rd.copy()

            for field in inheritable_fields:
                if field not in reading_dict and field in last_values:
                    reading_dict[field] = last_values[field]

            for field in inheritable_fields:
                if field in reading_dict:
                    last_values[field] = reading_dict[field]

            readings.append(Reading(**reading_dict))

        payload_data = {k: v for k, v in data.items() if k != "RD"}
        payload_data["RD"] = readings

        return cls(**payload_data)

    def _serialize_field_value(self, value) -> any:
        """Serialize a field value for JSON conversion."""
        import decimal

        if hasattr(value, "value"):
            return value.value
        if isinstance(value, list):
            return [item.value if hasattr(item, "value") else item for item in value]
        if isinstance(value, decimal.Decimal):
            return float(value)
        return value

    def _serialize_reading(self, reading: Reading) -> dict:
        """Serialize a reading to a dictionary with floats instead of Decimals."""
        import decimal

        reading_dict = reading.model_dump(exclude_none=True)
        for key, val in reading_dict.items():
            if isinstance(val, decimal.Decimal):
                reading_dict[key] = float(val)
        return reading_dict

    def to_flat_dict(self) -> dict:
        """Convert the Payload back to a flat dictionary format."""
        result = {}

        for field_name, _field_info in self.__class__.model_fields.items():
            if field_name != "RD":
                value = getattr(self, field_name)
                if value is not None:
                    result[field_name] = self._serialize_field_value(value)

        if hasattr(self, "__pydantic_extra__") and self.__pydantic_extra__:
            for field_name, value in self.__pydantic_extra__.items():
                if value is not None:
                    result[field_name] = value

        result["RD"] = [self._serialize_reading(reading) for reading in self.RD]

        return result

    def to_flat_dict_json(self) -> str:
        """Convert the Payload to a flat dictionary and return as JSON string."""
        import json

        return json.dumps(self.to_flat_dict(), separators=(",", ":"))
