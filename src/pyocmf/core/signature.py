import pydantic

from pyocmf.enums.crypto import (
    SignatureEncodingType,
    SignatureMethod,
    SignatureMimeType,
)
from pyocmf.exceptions import EncodingError
from pyocmf.types.encoding import validate_base64_string, validate_hex_string
from pyocmf.types.lenient import (
    LenientSignatureEncoding,
    LenientSignatureMethod,
    LenientSignatureMimeType,
    warn_spec,
)


class Signature(pydantic.BaseModel):
    # OCMF spec reserves extension points (keys starting with U-Z and A-F) in the
    # signature section; allow them so they survive parse/serialize roundtrips.
    model_config = pydantic.ConfigDict(extra="allow")

    SA: LenientSignatureMethod | None = pydantic.Field(
        default=SignatureMethod.SECP256R1_SHA256, description="Signature Algorithm"
    )
    SE: LenientSignatureEncoding | None = pydantic.Field(
        default=SignatureEncodingType.HEX, description="Signature Encoding"
    )
    SM: LenientSignatureMimeType | None = pydantic.Field(
        default=SignatureMimeType.APPLICATION_X_DER, description="Signature Mime Type"
    )
    SD: str = pydantic.Field(description="Signature Data (hex or base64)")

    @pydantic.field_validator("SD")
    @classmethod
    def warn_on_undecodable_signature_data(cls, v: str) -> str:
        for validate in (validate_hex_string, validate_base64_string):
            try:
                validate(v)
            except EncodingError:
                continue
            return v
        warn_spec("Signature Data (SD) is neither hex nor base64 encoded")
        return v
