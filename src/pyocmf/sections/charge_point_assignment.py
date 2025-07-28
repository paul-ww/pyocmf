import pydantic
import enum

class ChargePointIdentificationType(enum.StrEnum):
    EVSEID = "EVSEID"
    CBIDC = "CBIDC"


class ChargePointAssignment(pydantic.BaseModel):
    CT: ChargePointIdentificationType = pydantic.Field(
        description="Charge Point Identification Type"
    )
    CI: str = pydantic.Field(description="Charge Point Identification")
