import pydantic
from typing import Annotated, List
from pyocmf.sections.readings import Reading


TransactionContext = Annotated[str, pydantic.constr(pattern=r"^T[1-9]*$")]
FiscalContext = Annotated[str, pydantic.constr(pattern=r"^F[1-9]*$")]
PaginationString = TransactionContext | FiscalContext


class Payload(pydantic.BaseModel):
    # Flattened structure to match OCMF JSON format
    FV: str | None = pydantic.Field(default=None, description="Format Version")
    GI: str | None = pydantic.Field(default=None, description="Gateway Identification")
    GS: str | None = pydantic.Field(default=None, description="Gateway Serial")
    GV: str | None = pydantic.Field(default=None, description="Gateway Version")

    PG: PaginationString = pydantic.Field(description="Pagination")

    MV: str | None = pydantic.Field(default=None, description="Meter Vendor")
    MM: str | None = pydantic.Field(default=None, description="Meter Model")
    MS: str = pydantic.Field(description="Meter Serial")
    MF: str | None = pydantic.Field(default=None, description="Meter Firmware")

    # User Assignment fields (optional, transaction reference dependent)
    IS: bool | None = pydantic.Field(default=None, description="Identification Status")
    IL: str | None = pydantic.Field(default=None, description="Identification Level")
    IF: List[str] | None = pydantic.Field(
        default=None, max_length=4, description="Identification Flags"
    )
    IT: str | None = pydantic.Field(default=None, description="Identification Type")
    ID: str | None = pydantic.Field(default=None, description="Identification Data")
    TT: str | None = pydantic.Field(
        default=None, max_length=250, description="Tariff Text"
    )

    # EVSE Metrologic parameters (optional)
    CF: str | None = pydantic.Field(
        default=None, max_length=25, description="Charge Controller Firmware Version"
    )
    LC: dict | None = pydantic.Field(default=None, description="Loss Compensation")

    # Charge Point Assignment (optional)
    CT: str | None = pydantic.Field(
        default=None, description="Charge Point Identification Type"
    )
    CI: str | None = pydantic.Field(
        default=None, description="Charge Point Identification"
    )

    RD: List[Reading] = pydantic.Field(description="Readings")

    @pydantic.model_validator(mode="after")
    def validate_serial_numbers(self) -> "Payload":
        """Either GS or MS must be present for signature component identification"""
        if not self.GS and not self.MS:
            raise ValueError(
                "Either Gateway Serial (GS) or Meter Serial (MS) must be provided"
            )
        return self

    @classmethod
    def from_flat_dict(cls, data: dict) -> "Payload":
        # Extract readings
        readings_data = data.get("RD", [])
        readings = [Reading(**rd) for rd in readings_data]

        # Create payload with all fields from the flat dict
        payload_data = {k: v for k, v in data.items() if k != "RD"}
        payload_data["RD"] = readings

        return cls(**payload_data)
