import pydantic
import decimal
from pyocmf.custom_types.units import ResistanceUnit


class CableLossCompensation(pydantic.BaseModel):
    LN: str | None = pydantic.Field(
        default=None, max_length=20, description="Loss Compensation Naming"
    )
    LI: int | None = pydantic.Field(
        default=None, description="Loss Compensation Identification"
    )
    LR: decimal.Decimal = pydantic.Field(
        description="Loss Compensation Cable Resistance"
    )
    LU: ResistanceUnit = pydantic.Field(description="Loss Compensation Unit")


class MetrologicParameters(pydantic.BaseModel):
    CF: str | None = pydantic.Field(
        default=None, max_length=25, description="Charge Controller Firmware Version"
    )
    LC: CableLossCompensation | None = pydantic.Field(
        default=None, description="Loss Compensation"
    )
