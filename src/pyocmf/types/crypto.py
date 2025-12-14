"""Cryptography-related types for OCMF signatures."""

import enum


class HashAlgorithm(enum.StrEnum):
    """Hash algorithms supported by OCMF."""

    SHA256 = "SHA256"
    SHA512 = "SHA512"


class SignatureMethod(enum.StrEnum):
    """ECDSA signature algorithms supported by OCMF.

    Combines elliptic curve types with hash functions (SHA256 or SHA512).
    """

    SECP192K1_SHA256 = "ECDSA-secp192k1-SHA256"
    SECP256K1_SHA256 = "ECDSA-secp256k1-SHA256"
    SECP192R1_SHA256 = "ECDSA-secp192r1-SHA256"
    SECP256R1_SHA256 = "ECDSA-secp256r1-SHA256"
    BRAINPOOL256R1_SHA256 = "ECDSA-brainpool256r1-SHA256"
    BRAINPOOLP256R1_SHA256 = "ECDSA-brainpoolP256r1-SHA256"
    SECP384R1_SHA256 = "ECDSA-secp384r1-SHA256"
    BRAINPOOL384R1_SHA256 = "ECDSA-brainpool384r1-SHA256"
    SECP521R1_SHA256 = "ECDSA-secp521r1-SHA256"
    SECP192K1_SHA512 = "ECDSA-secp192k1-SHA512"
    SECP256K1_SHA512 = "ECDSA-secp256k1-SHA512"
    SECP192R1_SHA512 = "ECDSA-secp192r1-SHA512"
    SECP256R1_SHA512 = "ECDSA-secp256r1-SHA512"
    BRAINPOOL256R1_SHA512 = "ECDSA-brainpool256r1-SHA512"
    BRAINPOOLP256R1_SHA512 = "ECDSA-brainpoolP256r1-SHA512"
    SECP384R1_SHA512 = "ECDSA-secp384r1-SHA512"
    BRAINPOOL384R1_SHA512 = "ECDSA-brainpool384r1-SHA512"
    SECP521R1_SHA512 = "ECDSA-secp521r1-SHA512"


class SignatureEncodingType(enum.StrEnum):
    """Encoding format for signature data."""

    HEX = "hex"
    BASE64 = "base64"


class SignatureMimeType(enum.StrEnum):
    """MIME type for signature data format."""

    APPLICATION_X_DER = "application/x-der"
