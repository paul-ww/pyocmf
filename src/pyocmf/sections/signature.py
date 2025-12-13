import pydantic

from pyocmf.types.crypto import (
    KeyType,
    SignatureEncodingType,
    SignatureMethod,
    SignatureMimeType,
)
from pyocmf.types.identifiers import Base64Str, HexStr

SignatureDataType = HexStr | Base64Str


class Signature(pydantic.BaseModel):
    SA: SignatureMethod | None = pydantic.Field(
        default=SignatureMethod.SECP256R1_SHA256, description="Signature Algorithm"
    )
    SE: SignatureEncodingType | None = pydantic.Field(
        default=SignatureEncodingType.HEX, description="Signature Encoding"
    )
    SM: SignatureMimeType | None = pydantic.Field(
        default=SignatureMimeType.APPLICATION_X_DER, description="Signature Mime Type"
    )
    SD: SignatureDataType = pydantic.Field(description="Signature Data")
    PK: str | None = pydantic.Field(
        default=None, description="Public Key for verification with type designation"
    )
    KT: KeyType | None = pydantic.Field(
        default=None, description="Key Type - Elliptic curve identification"
    )
