import pydantic
from typing import Annotated, List
from ocmf.sections.readings import Reading


TransactionContext = Annotated[str, pydantic.constr(pattern=r"^T[1-9]*$")]
FiscalContext = Annotated[str, pydantic.constr(pattern=r"^F[1-9]*$")]
PaginationString = TransactionContext | FiscalContext


class GeneralInformation(pydantic.BaseModel):
    FV: str = pydantic.Field(description="Format Version")
    GI: str = pydantic.Field(description="Gateway Identification")
    GS: str = pydantic.Field(description="Gateway Serial")
    GV: str | None = pydantic.Field(description="Gateway Version")


class Pagination(pydantic.BaseModel):
    PG: PaginationString = pydantic.Field(description="Pagination")


class MeterIdentification(pydantic.BaseModel):
    MV: str = pydantic.Field(description="Meter Vendor")
    MM: str = pydantic.Field(description="Meter Model")
    MS: str = pydantic.Field(description="Meter Serial")
    MF: str = pydantic.Field(description="Meter Firmware")


class Payload(pydantic.BaseModel):
    general_information: GeneralInformation
    pagination: Pagination
    meter_identification: MeterIdentification
    readings: List[Reading]
