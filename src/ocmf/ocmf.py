import pydantic
from typing import Literal
from ocmf.sections.payload import Payload
from ocmf.sections.signature import Signature

class OCMF(pydantic.BaseModel):
    header: Literal["OCMF"]
    payload: Payload
    signature: Signature