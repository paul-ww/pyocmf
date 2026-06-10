import pydantic

from pyocmf.enums.crypto import (
    SignatureEncodingType,
    SignatureMethod,
    SignatureMimeType,
)
from pyocmf.types.encoding import Base64Str, HexStr

SignatureDataType = HexStr | Base64Str


class Signature(pydantic.BaseModel):
    # OCMF spec reserves extension points (keys starting with U-Z and A-F) in the
    # signature section; allow them so they survive parse/serialize roundtrips.
    model_config = pydantic.ConfigDict(extra="allow")

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
