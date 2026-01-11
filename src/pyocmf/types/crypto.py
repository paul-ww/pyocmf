import enum
from typing import Self


class HashAlgorithm(enum.StrEnum):
    SHA256 = "SHA256"
    SHA512 = "SHA512"


class CurveType(enum.StrEnum):
    SECP192K1 = "secp192k1"
    SECP256K1 = "secp256k1"
    SECP192R1 = "secp192r1"
    SECP256R1 = "secp256r1"
    SECP384R1 = "secp384r1"
    SECP521R1 = "secp521r1"
    BRAINPOOL256R1 = "brainpool256r1"
    BRAINPOOLP256R1 = "brainpoolP256r1"
    BRAINPOOL384R1 = "brainpool384r1"


class KeyType(enum.StrEnum):
    SECP192K1 = "ECDSA-secp192k1"
    SECP256K1 = "ECDSA-secp256k1"
    SECP192R1 = "ECDSA-secp192r1"
    SECP256R1 = "ECDSA-secp256r1"
    SECP384R1 = "ECDSA-secp384r1"
    SECP521R1 = "ECDSA-secp521r1"
    BRAINPOOL256R1 = "ECDSA-brainpool256r1"
    BRAINPOOLP256R1 = "ECDSA-brainpoolP256r1"
    BRAINPOOL384R1 = "ECDSA-brainpool384r1"

    @classmethod
    def from_curve(cls, curve: CurveType) -> Self:
        return cls(f"ECDSA-{curve.value}")

    @property
    def curve(self) -> CurveType:
        return CurveType(self.value.split("-")[1])


class SignatureMethod(enum.StrEnum):
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

    @classmethod
    def from_parts(cls, curve: CurveType, hash_algorithm: HashAlgorithm) -> Self:
        return cls(f"ECDSA-{curve.value}-{hash_algorithm.value}")

    @property
    def curve(self) -> CurveType:
        return CurveType(self.value.split("-")[1])

    @property
    def hash_algorithm(self) -> HashAlgorithm:
        return HashAlgorithm(self.value.split("-")[2])


class SignatureEncodingType(enum.StrEnum):
    HEX = "hex"
    BASE64 = "base64"


class SignatureMimeType(enum.StrEnum):
    APPLICATION_X_DER = "application/x-der"
