from __future__ import annotations

import decimal
import re
from typing import Any

import pydantic

from pyocmf.core.reading import Reading
from pyocmf.enums.identifiers import IdentificationType
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
from pyocmf.types.lenient import (
    LenientBool,
    LenientChargePointIdentificationType,
    LenientIdentificationFlag,
    LenientIdentificationType,
    LenientUserAssignmentStatus,
    warn_spec,
)

# OCMF spec Table 2: context letter (T or F) and a number without leading zeros
_PAGINATION_PATTERN = re.compile(r"^[TF](0|[1-9][0-9]*)$")
_MAX_IDENTIFICATION_FLAGS = 4
_MAX_TARIFF_TEXT_LENGTH = 250
_MAX_CHARGE_CONTROLLER_FIRMWARE_LENGTH = 25


class Payload(pydantic.BaseModel):
    """Payload section of an OCMF record: gateway, meter, user assignment and readings.

    Reading fields left out after the first reading are inherited from the previous
    reading, as the OCMF spec allows.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    FV: str | None = pydantic.Field(default=None, description="Format Version")
    GI: str | None = pydantic.Field(default=None, description="Gateway Identification")
    GS: str | None = pydantic.Field(default=None, description="Gateway Serial")
    GV: str | None = pydantic.Field(default=None, description="Gateway Version")

    PG: str | None = pydantic.Field(default=None, description="Pagination")

    MV: str | None = pydantic.Field(default=None, description="Meter Vendor")
    MM: str | None = pydantic.Field(default=None, description="Meter Model")
    MS: str | None = pydantic.Field(default=None, description="Meter Serial")
    MF: str | None = pydantic.Field(default=None, description="Meter Firmware")

    IS: LenientBool | None = pydantic.Field(default=None, description="Identification Status")
    IL: LenientUserAssignmentStatus | None = pydantic.Field(
        default=None, description="Identification Level"
    )
    IF: list[LenientIdentificationFlag] = pydantic.Field(
        default=[], description="Identification Flags (0..4 per OCMF spec Table 4)"
    )
    IT: LenientIdentificationType | None = pydantic.Field(
        default=IdentificationType.NONE, description="Identification Type"
    )
    ID: IdentificationData | None = pydantic.Field(default=None, description="Identification Data")
    TT: str | None = pydantic.Field(default=None, description="Tariff Text (0..250)")

    CF: str | None = pydantic.Field(
        default=None, description="Charge Controller Firmware Version (0..25)"
    )
    LC: CableLossCompensation | None = pydantic.Field(default=None, description="Loss Compensation")

    CT: LenientChargePointIdentificationType | None = pydantic.Field(
        default=None, description="Charge Point Identification Type"
    )
    CI: str | None = pydantic.Field(default=None, description="Charge Point Identification")

    RD: list[Reading] = pydantic.Field(description="Readings")

    @pydantic.model_validator(mode="before")
    @classmethod
    def apply_reading_inheritance(cls, data: dict[str, Any]) -> dict[str, Any]:
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
    def warn_on_spec_deviations(self) -> Payload:
        """Warn about OCMF spec violations the Transparenzsoftware tolerates."""
        if self.PG is None or not _PAGINATION_PATTERN.match(self.PG):
            warn_spec(f"Pagination (PG) '{self.PG}' must be 'T' or 'F' followed by a number")
        if self.IS is None:
            warn_spec("Identification Status (IS) is mandatory")
        # GS is optional (0..1) and MS mandatory (1..1), but either one identifies the
        # signature component
        if self.GS is None and self.MS is None:
            warn_spec("Either Gateway Serial (GS) or Meter Serial (MS) must be provided")
        if len(self.IF) > _MAX_IDENTIFICATION_FLAGS:
            warn_spec(
                f"At most {_MAX_IDENTIFICATION_FLAGS} identification flags (IF) are allowed, "
                f"got {len(self.IF)}"
            )
        if self.TT is not None and len(self.TT) > _MAX_TARIFF_TEXT_LENGTH:
            warn_spec(f"Tariff Text (TT) exceeds {_MAX_TARIFF_TEXT_LENGTH} characters")
        if self.CF is not None and len(self.CF) > _MAX_CHARGE_CONTROLLER_FIRMWARE_LENGTH:
            warn_spec(
                f"Charge Controller Firmware (CF) exceeds "
                f"{_MAX_CHARGE_CONTROLLER_FIRMWARE_LENGTH} characters"
            )
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
        """Warn when the ID does not match the format of its Identification Type (IT).

        Types without a defined format (LOCAL, CENTRAL, KEY_CODE, ...) accept any value.
        """
        if not self.ID or self.IT is None:
            return self

        adapter = _ID_FORMAT_ADAPTERS.get(self.IT)
        if adapter is None:
            return self

        try:
            adapter.validate_python(self.ID)
        except pydantic.ValidationError:
            warn_spec(
                f"ID value '{self.ID}' does not match expected format for identification "
                f"type '{self.IT}'"
            )
        return self


_ID_FORMAT_ADAPTERS: dict[IdentificationType, pydantic.TypeAdapter[Any]] = {
    IdentificationType.ISO14443: pydantic.TypeAdapter(ISO14443),
    IdentificationType.ISO15693: pydantic.TypeAdapter(ISO15693),
    IdentificationType.EMAID: pydantic.TypeAdapter(EMAID),
    IdentificationType.EVCCID: pydantic.TypeAdapter(EVCCID),
    IdentificationType.EVCOID: pydantic.TypeAdapter(EVCOID),
    IdentificationType.ISO7812: pydantic.TypeAdapter(ISO7812),
    IdentificationType.PHONE_NUMBER: pydantic.TypeAdapter(PHONE_NUMBER),
}
