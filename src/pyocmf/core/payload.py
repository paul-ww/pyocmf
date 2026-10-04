from __future__ import annotations

import decimal
import warnings

import pydantic

from pyocmf.core.reading import Reading
from pyocmf.enums.identifiers import (
    ChargePointIdentificationType,
    IdentificationFlag,
    IdentificationType,
    UserAssignmentStatus,
)
from pyocmf.exceptions import ValidationError
from pyocmf.models.cable_loss import CableLossCompensation
from pyocmf.types.identifiers import (
    EMAID,
    EVCCID,
    EVCOID,
    ISO7812,
    ISO14443,
    ISO15693,
    PHONE_NUMBER,
    IdentificationData,
    PaginationString,
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
    IF: list[IdentificationFlag] = pydantic.Field(
        default=[], max_length=4, description="Identification Flags (0..4 per OCMF spec Table 4)"
    )
    IT: IdentificationType | None = pydantic.Field(
        default=IdentificationType.NONE, description="Identification Type"
    )
    ID: IdentificationData | None = pydantic.Field(default=None, description="Identification Data")
    TT: str | None = pydantic.Field(default=None, max_length=250, description="Tariff Text")

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

        if isinstance(readings_data[0], Reading):
            return data

        inheritable_fields = ["TM", "TX", "RI", "RU", "RT", "EF", "ST"]
        last_values: dict[str, str] = {}
        processed_readings = []

        for rd in readings_data:
            reading_dict = {
                field: rd.get(field, last_values.get(field))
                for field in inheritable_fields
                if field in rd or field in last_values
            }
            reading_dict.update({k: v for k, v in rd.items() if k not in inheritable_fields})

            last_values.update({k: v for k, v in reading_dict.items() if k in inheritable_fields})

            processed_readings.append(reading_dict)

        return {**data, "RD": processed_readings}

    @pydantic.model_validator(mode="after")
    def validate_serial_numbers(self) -> Payload:
        """Either GS or MS must be present for signature component identification.

        Per OCMF spec: GS is optional (0..1) but MS is mandatory (1..1).
        However, at least one must be non-None (though can be empty string).
        """
        if self.GS is None and self.MS is None:
            msg = "Either Gateway Serial (GS) or Meter Serial (MS) must be provided"
            raise ValidationError(msg)
        return self

    @pydantic.field_validator("FV", mode="before")
    @classmethod
    def convert_fv_to_string(cls, v: int | float | decimal.Decimal | str | None) -> str | None:
        if isinstance(v, (int, float, decimal.Decimal)):
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

    @pydantic.model_validator(mode="after")
    def validate_id_format_by_type(self) -> Payload:
        """Validate ID format based on the Identification Type (IT).

        Types without a defined format (LOCAL, CENTRAL, KEY_CODE, ...) accept any value.
        Mismatches raise ValidationError, except for ISO14443 and ISO15693, which only
        warn because real-world RFID cards often use vendor-specific UID lengths.
        """
        if not self.ID or self.IT is None:
            return self

        adapter = _ID_FORMAT_ADAPTERS.get(self.IT)
        if adapter is None:
            return self

        try:
            adapter.validate_python(self.ID)
        except pydantic.ValidationError as e:
            msg = (
                f"ID value '{self.ID}' does not match expected format for identification "
                f"type '{self.IT.value}'"
            )
            if self.IT not in _PERMISSIVE_ID_TYPES:
                error_msg = f"{msg}: {e}"
                raise ValidationError(error_msg) from e
            warnings.warn(
                f"{msg}. This may indicate non-standard RFID card format or vendor-specific "
                f"implementation. Data will be accepted but may not be fully spec-compliant.",
                UserWarning,
                stacklevel=3,
            )
        return self


_ID_FORMAT_ADAPTERS: dict[IdentificationType, pydantic.TypeAdapter] = {
    IdentificationType.ISO14443: pydantic.TypeAdapter(ISO14443),
    IdentificationType.ISO15693: pydantic.TypeAdapter(ISO15693),
    IdentificationType.EMAID: pydantic.TypeAdapter(EMAID),
    IdentificationType.EVCCID: pydantic.TypeAdapter(EVCCID),
    IdentificationType.EVCOID: pydantic.TypeAdapter(EVCOID),
    IdentificationType.ISO7812: pydantic.TypeAdapter(ISO7812),
    IdentificationType.PHONE_NUMBER: pydantic.TypeAdapter(PHONE_NUMBER),
}

_PERMISSIVE_ID_TYPES = {IdentificationType.ISO14443, IdentificationType.ISO15693}
