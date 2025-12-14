"""OCMF signature section containing cryptographic signature data.

This module defines the Signature model which contains the cryptographic
signature information used to verify the authenticity of OCMF data.
"""

import base64

import pydantic
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

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

    def _get_hash_algorithm(self) -> type[hashes.HashAlgorithm]:
        """Get the hash algorithm from the signature method."""
        if self.SA is None:
            msg = "Signature algorithm (SA) is required for verification"
            raise SignatureVerificationError(msg)

        if "SHA256" in self.SA:
            return hashes.SHA256
        if "SHA512" in self.SA:
            return hashes.SHA512

        msg = f"Unsupported hash algorithm in signature method: {self.SA}"
        raise SignatureVerificationError(msg)

    def _get_elliptic_curve(self) -> ec.EllipticCurve:
        """Get the elliptic curve from the signature method."""
        if self.SA is None:
            msg = "Signature algorithm (SA) is required for verification"
            raise SignatureVerificationError(msg)

        curve_mapping = {
            "secp192k1": ec.SECP192R1,
            "secp256k1": ec.SECP256K1,
            "secp192r1": ec.SECP192R1,
            "secp256r1": ec.SECP256R1,
            "secp384r1": ec.SECP384R1,
            "secp521r1": ec.SECP521R1,
            "brainpool256r1": ec.BrainpoolP256R1,
            "brainpoolp256r1": ec.BrainpoolP256R1,
            "brainpool384r1": ec.BrainpoolP384R1,
        }

        for curve_name, curve_class in curve_mapping.items():
            if curve_name in self.SA.lower():
                return curve_class()

        msg = f"Unsupported elliptic curve in signature method: {self.SA}"
        raise SignatureVerificationError(msg)

    def _decode_signature_data(self) -> bytes:
        """Decode the signature data based on its encoding type."""
        if self.SE == SignatureEncodingType.HEX or self.SE is None:
            try:
                return bytes.fromhex(self.SD)
            except ValueError as e:
                msg = f"Failed to decode hex signature data: {e}"
                raise SignatureVerificationError(msg) from e
        elif self.SE == SignatureEncodingType.BASE64:
            try:
                return base64.b64decode(self.SD)
            except Exception as e:
                msg = f"Failed to decode base64 signature data: {e}"
                raise SignatureVerificationError(msg) from e
        else:
            msg = f"Unsupported signature encoding: {self.SE}"
            raise SignatureVerificationError(msg)

    def _decode_public_key(self, public_key_hex: str) -> ec.EllipticCurvePublicKey:
        """Decode a hex-encoded public key into an EllipticCurvePublicKey object."""
        try:
            key_bytes = bytes.fromhex(public_key_hex)
            public_key = serialization.load_der_public_key(key_bytes)

            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                msg = "Public key is not an elliptic curve key"
                raise SignatureVerificationError(msg)

            return public_key
        except ValueError as e:
            msg = f"Failed to decode public key: {e}"
            raise SignatureVerificationError(msg) from e

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
        """
        key_to_use = public_key_hex or self.PK
        if key_to_use is None:
            msg = "Public key is required for signature verification"
            raise SignatureVerificationError(msg)

        public_key = self._decode_public_key(key_to_use)
        signature_bytes = self._decode_signature_data()
        hash_algorithm = self._get_hash_algorithm()

        payload_bytes = payload_json.encode("utf-8")

        try:
            public_key.verify(
                signature_bytes,
                payload_bytes,
                ec.ECDSA(hash_algorithm()),
            )
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            msg = f"Signature verification failed: {e}"
            raise SignatureVerificationError(msg) from e
