import pydantic
from pyocmf.custom_types.units import ResistanceUnit


class CableLossCompensation(pydantic.BaseModel):
    LN: str = pydantic.Field(description="Loss Compensation Naming")
    LI: int = pydantic.Field(description="Loss Compensation Identification")
    LR: int = pydantic.Field(description="Loss Compensation Cable Resistance")
    LU: ResistanceUnit = pydantic.Field(description="Loss Compensation Unit")


class MetrologicParameters(pydantic.BaseModel):
    CF: str | None = pydantic.Field(description="Charge Controller Firmware Version")
    LC: CableLossCompensation = pydantic.Field(description="Loss Compensation")
