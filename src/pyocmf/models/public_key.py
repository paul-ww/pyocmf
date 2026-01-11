from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Self

import pydantic

from pyocmf.enums.crypto import CurveType, KeyType
from pyocmf.exceptions import Base64DecodingError, PublicKeyError
from pyocmf.types.encoding import HexStr

try:
    from cryptography.exceptions import UnsupportedAlgorithm
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
except ImportError:
    serialization = None  # type: ignore[assignment]
    ec = None  # type: ignore[assignment]
    UnsupportedAlgorithm = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from pyocmf.enums.crypto import SignatureMethod


def _try_parse_raw_p256_coordinates(key_bytes: bytes) -> tuple[str, str, int, int] | None:
    if ec is None or serialization is None:
        return None

    if len(key_bytes) != 64:
        return None

    try:
        # Raw coordinates: X (32 bytes) || Y (32 bytes)
        # Construct uncompressed point format: 04 || X || Y
        point_bytes = b"\x04" + key_bytes
        public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), point_bytes)

        curve_name = public_key.curve.name
        key_size = public_key.curve.key_size
        block_length = key_size // 8

        # Store as DER-encoded for consistency
        der_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        der_hex = der_bytes.hex()

        return (der_hex, curve_name, key_size, block_length)
    except Exception:
        return None


class PublicKey(pydantic.BaseModel):
    key: HexStr = pydantic.Field(description="Hex-encoded DER public key")
    curve: CurveType = pydantic.Field(description="Elliptic curve type")
    size: int = pydantic.Field(description="Key size in bits")
    block_length: int = pydantic.Field(description="Block length in bytes")

    def to_string(self, base64_encode: bool = False) -> str:
        if base64_encode:
            key_bytes = bytes.fromhex(self.key)
            return base64.b64encode(key_bytes).decode("ascii")
        return self.key

    @classmethod
    def from_string(cls, key_string: str) -> Self:
        """Parse DER public key string (hex or base64) and extract metadata."""
        if serialization is None or ec is None:
            msg = (
                "Public key parsing requires the 'cryptography' package. "
                "Install it with: pip install pyocmf[crypto]"
            )
            raise ImportError(msg)

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
                key=key_hex,
                curve=curve_name,
                size=key_size,
                block_length=block_length,
            )
        except (ValueError, TypeError) as e:
            result = _try_parse_raw_p256_coordinates(key_bytes)
            if result is not None:
                key_hex, curve_name, key_size, block_length = result
                return cls(
                    key=key_hex,
                    curve=curve_name,
                    size=key_size,
                    block_length=block_length,
                )

            msg = f"Failed to parse public key: {e}"
            raise PublicKeyError(msg) from e
        except Exception as e:
            if UnsupportedAlgorithm is not None and type(e).__name__ == "UnsupportedAlgorithm":
                msg = f"Unsupported elliptic curve in public key: {e}"
                raise PublicKeyError(msg) from e
            raise

    @property
    def key_type_identifier(self) -> KeyType:
        return KeyType.from_curve(self.curve)

    def matches_signature_algorithm(self, signature_algorithm: SignatureMethod | None) -> bool:
        if signature_algorithm is None:
            return False

        return self.curve == signature_algorithm.curve
