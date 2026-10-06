"""Signature verification for curves the cryptography package does not support.

OpenSSL, which cryptography builds on, lacks secp192k1. The OCMF spec lists it and the
Transparenzsoftware verifies it, so pyocmf falls back to the pure-Python ecdsa package.
"""

from __future__ import annotations

import functools
import hashlib
from typing import TYPE_CHECKING

from pyocmf.enums.crypto import CurveType, HashAlgorithm
from pyocmf.exceptions import PublicKeyError

if TYPE_CHECKING:
    from ecdsa import BadSignatureError, VerifyingKey, der
    from ecdsa.curves import Curve
    from ecdsa.ellipticcurve import CurveFp, PointJacobi
    from ecdsa.util import sigdecode_der

    ECDSA_AVAILABLE = True
else:
    try:
        from ecdsa import BadSignatureError, VerifyingKey, der
        from ecdsa.curves import Curve
        from ecdsa.ellipticcurve import CurveFp, PointJacobi
        from ecdsa.util import sigdecode_der

        ECDSA_AVAILABLE = True
    except ImportError:
        ECDSA_AVAILABLE = False

_SECP192K1_OID = (1, 3, 132, 0, 31)
FALLBACK_CURVES = {CurveType.SECP192K1}

_HASHES = {HashAlgorithm.SHA256: hashlib.sha256, HashAlgorithm.SHA512: hashlib.sha512}


@functools.cache
def _secp192k1() -> Curve:
    # Domain parameters from SEC 2 (version 2.0), section 2.2.1
    p = 0xFFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFE_FFFFEE37
    n = 0xFFFFFFFF_FFFFFFFF_FFFFFFFE_26F2FC17_0F69466A_74DEFD8D
    gx = 0xDB4FF10E_C057E9AE_26B07D02_80B7F434_1DA5D1B1_EAE06C7D
    gy = 0x9B2F2F6D_9C5628A7_844163D0_15BE8634_4082AA88_D95E2F9D
    curve = CurveFp(p, 0, 3, 1)
    generator = PointJacobi(curve, gx, gy, 1, n, generator=True)
    return Curve("SECP192k1", curve, generator, _SECP192K1_OID)


def _check_ecdsa_available() -> None:
    if not ECDSA_AVAILABLE:
        msg = (
            "secp192k1 keys require the 'ecdsa' package. "
            "Install it with: pip install pyocmf[crypto]"
        )
        raise ImportError(msg)


def _split_public_key(der_key: bytes) -> tuple[tuple[int, ...], bytes]:
    """Return the curve OID and the encoded point of a DER SubjectPublicKeyInfo."""
    spki, _ = der.remove_sequence(der_key)
    algorithm, rest = der.remove_sequence(spki)
    _, curve_parameters = der.remove_object(algorithm)
    curve_oid, _ = der.remove_object(curve_parameters)
    point, _ = der.remove_bitstring(rest, 0)
    return curve_oid, point


def fallback_curve(der_key: bytes) -> CurveType | None:
    """Curve of a DER public key that only this fallback can load, if any."""
    if not ECDSA_AVAILABLE:
        return None
    try:
        curve_oid, _ = _split_public_key(der_key)
    except der.UnexpectedDER:
        return None
    return CurveType.SECP192K1 if curve_oid == _SECP192K1_OID else None


def verify_signature(
    der_key: bytes, signature: bytes, payload: bytes, hash_algorithm: HashAlgorithm
) -> bool:
    """Verify a DER-encoded ECDSA signature with a key on a fallback curve."""
    _check_ecdsa_available()
    try:
        _, point = _split_public_key(der_key)
        key = VerifyingKey.from_string(point, curve=_secp192k1(), hashfunc=_HASHES[hash_algorithm])
    except (der.UnexpectedDER, ValueError) as e:
        msg = f"Failed to parse public key: {e}"
        raise PublicKeyError(msg) from e
    try:
        return key.verify(signature, payload, sigdecode=sigdecode_der)
    except BadSignatureError:
        # ecdsa reports malformed DER signatures this way too, as cryptography does
        return False
