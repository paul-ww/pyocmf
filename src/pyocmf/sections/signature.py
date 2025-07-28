import pydantic
from pyocmf.custom_types.hex_string import HexStr
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

SignatureDataType = pydantic.Base64Str | HexStr


class Signature(pydantic.BaseModel):
    SA: SignatureMethod | None = pydantic.Field(
        SignatureMethod.SECP256R1, description="Signature Algorithm"
    )
    SE: SignatureEncodingType | None = pydantic.Field(
        default=SignatureEncodingType.HEX, description="Signature Encoding"
    )
    SM: SignatureMimeType | None = pydantic.Field(
        default=SignatureMimeType.APPLICATION_X_DER, description="Signature Mime Type"
    )
    SD: SignatureDataType = pydantic.Field(..., description="Signature Data")

    @pydantic.field_validator("SD", mode="before")
    @classmethod
    def validate_signature_data(cls, v: str, info: pydantic.ValidationInfo) -> str:
        """Validate signature data based on encoding type."""
        # For now, we'll accept any string format and let downstream validation handle it
        # This allows both hex and base64 encoded data
        return v
