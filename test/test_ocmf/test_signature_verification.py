"""Tests for cryptographic signature verification."""

import pathlib

import pytest

from pyocmf.exceptions import SignatureVerificationError
from pyocmf.ocmf import OCMF
from pyocmf.utils.xml import (
    extract_ocmf_data_from_file,
    parse_ocmf_with_key_from_xml,
)

# Check if cryptography is available by checking if verification module works
try:
    from pyocmf.verification import CRYPTOGRAPHY_AVAILABLE
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not installed"
)


@pytest.fixture
def ocmf_string_without_public_key() -> str:
    """Fixture providing a sample OCMF string without embedded public key."""
    return (
        'OCMF|{"FV":"1.0","GI":"Test","GS":"123","GV":"1.0","PG":"T1",'
        '"IS":false,"IL":"NONE","RD":[{"TM":"2022-01-01T12:00:00,000+0000 S",'
        '"TX":"B","RV":0.0,"RI":"1-b:1.8.0","RU":"kWh","ST":"G"}]}|'
        '{"SA":"ECDSA-secp256r1-SHA256","SD":"3046022100abcd1234"}'
    )


class TestSignatureVerification:
    """Test suite for OCMF signature verification."""

    def test_verify_valid_keba_signature(self, transparency_xml_dir: pathlib.Path) -> None:
        """Test verification of valid KEBA KCP30 signature from XML file."""
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        # Extract OCMF and public key from XML
        ocmf, public_key = parse_ocmf_with_key_from_xml(xml_file)

        assert public_key is not None
        assert ocmf.verify_signature(public_key) is True

    def test_verify_invalid_signature(self, transparency_xml_dir: pathlib.Path) -> None:
        """Test that tampered data results in invalid signature.

        Uses real OCMF from XML but tampers with the payload to make signature invalid.
        """
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        # Get original valid OCMF and public key
        ocmf_data_list = extract_ocmf_data_from_file(xml_file)
        original_ocmf = ocmf_data_list[0].ocmf_string
        public_key = ocmf_data_list[0].public_key.key_hex if ocmf_data_list[0].public_key else None

        # Tamper with the data (change energy value)
        tampered_ocmf = original_ocmf.replace('"RV":0.2597', '"RV":999.9999')

        assert public_key is not None
        ocmf = OCMF.from_string(tampered_ocmf)
        assert ocmf.verify_signature(public_key) is False

    def test_verify_wrong_public_key(self, transparency_xml_dir: pathlib.Path) -> None:
        """Test that wrong public key (but correct curve) results in invalid signature."""
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        ocmf, _correct_key = parse_ocmf_with_key_from_xml(xml_file)

        # Use a different secp256r1 public key (same curve type, but wrong key)
        # This is a valid secp256r1 key, just not the one that signed this data
        wrong_public_key = (
            "3059301306072a8648ce3d020106082a8648ce3d03010703420004"
            "212d06048b2b1a74bdedd0df839b768f0b700749f1ab041f297e7e0fad0e0fa2"
            "00e93b827c9ce0874b3f1d63dba1fd7d9d881dcbbfedcb228faa7304b4348c36"
        )

        assert ocmf.verify_signature(wrong_public_key) is False

    def test_verify_missing_public_key(self, ocmf_string_without_public_key: str) -> None:
        """Test that verification requires public key parameter."""
        ocmf = OCMF.from_string(ocmf_string_without_public_key)

        with pytest.raises(TypeError, match="missing 1 required positional argument"):
            ocmf.verify_signature()  # type: ignore[call-arg]

    def test_verify_malformed_public_key(self, ocmf_string_without_public_key: str) -> None:
        """Test that malformed public key raises error."""
        ocmf = OCMF.from_string(ocmf_string_without_public_key)

        with pytest.raises(SignatureVerificationError, match="Failed to parse public key"):
            ocmf.verify_signature("not_a_valid_hex_key")

    def test_signature_algorithm_secp256r1(self, transparency_xml_dir: pathlib.Path) -> None:
        """Test ECDSA-secp256r1-SHA256 signature algorithm."""
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        ocmf, public_key = parse_ocmf_with_key_from_xml(xml_file)

        assert public_key is not None
        assert ocmf.verify_signature(public_key) is True
        assert ocmf.signature.SA == "ECDSA-secp256r1-SHA256"

    def test_verify_key_curve_mismatch(self, transparency_xml_dir: pathlib.Path) -> None:
        """Test that using a key with wrong curve type raises error."""
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        # Get OCMF with secp256r1 signature
        ocmf, _correct_key = parse_ocmf_with_key_from_xml(xml_file)
        assert ocmf.signature.SA == "ECDSA-secp256r1-SHA256"

        # Use a secp192r1 public key (from Compleo test data which uses secp192r1)
        secp192r1_public_key = (
            "3049301306072a8648ce3d020106082a8648ce3d030101033200041e155ef46fbcc56005769c08"
            "d792127c006c242ccccd96bf7051b6fbc278497036659e7bae57f542776a17c7f8b28600"
        )

        with pytest.raises(
            SignatureVerificationError,
            match="Public key curve mismatch.*secp256r1.*secp192r1",
        ):
            ocmf.verify_signature(secp192r1_public_key)
