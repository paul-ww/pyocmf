import pydantic
from pyocmf.custom_types.strings import HexStr, Base64Str
import enum


class SignatureMethod(enum.StrEnum):
    SECP192K1 = "ECDSA-secp192k1-SHA256"
    SECP256K1 = "ECDSA-secp256k1-SHA256"
    SECP192R1 = "ECDSA-secp192r1-SHA256"
    SECP256R1 = "ECDSA-secp256r1-SHA256"
    BRAINPOOL256R1 = "ECDSA-brainpool256r1-SHA256"
    BRAINPOOLP256R1 = "ECDSA-brainpoolP256r1-SHA256"
    SECP384R1 = "ECDSA-secp384r1-SHA256"
    BRAINPOOL384R1 = "ECDSA-brainpool384r1-SHA256"


class SignatureEncodingType(enum.StrEnum):
    HEX = "hex"
    BASE64 = "base64"


class SignatureMimeType(enum.StrEnum):
    APPLICATION_X_DER = "application/x-der"


SignatureDataType = HexStr | Base64Str


class Signature(pydantic.BaseModel):
    SA: SignatureMethod | None = pydantic.Field(
        default=SignatureMethod.SECP256R1, description="Signature Algorithm"
    )
    SE: SignatureEncodingType | None = pydantic.Field(
        default=SignatureEncodingType.HEX, description="Signature Encoding"
    )
    SM: SignatureMimeType | None = pydantic.Field(
        default=SignatureMimeType.APPLICATION_X_DER, description="Signature Mime Type"
    )
    SD: SignatureDataType = pydantic.Field(description="Signature Data")
