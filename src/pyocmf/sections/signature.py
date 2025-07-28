import pydantic
from typing import Literal
from pyocmf.custom_types.hex_string import HexStr
from enum import Enum


class SignatureMethod(str, Enum):
    secp192k1 = "ECDSA-secp192k1-SHA256"
    secp256k1 = "ECDSA-secp256k1-SHA256"
    secp192r1 = "ECDSA-secp192r1-SHA256"
    secp256r1 = "ECDSA-secp256r1-SHA256"
    brainpool256r1 = "ECDSA-brainpool256r1-SHA256"
    secp384r1 = "ECDSA-secp384r1-SHA256"
    brainpool384r1 = "ECDSA-brainpool384r1-SHA256"


SignatureEncodingType = Literal["hex", "base64"]

SignatureMimeType = Literal["application/x-der"]

SignatureDataType = pydantic.Base64Str | type[HexStr]


class Signature(pydantic.BaseModel):
    SA: SignatureMethod | None = pydantic.Field(
        SignatureMethod.secp256r1, description="Signature Algorithm"
    )
    SE: SignatureEncodingType | None = pydantic.Field(
        default="hex", description="Signature Encoding"
    )
    SM: SignatureMimeType | None = pydantic.Field(
        default="application/x-der", description="Signature Mime Type"
    )
    SD: HexStr = pydantic.Field(..., description="Signature Data (hex string)")
