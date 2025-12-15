"""OCMF signature section containing cryptographic signature data.

This module defines the Signature model which contains the cryptographic
signature information used to verify the authenticity of OCMF data.
"""

import pydantic

from pyocmf.types.crypto import (
    SignatureEncodingType,
    SignatureMethod,
    SignatureMimeType,
)
from pyocmf.types.encoding import Base64Str, HexStr

SignatureDataType = HexStr | Base64Str


class Signature(pydantic.BaseModel):
    """Cryptographic signature data for OCMF payload verification.

    Contains the signature algorithm, encoding, and data for verifying
    the authenticity of the OCMF payload. Per OCMF specification, the
    public key must be transmitted out-of-band (separately from the OCMF data).
    """

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
