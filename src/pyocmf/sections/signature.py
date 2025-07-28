import pydantic
from pyocmf.custom_types.hex_string import HexStr
import enum


class SignatureMethod(enum.StrEnum):
    secp192k1 = "ECDSA-secp192k1-SHA256"
    secp256k1 = "ECDSA-secp256k1-SHA256"
    secp192r1 = "ECDSA-secp192r1-SHA256"
    secp256r1 = "ECDSA-secp256r1-SHA256"
    brainpool256r1 = "ECDSA-brainpool256r1-SHA256"
    secp384r1 = "ECDSA-secp384r1-SHA256"
    brainpool384r1 = "ECDSA-brainpool384r1-SHA256"


class SignatureEncodingType(enum.StrEnum):
    HEX = "hex"
    BASE64 = "base64"

class SignatureMimeType(enum.StrEnum):
    APPLICATION_X_DER = "application/x-der"

SignatureDataType = pydantic.Base64Str | HexStr


class Signature(pydantic.BaseModel):
    SA: SignatureMethod | None = pydantic.Field(
        SignatureMethod.secp256r1, description="Signature Algorithm"
    )
    SE: SignatureEncodingType | None = pydantic.Field(
        default=SignatureEncodingType.HEX, description="Signature Encoding"
    )
    SM: SignatureMimeType | None = pydantic.Field(
        default=SignatureMimeType.APPLICATION_X_DER, description="Signature Mime Type"
    )
    SD: HexStr = pydantic.Field(..., description="Signature Data (hex string)")
