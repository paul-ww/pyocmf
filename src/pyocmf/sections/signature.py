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
from pyocmf.types.identifiers import Base64Str, HexStr

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

    def verify(self, payload_json: str, public_key_hex: str) -> bool:
        """Verify the signature against the payload using the provided public key.

        Args:
            payload_json: The JSON string of the OCMF payload to verify
            public_key_hex: Hex-encoded public key (required per OCMF spec)

        Returns:
            bool: True if signature is valid, False otherwise

        Raises:
            SignatureVerificationError: If verification cannot be performed due to
                missing data, unsupported algorithms, or malformed keys/signatures
            ImportError: If cryptography package is not installed
        """
        from pyocmf import verification

        return verification.verify_signature(
            payload_json=payload_json,
            signature_data=self.SD,
            signature_method=self.SA,
            signature_encoding=self.SE,
            public_key_hex=public_key_hex,
        )
