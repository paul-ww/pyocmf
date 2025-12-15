"""Public key types and metadata for OCMF signature verification."""

from __future__ import annotations

import base64
import enum
from typing import TYPE_CHECKING, Self

import pydantic

from pyocmf.exceptions import Base64DecodingError, PublicKeyError
from pyocmf.types.encoding import HexStr

if TYPE_CHECKING:
    from pyocmf.types.crypto import SignatureMethod


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

    key_hex: HexStr = pydantic.Field(description="Hex-encoded DER public key")
    curve: CurveType = pydantic.Field(description="Elliptic curve type")
    key_size: int = pydantic.Field(description="Key size in bits")
    block_length: int = pydantic.Field(description="Block length in bytes")

    def to_string(self, *, base64: bool = False) -> str:
        """Convert the public key to a string representation.

        Args:
            base64: If True, return base64-encoded string. Defaults to False (hex).

        Returns:
            str: The public key as hex or base64 string.
        """
        if base64:
            import base64 as b64

            key_bytes = bytes.fromhex(self.key_hex)
            return b64.b64encode(key_bytes).decode("ascii")
        return self.key_hex

    @classmethod
    def from_string(cls, key_string: str) -> Self:
        """Create PublicKey by parsing a DER public key string.

        Automatically detects whether the input is hex-encoded or base64-encoded.

        Args:
            key_string: Hex-encoded or base64-encoded DER public key

        Returns:
            PublicKey with extracted metadata

        Raises:
            HexDecodingError: If the string appears to be hex but cannot be decoded
            Base64DecodingError: If the string appears to be base64 but cannot be decoded
            PublicKeyError: If the key cannot be parsed or is not an EC key
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

        key_string = key_string.strip()

        # Try hex first (DER-encoded keys typically start with 30 in hex)
        key_bytes: bytes | None = None
        key_hex: str

        try:
            key_bytes = bytes.fromhex(key_string)
            key_hex = key_string
        except ValueError:
            # Not valid hex, try base64
            try:
                key_bytes = base64.b64decode(key_string, validate=True)
                key_hex = key_bytes.hex()
            except Exception as e:
                msg = f"Invalid public key encoding: not valid hex or base64. {e}"
                raise Base64DecodingError(msg) from e

        try:
            public_key = serialization.load_der_public_key(key_bytes)

            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                msg = "Public key is not an elliptic curve key"
                raise TypeError(msg)  # noqa: TRY301

            curve_name = public_key.curve.name
            key_size = public_key.curve.key_size
            block_length = key_size // 8

            return cls(
                key_hex=key_hex,
                curve=curve_name,
                key_size=key_size,
                block_length=block_length,
            )
        except (ValueError, TypeError) as e:
            msg = f"Failed to parse public key: {e}"
            raise PublicKeyError(msg) from e

    @property
    def key_type_identifier(self) -> str:
        """Get the OCMF key type identifier (e.g., 'ECDSA-secp256r1')."""
        return f"ECDSA-{self.curve}"

    def matches_signature_algorithm(
        self, signature_algorithm: SignatureMethod | str | None
    ) -> bool:
        """Check if this key's curve matches the given signature algorithm.

        Args:
            signature_algorithm: OCMF signature algorithm (e.g., 'ECDSA-secp256r1-SHA256')

        Returns:
            True if the curves match, False otherwise
        """
        if signature_algorithm is None:
            return False

        algo_str = str(signature_algorithm).lower()
        return self.curve.value in algo_str
