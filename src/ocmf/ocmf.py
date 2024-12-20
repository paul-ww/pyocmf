import pydantic
from typing import Literal
from ocmf.payload import Payload
from ocmf.signature import Signature

class OCMF(pydantic.BaseModel):
    version: str = "1.4.0"
    header: Literal["OCMF"]
    payload: Payload
    signature: Signature