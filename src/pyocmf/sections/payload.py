from __future__ import annotations

import pydantic
from pyocmf.custom_types.cable_loss import CableLossCompensation
from pyocmf.custom_types.strings import (
    ChargePointIdentificationType,
    IdentificationData,
    IdentificationFlag,
    IdentificationType,
    PaginationString,
    UserAssignmentStatus,
)
from pyocmf.sections.readings import Reading
from typing import List


class Payload(pydantic.BaseModel):
    FV: str | None = pydantic.Field(default=None, description="Format Version")
    GI: str | None = pydantic.Field(default=None, description="Gateway Identification")
    GS: str | None = pydantic.Field(default=None, description="Gateway Serial")
    GV: str | None = pydantic.Field(default=None, description="Gateway Version")

    PG: PaginationString = pydantic.Field(description="Pagination")

    MV: str | None = pydantic.Field(default=None, description="Meter Vendor")
    MM: str | None = pydantic.Field(default=None, description="Meter Model")
    MS: str | None = pydantic.Field(default=None, description="Meter Serial")
    MF: str | None = pydantic.Field(default=None, description="Meter Firmware")

    # User Assignment fields (optional, transaction reference dependent)
    IS: bool = pydantic.Field(description="Identification Status")
    IL: UserAssignmentStatus | None = pydantic.Field(
        default=None, description="Identification Level"
    )
    IF: List[IdentificationFlag] = pydantic.Field(
        default=[], description="Identification Flags"
    )
    IT: IdentificationType | None = pydantic.Field(
        default=IdentificationType.NONE, description="Identification Type"
    )
    ID: IdentificationData | None = pydantic.Field(
        default=None, description="Identification Data"
    )
    TT: str | None = pydantic.Field(default=None, description="Tariff Text")

    # EVSE Metrologic parameters (optional)
    CF: str | None = pydantic.Field(
        default=None, max_length=25, description="Charge Controller Firmware Version"
    )
    LC: CableLossCompensation | None = pydantic.Field(
        default=None, description="Loss Compensation"
    )

    # Charge Point Assignment (optional)
    CT: ChargePointIdentificationType | None = pydantic.Field(
        default=None, description="Charge Point Identification Type"
    )
    CI: str | None = pydantic.Field(
        default=None, description="Charge Point Identification"
    )

    RD: List[Reading] = pydantic.Field(description="Readings")

    @pydantic.field_validator("FV", mode="before")
    @classmethod
    def convert_fv_to_string(cls, v: int | float | str | None) -> str | None:
        """Convert FV (Format Version) from float/int to string if needed."""
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @pydantic.field_validator("CT", mode="before")
    @classmethod
    def convert_ct_empty_to_none(cls, v: str | int | None) -> str | None:
        """Convert empty CT (Charge Point Identification Type) values to None."""
        if v == "" or v == 0:
            return None
        if isinstance(v, int):
            return str(v)
        return v

    @pydantic.model_validator(mode="after")
    def validate_serial_numbers(self) -> Payload:
        """Either GS or MS must be present for signature component identification"""
        if not self.GS and not self.MS:
            raise ValueError(
                "Either Gateway Serial (GS) or Meter Serial (MS) must be provided"
            )
        return self

    @classmethod
    def from_flat_dict(cls, data: dict) -> Payload:
        # Extract readings and apply field inheritance
        readings_data = data.get("RD", [])
        readings = []

        # Fields that can be inherited from previous readings
        inheritable_fields = ["TM", "TX", "RI", "RU", "RT", "EF", "ST"]
        last_values: dict[str, str] = {}

        for rd in readings_data:
            # Create a copy of the reading data
            reading_dict = rd.copy()

            # Apply inheritance for missing fields
            for field in inheritable_fields:
                if field not in reading_dict and field in last_values:
                    reading_dict[field] = last_values[field]

            # Update last_values with current reading's values
            for field in inheritable_fields:
                if field in reading_dict:
                    last_values[field] = reading_dict[field]

            readings.append(Reading(**reading_dict))

        # Create payload with all fields from the flat dict
        payload_data = {k: v for k, v in data.items() if k != "RD"}
        payload_data["RD"] = readings

        return cls(**payload_data)
