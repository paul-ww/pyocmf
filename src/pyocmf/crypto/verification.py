from __future__ import annotations

import base64

from pyocmf.crypto.availability import (
    InvalidSignature,
    check_cryptography_available,
    ec,
    hashes,
    serialization,
)
from pyocmf.enums.crypto import HashAlgorithm, SignatureEncodingType, SignatureMethod
from pyocmf.exceptions import EncodingError, PublicKeyError, SignatureVerificationError


def get_hash_algorithm(signature_method: SignatureMethod | None) -> type[hashes.HashAlgorithm]:
    check_cryptography_available()

    if signature_method is None:
        msg = "Signature algorithm (SA) is required for verification"
        raise SignatureVerificationError(msg)

    hash_mapping: dict[HashAlgorithm, type[hashes.HashAlgorithm]] = {
        HashAlgorithm.SHA256: hashes.SHA256,
        HashAlgorithm.SHA512: hashes.SHA512,
    }

    hash_class = hash_mapping.get(signature_method.hash_algorithm)
    if hash_class is None:
        msg = f"Unsupported hash algorithm in signature method: {signature_method}"
        raise SignatureVerificationError(msg)

    return hash_class


def decode_signature_data(signature_data: str, encoding: SignatureEncodingType | None) -> bytes:
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


def verify_signature(
    payload_json: str,
    signature_data: str,
    signature_method: SignatureMethod | None,
    signature_encoding: SignatureEncodingType | None,
    public_key_hex: str,
) -> bool:
    """Verify ECDSA signature against payload using the provided public key.

    Requires the 'cryptography' package (install with: pip install pyocmf[crypto]).

    Raises SignatureVerificationError if the public key curve doesn't match the
    signature algorithm or if verification cannot be performed.
    """
    check_cryptography_available()

    from pyocmf.models.public_key import PublicKey

    try:
        public_key_info = PublicKey.from_string(public_key_hex)
    except (PublicKeyError, EncodingError, ImportError) as e:
        msg = f"Failed to parse public key: {e}"
        raise SignatureVerificationError(msg) from e

    if not public_key_info.matches_signature_algorithm(signature_method):
        msg = (
            f"Public key curve mismatch: signature algorithm specifies "
            f"'{signature_method}' but public key uses '{public_key_info.curve}'"
        )
        raise SignatureVerificationError(msg)

    signature_bytes = decode_signature_data(signature_data, signature_encoding)
    hash_algorithm = get_hash_algorithm(signature_method)
    payload_bytes = payload_json.encode("utf-8")

    key_bytes = bytes.fromhex(public_key_hex)
    crypto_public_key = serialization.load_der_public_key(key_bytes)

    try:
        crypto_public_key.verify(
            signature_bytes,
            payload_bytes,
            ec.ECDSA(hash_algorithm()),
        )
    except InvalidSignature:
        return False
    except (TypeError, ValueError) as e:
        msg = f"Signature verification failed: {e}"
        raise SignatureVerificationError(msg, reason="invalid_signature_format") from e
    else:
        return True
