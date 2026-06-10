import pydantic

from pyocmf.enums.units import ResistanceUnit
from pyocmf.types.numbers import OCMFNumber


class CableLossCompensation(pydantic.BaseModel):
    LN: str | None = pydantic.Field(
        default=None, max_length=20, description="Loss Compensation Naming"
    )
    LI: int | None = pydantic.Field(default=None, description="Loss Compensation Identification")
    LR: OCMFNumber = pydantic.Field(description="Loss Compensation Cable Resistance")
    LU: ResistanceUnit = pydantic.Field(description="Loss Compensation Unit")
