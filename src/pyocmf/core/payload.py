from __future__ import annotations

import pydantic

from pyocmf.core.reading import Reading
from pyocmf.enums.identifiers import (
    ChargePointIdentificationType,
    IdentificationFlag,
    IdentificationFlagIso15118,
    IdentificationFlagOCPP,
    IdentificationFlagPLMN,
    IdentificationFlagRFID,
    IdentificationType,
    UserAssignmentStatus,
)
from pyocmf.enums.reading import MeterReadingReason
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
)
from pyocmf.types.pagination import PaginationString


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

        from pyocmf.core.reading import Reading

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
        """Either GS or MS must be present for signature component identification."""
        if not self.GS and not self.MS:
            msg = "Either Gateway Serial (GS) or Meter Serial (MS) must be provided"
            raise ValidationError(msg)
        return self

    @pydantic.model_validator(mode="after")
    def validate_tx_sequence(self) -> Payload:
        """Validate transaction type (TX) sequence within readings."""
        if not self.RD or len(self.RD) < 2:
            return self

        begin_seen = False
        end_seen = False

        for i, reading in enumerate(self.RD):
            if reading.TX is None:
                continue

            tx = reading.TX

            if tx == MeterReadingReason.BEGIN:
                if end_seen:
                    msg = f"Reading {i}: TX=B (Begin) cannot appear after transaction end"
                    raise ValidationError(msg)
                begin_seen = True

            elif tx in (
                MeterReadingReason.END,
                MeterReadingReason.TERMINATION_LOCAL,
                MeterReadingReason.TERMINATION_REMOTE,
                MeterReadingReason.TERMINATION_ABORT,
                MeterReadingReason.TERMINATION_POWER_FAILURE,
            ):
                if not begin_seen:
                    msg = f"Reading {i}: TX={tx.value} (End) requires TX=B (Begin) first"
                    raise ValidationError(msg)
                end_seen = True

            elif tx in (
                MeterReadingReason.CHARGING,
                MeterReadingReason.EXCEPTION,
                MeterReadingReason.SUSPENDED,
                MeterReadingReason.TARIFF_CHANGE,
            ):
                if end_seen:
                    msg = f"Reading {i}: TX={tx.value} cannot appear after transaction end"
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

    @pydantic.field_validator("IF")
    @classmethod
    def validate_flags_consistent_source(
        cls, v: list[IdentificationFlag]
    ) -> list[IdentificationFlag]:
        """Ensure IF flags don't mix from different tables."""
        if not v or len(v) <= 1:
            return v

        all_none = all(str(flag).endswith("_NONE") for flag in v)
        if all_none:
            return v

        categories = set()
        for flag in v:
            if isinstance(flag, IdentificationFlagRFID):
                categories.add("RFID")
            elif isinstance(flag, IdentificationFlagOCPP):
                categories.add("OCPP")
            elif isinstance(flag, IdentificationFlagIso15118):
                categories.add("ISO15118")
            elif isinstance(flag, IdentificationFlagPLMN):
                categories.add("PLMN")

        if len(categories) > 1:
            msg = f"IF (Identification Flags) cannot mix flags from different sources. Found: {', '.join(sorted(categories))}"
            raise ValidationError(msg)

        return v

    def _validate_id_format(self, it_value: str, id_value: str) -> None:
        format_validators = {
            IdentificationType.ISO14443.value: ISO14443,
            IdentificationType.ISO15693.value: ISO15693,
            IdentificationType.EMAID.value: EMAID,
            IdentificationType.EVCCID.value: EVCCID,
            IdentificationType.EVCOID.value: EVCOID,
            IdentificationType.ISO7812.value: ISO7812,
            IdentificationType.PHONE_NUMBER.value: PHONE_NUMBER,
        }

        if it_value not in format_validators:
            return

        try:
            pydantic.TypeAdapter(format_validators[it_value]).validate_python(id_value)
        except pydantic.ValidationError as e:
            msg = f"ID value '{id_value}' does not match format for identification type '{it_value}': {e}"
            raise ValidationError(msg) from e

    @pydantic.model_validator(mode="after")
    def validate_id_format_by_type(self) -> Payload:
        """Validate ID format based on the Identification Type (IT)."""
        if self.IT in (
            IdentificationType.NONE,
            IdentificationType.DENIED,
            IdentificationType.UNDEFINED,
        ):
            if self.ID is not None and self.ID != "":
                msg = f"ID must be None or empty when IT={self.IT.value} (no assignment type)"
                raise ValidationError(msg)
            return self

        if not self.ID or not self.IT:
            return self

        it_value = self.IT.value if isinstance(self.IT, IdentificationType) else str(self.IT)
        id_value = self.ID

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
            return self

        self._validate_id_format(it_value, id_value)
        return self
