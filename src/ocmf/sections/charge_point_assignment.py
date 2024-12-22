import pydantic
from typing import Literal

ChargePointIdentificationType = Literal["EVSEID", "CBIDC"]


class ChargePointAssignment(pydantic.BaseModel):
    CT: ChargePointIdentificationType = pydantic.Field(
        description="Charge Point Identification Type"
    )
    CI: str = pydantic.Field(description="Charge Point Identification")
