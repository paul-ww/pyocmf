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
    MS: str | None = pydantic.Field(description="Meter Serial")
    MF: str | None = pydantic.Field(default=None, description="Meter Firmware")

    # User Assignment fields (optional, transaction reference dependent)
    IS: bool = pydantic.Field(description="Identification Status")
    IL: UserAssignmentStatus | None = pydantic.Field(description="Identification Level")
    IF: List[IdentificationFlag] = pydantic.Field(
        default=[], description="Identification Flags"
    )
    IT: IdentificationType = pydantic.Field(description="Identification Type")
    ID: IdentificationData = pydantic.Field(description="Identification Data")
    TT: str = pydantic.Field(description="Tariff Text")

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
        # Extract readings
        readings_data = data.get("RD", [])
        readings = [Reading(**rd) for rd in readings_data]

        # Create payload with all fields from the flat dict
        payload_data = {k: v for k, v in data.items() if k != "RD"}
        payload_data["RD"] = readings

        return cls(**payload_data)
