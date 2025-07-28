import pydantic
from typing import Annotated, List
from pyocmf.sections.readings import Reading


TransactionContext = Annotated[str, pydantic.constr(pattern=r"^T[1-9]*$")]
FiscalContext = Annotated[str, pydantic.constr(pattern=r"^F[1-9]*$")]
PaginationString = TransactionContext | FiscalContext


class GeneralInformation(pydantic.BaseModel):
    FV: str | None = pydantic.Field(description="Format Version")
    GI: str | None = pydantic.Field(description="Gateway Identification")
    GS: str | None = pydantic.Field(description="Gateway Serial")
    GV: str | None = pydantic.Field(description="Gateway Version")


class Pagination(pydantic.BaseModel):
    PG: PaginationString | None = pydantic.Field(description="Pagination")


class MeterIdentification(pydantic.BaseModel):
    MV: str | None = pydantic.Field(description="Meter Vendor")
    MM: str | None = pydantic.Field(description="Meter Model")
    MS: str | None = pydantic.Field(description="Meter Serial")
    MF: str | None = pydantic.Field(description="Meter Firmware")


class Payload(pydantic.BaseModel):
    general_information: GeneralInformation
    pagination: Pagination
    meter_identification: MeterIdentification
    readings: List[Reading]

    @classmethod
    def from_flat_dict(cls, data: dict) -> "Payload":
        # General Information
        gi_fields = {k: data.get(k) for k in ["FV", "GI", "GS", "GV"]}
        general_information = GeneralInformation(**gi_fields)

        # Pagination
        pagination_fields = {"PG": data.get("PG")}
        pagination = Pagination(**pagination_fields)

        # Meter Identification
        meter_fields = {k: data.get(k) for k in ["MV", "MM", "MS", "MF"]}
        meter_identification = MeterIdentification(**meter_fields)

        # Readings
        readings_data = data.get("RD", [])
        readings = [Reading(**rd) for rd in readings_data]

        # Extend here for metrologic parameters, user assignment, etc.
        return cls(
            general_information=general_information,
            pagination=pagination,
            meter_identification=meter_identification,
            readings=readings,
        )
