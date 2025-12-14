"""Public key types and metadata for OCMF signature verification."""

from __future__ import annotations

import enum

import pydantic


class CurveType(enum.StrEnum):
    """Elliptic curve types supported by OCMF."""

    SECP192K1 = "secp192k1"
    SECP256K1 = "secp256k1"
    SECP192R1 = "secp192r1"
    SECP256R1 = "secp256r1"
    SECP384R1 = "secp384r1"
    SECP521R1 = "secp521r1"
    BRAINPOOL256R1 = "brainpool256r1"
    BRAINPOOLP256R1 = "brainpoolP256r1"
    BRAINPOOL384R1 = "brainpool384r1"


class PublicKey(pydantic.BaseModel):
    """Public key information with metadata per OCMF spec Table 23.

    This model represents public key metadata as defined in the OCMF specification.
    The key type, length, and block length are extracted from the actual key data.
    """

    key_hex: str = pydantic.Field(description="Hex-encoded DER public key")
    curve: CurveType = pydantic.Field(description="Elliptic curve type")
    key_size: int = pydantic.Field(description="Key size in bits")
    block_length: int = pydantic.Field(description="Block length in bytes")

    @classmethod
    def from_hex(cls, key_hex: str) -> PublicKey:
        """Create PublicKeyInfo by parsing a hex-encoded DER public key.

        Args:
            key_hex: Hex-encoded DER public key

        Returns:
            PublicKeyInfo with extracted metadata

        Raises:
            ValueError: If the key cannot be parsed or is not an EC key
        """
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import ec
        except ImportError as e:
            msg = (
                "Public key parsing requires the 'cryptography' package. "
                "Install it with: pip install pyocmf[crypto]"
            )
            raise ImportError(msg) from e

        try:
            key_bytes = bytes.fromhex(key_hex)
            public_key = serialization.load_der_public_key(key_bytes)

            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                msg = "Public key is not an elliptic curve key"
                raise TypeError(msg)  # noqa: TRY301

            curve_name = public_key.curve.name
            key_size = public_key.curve.key_size
            block_length = key_size // 8

            return cls(
                key_hex=key_hex,
                curve=curve_name,  # type: ignore[arg-type]
                key_size=key_size,
                block_length=block_length,
            )
        except (ValueError, TypeError) as e:
            msg = f"Failed to parse public key: {e}"
            raise ValueError(msg) from e

    @property
    def key_type_identifier(self) -> str:
        """Get the OCMF key type identifier (e.g., 'ECDSA-secp256r1')."""
        return f"ECDSA-{self.curve}"

    def matches_signature_algorithm(self, signature_algorithm: str | None) -> bool:
        """Check if this key's curve matches the given signature algorithm.

        Args:
            signature_algorithm: OCMF signature algorithm (e.g., 'ECDSA-secp256r1-SHA256')

        Returns:
            True if the curves match, False otherwise
        """
        if signature_algorithm is None:
            return False

        return self.curve in signature_algorithm.lower()
