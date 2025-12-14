"""OCMF signature section containing cryptographic signature data.

This module defines the Signature model which contains the cryptographic
signature information used to verify the authenticity of OCMF data.
"""

import pydantic

from pyocmf.exceptions import SignatureVerificationError
from pyocmf.types.crypto import (
    KeyType,
    SignatureEncodingType,
    SignatureMethod,
    SignatureMimeType,
)
from pyocmf.types.identifiers import Base64Str, HexStr

SignatureDataType = HexStr | Base64Str


class Signature(pydantic.BaseModel):
    """Cryptographic signature data for OCMF payload verification.

    Contains the signature algorithm, encoding, data, and optional public key
    information for verifying the authenticity of the OCMF payload.
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
    PK: str | None = pydantic.Field(
        default=None, description="Public Key for verification with type designation"
    )
    KT: KeyType | None = pydantic.Field(
        default=None, description="Key Type - Elliptic curve identification"
    )

    def verify(self, payload_json: str, public_key_hex: str | None = None) -> bool:
        """Verify the signature against the payload using the provided public key.

        Args:
            payload_json: The JSON string of the OCMF payload to verify
            public_key_hex: Hex-encoded public key. If None, uses self.PK

        Returns:
            bool: True if signature is valid, False otherwise

        Raises:
            SignatureVerificationError: If verification cannot be performed due to
                missing data, unsupported algorithms, or malformed keys/signatures
            ImportError: If cryptography package is not installed
        """
        from pyocmf import verification

        key_to_use = public_key_hex or self.PK
        if key_to_use is None:
            msg = "Public key is required for signature verification"
            raise SignatureVerificationError(msg)

        return verification.verify_signature(
            payload_json=payload_json,
            signature_data=self.SD,
            signature_method=self.SA,
            signature_encoding=self.SE,
            public_key_hex=key_to_use,
        )
