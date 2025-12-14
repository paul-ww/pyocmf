"""Cryptographic signature verification for OCMF data.

This module requires the 'cryptography' package to be installed.
Install with: pip install pyocmf[crypto]
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyocmf.types.crypto import SignatureEncodingType

from pyocmf.types.crypto import HashAlgorithm, SignatureMethod
from pyocmf.types.public_key import CurveType

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


from pyocmf.exceptions import SignatureVerificationError


def check_cryptography_available() -> None:
    """Check if cryptography library is available.

    Raises:
        ImportError: If cryptography is not installed
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        msg = (
            "Signature verification requires the 'cryptography' package. "
            "Install it with: pip install pyocmf[crypto]"
        )
        raise ImportError(msg)


def get_hash_algorithm(signature_method: SignatureMethod | None) -> type[hashes.HashAlgorithm]:
    """Get the hash algorithm from the signature method.

    Args:
        signature_method: The ECDSA signature method

    Returns:
        The hash algorithm class

    Raises:
        SignatureVerificationError: If algorithm is missing or unsupported
    """
    check_cryptography_available()

    if signature_method is None:
        msg = "Signature algorithm (SA) is required for verification"
        raise SignatureVerificationError(msg)

    hash_mapping: dict[HashAlgorithm, type[hashes.HashAlgorithm]] = {
        HashAlgorithm.SHA256: hashes.SHA256,
        HashAlgorithm.SHA512: hashes.SHA512,
    }

    for hash_algo, hash_class in hash_mapping.items():
        if hash_algo.value in signature_method:
            return hash_class

    msg = f"Unsupported hash algorithm in signature method: {signature_method}"
    raise SignatureVerificationError(msg)


def get_elliptic_curve(signature_method: SignatureMethod | None) -> ec.EllipticCurve:
    """Get the elliptic curve from the signature method.

    Args:
        signature_method: The ECDSA signature method

    Returns:
        The elliptic curve instance

    Raises:
        SignatureVerificationError: If algorithm is missing or unsupported
    """
    check_cryptography_available()

    if signature_method is None:
        msg = "Signature algorithm (SA) is required for verification"
        raise SignatureVerificationError(msg)

    curve_mapping: dict[CurveType, type[ec.EllipticCurve]] = {
        CurveType.SECP192K1: ec.SECP192R1,
        CurveType.SECP256K1: ec.SECP256K1,
        CurveType.SECP192R1: ec.SECP192R1,
        CurveType.SECP256R1: ec.SECP256R1,
        CurveType.SECP384R1: ec.SECP384R1,
        CurveType.SECP521R1: ec.SECP521R1,
        CurveType.BRAINPOOL256R1: ec.BrainpoolP256R1,
        CurveType.BRAINPOOLP256R1: ec.BrainpoolP256R1,
        CurveType.BRAINPOOL384R1: ec.BrainpoolP384R1,
    }

    for curve_type, curve_class in curve_mapping.items():
        if curve_type.value in signature_method.lower():
            return curve_class()

    msg = f"Unsupported elliptic curve in signature method: {signature_method}"
    raise SignatureVerificationError(msg)


def decode_signature_data(signature_data: str, encoding: SignatureEncodingType | None) -> bytes:
    """Decode the signature data based on its encoding type.

    Args:
        signature_data: The encoded signature data
        encoding: The encoding type (hex or base64)

    Returns:
        The decoded signature bytes

    Raises:
        SignatureVerificationError: If decoding fails
    """
    from pyocmf.types.crypto import SignatureEncodingType

    if encoding == SignatureEncodingType.HEX or encoding is None:
        try:
            return bytes.fromhex(signature_data)
        except ValueError as e:
            msg = f"Failed to decode hex signature data: {e}"
            raise SignatureVerificationError(msg) from e
    elif encoding == SignatureEncodingType.BASE64:
        try:
            return base64.b64decode(signature_data)
        except Exception as e:
            msg = f"Failed to decode base64 signature data: {e}"
            raise SignatureVerificationError(msg) from e
    else:
        msg = f"Unsupported signature encoding: {encoding}"
        raise SignatureVerificationError(msg)


def decode_public_key(public_key_hex: str) -> ec.EllipticCurvePublicKey:
    """Decode a hex-encoded public key into an EllipticCurvePublicKey object.

    Args:
        public_key_hex: Hex-encoded DER public key

    Returns:
        The elliptic curve public key

    Raises:
        SignatureVerificationError: If decoding fails or key is invalid
    """
    check_cryptography_available()

    try:
        key_bytes = bytes.fromhex(public_key_hex)
        public_key = serialization.load_der_public_key(key_bytes)

        if not isinstance(public_key, ec.EllipticCurvePublicKey):
            msg = "Public key is not an elliptic curve key"
            raise SignatureVerificationError(msg)
    except ValueError as e:
        msg = f"Failed to decode public key: {e}"
        raise SignatureVerificationError(msg) from e
    else:
        return public_key


def validate_key_matches_algorithm(
    public_key: ec.EllipticCurvePublicKey,
    signature_method: SignatureMethod | None,
) -> None:
    """Validate that the public key curve matches the signature algorithm.

    Args:
        public_key: The elliptic curve public key
        signature_method: The ECDSA signature method from OCMF data

    Raises:
        SignatureVerificationError: If the key curve doesn't match the algorithm
    """
    if signature_method is None:
        return

    expected_curve = get_elliptic_curve(signature_method)
    actual_curve_name = public_key.curve.name

    if actual_curve_name != expected_curve.name:
        msg = (
            f"Public key curve mismatch: signature algorithm specifies "
            f"'{expected_curve.name}' but public key uses '{actual_curve_name}'"
        )
        raise SignatureVerificationError(msg)


def verify_signature(
    payload_json: str,
    signature_data: str,
    signature_method: SignatureMethod | None,
    signature_encoding: SignatureEncodingType | None,
    public_key_hex: str,
) -> bool:
    """Verify an ECDSA signature against payload data.

    Args:
        payload_json: The JSON string of the payload to verify
        signature_data: The signature data (hex or base64 encoded)
        signature_method: The ECDSA signature algorithm
        signature_encoding: The encoding of the signature data
        public_key_hex: Hex-encoded DER public key

    Returns:
        True if signature is valid, False otherwise

    Raises:
        SignatureVerificationError: If verification cannot be performed or if
            the public key curve doesn't match the signature algorithm
        ImportError: If cryptography package is not installed
    """
    check_cryptography_available()

    public_key = decode_public_key(public_key_hex)
    validate_key_matches_algorithm(public_key, signature_method)
    signature_bytes = decode_signature_data(signature_data, signature_encoding)
    hash_algorithm = get_hash_algorithm(signature_method)

    payload_bytes = payload_json.encode("utf-8")

    try:
        public_key.verify(
            signature_bytes,
            payload_bytes,
            ec.ECDSA(hash_algorithm()),
        )
    except InvalidSignature:
        return False
    except Exception as e:
        msg = f"Signature verification failed: {e}"
        raise SignatureVerificationError(msg) from e
    else:
        return True
