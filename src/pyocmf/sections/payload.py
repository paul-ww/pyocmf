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
    EMAID,
    EVCCID,
    EVCOID,
    ISO7812,
    ISO14443,
    ISO15693,
    PHONE_NUMBER,
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

    @pydantic.model_validator(mode="before")
    @classmethod
    def apply_reading_inheritance(cls, data: dict) -> dict:
        """Apply field inheritance for readings.

        Per OCMF spec, some reading fields can be inherited from the previous reading
        if not specified.
        """
        if not isinstance(data, dict):
            return data

        readings_data = data.get("RD", [])
        if not readings_data:
            return data

        inheritable_fields = ["TM", "TX", "RI", "RU", "RT", "EF", "ST"]
        last_values: dict[str, str] = {}
        processed_readings = []

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

            processed_readings.append(reading_dict)

        return {**data, "RD": processed_readings}

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

    @pydantic.model_validator(mode="after")
    def validate_id_format_by_type(self) -> Payload:
        """Validate ID format based on the Identification Type (IT).

        Per OCMF spec Table 17, each identification type has specific format requirements:
        - ISO14443: 8 or 14 hex chars
        - ISO15693: 16 hex chars
        - EMAID: 14-15 alphanumeric
        - EVCCID: max 6 chars
        - EVCOID: specific pattern
        - ISO7812: 8-19 digits
        - PHONE_NUMBER: valid phone number
        - LOCAL, CENTRAL, CARD_TXN_NR, KEY_CODE: no format defined (accept any string)
        - NONE, DENIED, UNDEFINED: no ID should be provided
        """
        if not self.ID or not self.IT:
            return self

        it_value = self.IT.value if isinstance(self.IT, IdentificationType) else str(self.IT)
        id_value = self.ID

        # Types with no format defined - accept any string
        unrestricted_types = {
            IdentificationType.LOCAL.value,
            IdentificationType.LOCAL_1.value,
            IdentificationType.LOCAL_2.value,
            IdentificationType.CENTRAL.value,
            IdentificationType.CENTRAL_1.value,
            IdentificationType.CENTRAL_2.value,
            IdentificationType.CARD_TXN_NR.value,
            IdentificationType.KEY_CODE.value,
        }

        if it_value in unrestricted_types:
            # Accept any string value for these types
            return self

        # For format-restricted types, validate the format using TypeAdapter
        try:
            if self.IT == IdentificationType.ISO14443:
                # Validate against ISO14443 pattern (8 or 14 hex chars)
                pydantic.TypeAdapter(ISO14443).validate_python(id_value)
            elif self.IT == IdentificationType.ISO15693:
                pydantic.TypeAdapter(ISO15693).validate_python(id_value)
            elif self.IT == IdentificationType.EMAID:
                pydantic.TypeAdapter(EMAID).validate_python(id_value)
            elif self.IT == IdentificationType.EVCCID:
                pydantic.TypeAdapter(EVCCID).validate_python(id_value)
            elif self.IT == IdentificationType.EVCOID:
                pydantic.TypeAdapter(EVCOID).validate_python(id_value)
            elif self.IT == IdentificationType.ISO7812:
                pydantic.TypeAdapter(ISO7812).validate_python(id_value)
            elif self.IT == IdentificationType.PHONE_NUMBER:
                pydantic.TypeAdapter(PHONE_NUMBER).validate_python(id_value)
            # NONE, DENIED, UNDEFINED don't accept ID values (currently not validated)
        except pydantic.ValidationError as e:
            msg = f"ID value '{id_value}' does not match format for identification type '{it_value}': {e}"
            raise ValidationError(msg) from e

        return self
