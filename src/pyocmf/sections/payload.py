from __future__ import annotations

from typing import List

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
    model_config = pydantic.ConfigDict(
        extra="allow"
    )  # Allow extension fields U, V, W, X, Y, Z

    FV: str | None = pydantic.Field(default=None, description="Format Version")
    GI: str | None = pydantic.Field(default=None, description="Gateway Identification")
    GS: str | None = pydantic.Field(default=None, description="Gateway Serial")
    GV: str | None = pydantic.Field(default=None, description="Gateway Version")

    PG: PaginationString = pydantic.Field(description="Pagination")

    MV: str | None = pydantic.Field(default=None, description="Meter Vendor")
    MM: str | None = pydantic.Field(default=None, description="Meter Model")
    MS: str | None = pydantic.Field(
        default=None, description="Meter Serial - Mandatory per spec"
    )
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
    # Note: CT can be enum or free text in practice (spec shows enum but implementations vary)
    CT: ChargePointIdentificationType | str | None = pydantic.Field(
        default=None, description="Charge Point Identification Type"
    )
    CI: str | None = pydantic.Field(
        default=None, description="Charge Point Identification"
    )

    RD: List[Reading] = pydantic.Field(description="Readings")

    @pydantic.model_validator(mode="after")
    def validate_serial_numbers(self) -> Payload:
        """Either GS or MS must be present for signature component identification"""
        if not self.GS and not self.MS:
            raise ValidationError(
                "Either Gateway Serial (GS) or Meter Serial (MS) must be provided"
            )
        return self

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

    def to_flat_dict(self) -> dict:
        """Convert the Payload back to a flat dictionary format."""
        import decimal

        result = {}

        # Add all defined model fields
        for field_name, field_info in self.__class__.model_fields.items():
            if field_name != "RD":  # Handle readings separately
                value = getattr(self, field_name)
                if value is not None:
                    # Convert enums and custom types to their string representation
                    if hasattr(value, "value"):
                        result[field_name] = value.value
                    elif isinstance(value, list):
                        # Handle list fields like IF (IdentificationFlags)
                        result[field_name] = [
                            item.value if hasattr(item, "value") else item
                            for item in value
                        ]
                    elif isinstance(value, decimal.Decimal):
                        # Convert Decimal to float for JSON serialization
                        result[field_name] = float(value)
                    else:
                        result[field_name] = value

        # Add extension fields (U, V, W, X, Y, Z, etc.) stored in __pydantic_extra__
        if hasattr(self, "__pydantic_extra__") and self.__pydantic_extra__:
            for field_name, value in self.__pydantic_extra__.items():
                if value is not None:
                    result[field_name] = value

        # Add readings - convert them using pydantic's model_dump which handles Decimals
        readings_list = []
        for reading in self.RD:
            reading_dict = reading.model_dump(exclude_none=True)
            # Convert Decimal values to float in the reading dict
            for key, val in reading_dict.items():
                if isinstance(val, decimal.Decimal):
                    reading_dict[key] = float(val)
            readings_list.append(reading_dict)

        result["RD"] = readings_list

        return result

    def to_flat_dict_json(self) -> str:
        """Convert the Payload to a flat dictionary and return as JSON string."""
        import json

        return json.dumps(self.to_flat_dict(), separators=(",", ":"))
        import json

        return json.dumps(self.to_flat_dict(), separators=(",", ":"))
