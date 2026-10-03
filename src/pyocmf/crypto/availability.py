"""Centralized cryptography package availability checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

# Type checkers see the real imports; the None fallback only applies at runtime
if TYPE_CHECKING:
    from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    CRYPTOGRAPHY_AVAILABLE = True
else:
    try:
        from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec

        CRYPTOGRAPHY_AVAILABLE = True
    except ImportError:
        CRYPTOGRAPHY_AVAILABLE = False
        InvalidSignature = None
        UnsupportedAlgorithm = None
        hashes = None
        serialization = None
        ec = None


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
    "InvalidSignature",
    "UnsupportedAlgorithm",
    "check_cryptography_available",
    "ec",
    "hashes",
    "serialization",
]
