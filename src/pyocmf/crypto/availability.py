"""Centralized cryptography package availability checks."""

from __future__ import annotations

try:
    from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    InvalidSignature = None  # type: ignore[assignment,misc]
    UnsupportedAlgorithm = None  # type: ignore[assignment,misc]
    hashes = None  # type: ignore[assignment]
    serialization = None  # type: ignore[assignment]
    ec = None  # type: ignore[assignment]


def check_cryptography_available() -> None:
    """Raise ImportError if cryptography package is not installed."""
    if not CRYPTOGRAPHY_AVAILABLE:
        msg = (
            "Cryptographic operations require the 'cryptography' package. "
            "Install it with: pip install pyocmf[crypto]"
        )
        raise ImportError(msg)


__all__ = [
    "CRYPTOGRAPHY_AVAILABLE",
    "check_cryptography_available",
    "InvalidSignature",
    "UnsupportedAlgorithm",
    "hashes",
    "serialization",
    "ec",
]
