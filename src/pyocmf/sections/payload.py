"""OCMF payload section containing meter readings and metadata.

This module defines the Payload model which contains all the charging session
metadata, meter information, identification data, and meter readings.
"""

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
    """OCMF payload containing meter readings and session metadata.

    The payload contains information about the gateway, meter, user identification,
    charge point, and the actual meter readings from the charging session.
    """

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
        """Either GS or MS must be present for signature component identification."""
        if not self.GS and not self.MS:
            msg = "Either Gateway Serial (GS) or Meter Serial (MS) must be provided"
            raise ValidationError(msg)
        return self

    @pydantic.field_validator("FV", mode="before")
    @classmethod
    def convert_fv_to_string(cls, v: int | float | str | None) -> str | None:
        """Convert numeric format version values to strings."""
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @pydantic.field_validator("CT", mode="before")
    @classmethod
    def convert_ct_empty_to_none(cls, v: str | int | None) -> str | None:
        """Convert empty strings and zero values to None for charge point type."""
        if v == "" or v == 0:
            return None
        if isinstance(v, int):
            return str(v)
        return v

    @classmethod
    def from_flat_dict(cls, data: dict) -> Payload:
        """Parse payload data with inheritable reading fields.

        Some reading fields can be inherited from the previous reading if not specified.
        """
        readings_data = data.get("RD", [])
        readings = []

        inheritable_fields = ["TM", "TX", "RI", "RU", "RT", "EF", "ST"]
        last_values: dict[str, str] = {}

        for rd in readings_data:
            # Inherit missing fields from previous reading
            reading_dict = {
                field: rd.get(field, last_values.get(field))
                for field in inheritable_fields
                if field in rd or field in last_values
            }
            # Add non-inheritable fields
            reading_dict.update({k: v for k, v in rd.items() if k not in inheritable_fields})

            # Update last_values with current reading's inheritable fields
            last_values.update({k: v for k, v in reading_dict.items() if k in inheritable_fields})

            readings.append(Reading(**reading_dict))

        payload_data = {k: v for k, v in data.items() if k != "RD"}
        payload_data["RD"] = readings
        return cls(**payload_data)

    def to_flat_dict(self) -> dict:
        """Convert the Payload back to a flat dictionary format."""
        return self.model_dump(mode="python", exclude_none=True)

    def to_flat_dict_json(self) -> str:
        """Convert the Payload to a flat dictionary and return as JSON string."""
        return self.model_dump_json(exclude_none=True)
