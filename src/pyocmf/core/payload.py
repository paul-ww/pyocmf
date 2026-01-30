from __future__ import annotations

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
    IF: list[IdentificationFlag] = pydantic.Field(default=[], description="Identification Flags")
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

        if readings_data and isinstance(readings_data[0], Reading):
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

    # Validator mapping at class level to avoid recreation
    _ID_FORMAT_VALIDATORS = {
        IdentificationType.ISO14443.value: ISO14443,
        IdentificationType.ISO15693.value: ISO15693,
        IdentificationType.EMAID.value: EMAID,
        IdentificationType.EVCCID.value: EVCCID,
        IdentificationType.EVCOID.value: EVCOID,
        IdentificationType.ISO7812.value: ISO7812,
        IdentificationType.PHONE_NUMBER.value: PHONE_NUMBER,
    }

    # Types that accept any string value without validation
    _UNRESTRICTED_TYPES = {
        IdentificationType.LOCAL.value,
        IdentificationType.LOCAL_1.value,
        IdentificationType.LOCAL_2.value,
        IdentificationType.CENTRAL.value,
        IdentificationType.CENTRAL_1.value,
        IdentificationType.CENTRAL_2.value,
        IdentificationType.CARD_TXN_NR.value,
        IdentificationType.KEY_CODE.value,
        IdentificationType.UNDEFINED.value,
        IdentificationType.NONE.value,
        IdentificationType.DENIED.value,
    }

    # Types that validate with warnings instead of errors (permissive mode)
    _PERMISSIVE_TYPES = {
        IdentificationType.ISO14443.value,
        IdentificationType.ISO15693.value,
    }

    def _validate_id_format(self, it_value: str, id_value: str, *, strict: bool = True) -> None:
        """Validate ID format, either strictly (raise) or permissively (warn).

        Args:
            it_value: Identification type value
            id_value: Identification data value
            strict: If True, raise ValidationError on mismatch. If False, emit warning.

        """
        if it_value not in self._ID_FORMAT_VALIDATORS:
            return

        try:
            pydantic.TypeAdapter(self._ID_FORMAT_VALIDATORS[it_value]).validate_python(id_value)
        except pydantic.ValidationError as e:
            msg = (
                f"ID value '{id_value}' does not match expected format for identification "
                f"type '{it_value}'"
            )

            if strict:
                error_msg = f"{msg}: {e}"
                raise ValidationError(error_msg) from e
            else:
                warnings.warn(
                    f"{msg}. This may indicate non-standard RFID card format or vendor-specific "
                    f"implementation. Data will be accepted but may not be fully spec-compliant.",
                    UserWarning,
                    stacklevel=4,
                )

    @pydantic.model_validator(mode="after")
    def validate_id_format_by_type(self) -> Payload:
        """Validate ID format based on the Identification Type (IT).

        For most types, validation is strict (raises ValidationError).
        For ISO14443 and ISO15693, validation emits warnings but allows non-standard formats,
        as real-world RFID cards may have vendor-specific implementations.
        """
        if not self.ID or not self.IT:
            return self

        it_value = self.IT.value if isinstance(self.IT, IdentificationType) else str(self.IT)
        id_value = self.ID

        if it_value in self._UNRESTRICTED_TYPES:
            return self

        # Use permissive validation (warn) for ISO types, strict for others
        strict = it_value not in self._PERMISSIVE_TYPES
        self._validate_id_format(it_value, id_value, strict=strict)
        return self
