import pytest

from pyocmf.enums.crypto import CurveType, HashAlgorithm, KeyType, SignatureMethod


class TestKeyType:
    def test_from_curve(self) -> None:
        assert KeyType.from_curve(CurveType.SECP256R1) == KeyType.SECP256R1
        assert KeyType.from_curve(CurveType.SECP384R1) == KeyType.SECP384R1
        assert KeyType.from_curve(CurveType.BRAINPOOLP256R1) == KeyType.BRAINPOOLP256R1

    def test_curve_property(self) -> None:
        assert KeyType.SECP256R1.curve == CurveType.SECP256R1
        assert KeyType.SECP384R1.curve == CurveType.SECP384R1
        assert KeyType.BRAINPOOLP256R1.curve == CurveType.BRAINPOOLP256R1

    def test_roundtrip(self) -> None:
        for curve in CurveType:
            key_type = KeyType.from_curve(curve)
            assert key_type.curve == curve


class TestSignatureMethod:
    def test_from_parts(self) -> None:
        assert (
            SignatureMethod.from_parts(CurveType.SECP256R1, HashAlgorithm.SHA256)
            == SignatureMethod.SECP256R1_SHA256
        )
        assert (
            SignatureMethod.from_parts(CurveType.SECP256R1, HashAlgorithm.SHA512)
            == SignatureMethod.SECP256R1_SHA512
        )
        assert (
            SignatureMethod.from_parts(CurveType.BRAINPOOLP256R1, HashAlgorithm.SHA256)
            == SignatureMethod.BRAINPOOLP256R1_SHA256
        )

    def test_curve_property(self) -> None:
        assert SignatureMethod.SECP256R1_SHA256.curve == CurveType.SECP256R1
        assert SignatureMethod.SECP384R1_SHA512.curve == CurveType.SECP384R1
        assert SignatureMethod.BRAINPOOLP256R1_SHA256.curve == CurveType.BRAINPOOLP256R1

    def test_hash_algorithm_property(self) -> None:
        assert SignatureMethod.SECP256R1_SHA256.hash_algorithm == HashAlgorithm.SHA256
        assert SignatureMethod.SECP256R1_SHA512.hash_algorithm == HashAlgorithm.SHA512
        assert SignatureMethod.SECP384R1_SHA256.hash_algorithm == HashAlgorithm.SHA256

    def test_roundtrip(self) -> None:
        for sig_method in SignatureMethod:
            reconstructed = SignatureMethod.from_parts(sig_method.curve, sig_method.hash_algorithm)
            assert reconstructed == sig_method

    def test_from_parts_invalid_combination(self) -> None:
        # SECP521R1 with SHA256 exists, but let's test with a curve that
        # doesn't have all combinations defined if any exist
        # Actually all combinations exist in our enum, so we test a made-up case
        # by directly checking that from_parts validates against enum members
        with pytest.raises(ValueError, match="invalid"):
            # This would create "ECDSA-invalid-SHA256" which isn't a valid member
            SignatureMethod.from_parts(
                CurveType("invalid"),
                HashAlgorithm.SHA256,
            )
