"""Tests for cryptographic signature verification."""

import json
import pathlib

import pytest

from pyocmf.exceptions import SignatureVerificationError
from pyocmf.ocmf import OCMF
from pyocmf.utils.xml import extract_ocmf_strings_from_file, parse_ocmf_from_xml

# Check if cryptography is available by checking if verification module works
try:
    from pyocmf.verification import CRYPTOGRAPHY_AVAILABLE
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not installed"
)


class TestSignatureVerification:
    """Test suite for OCMF signature verification."""

    def test_verify_valid_keba_signature(self, test_data_dir: pathlib.Path) -> None:
        """Test verification of valid KEBA KCP30 signature from XML file."""
        xml_file = test_data_dir / "src" / "test" / "resources" / "xml" / "test_ocmf_keba_kcp30.xml"

        # Extract OCMF and public key from XML
        ocmf = parse_ocmf_from_xml(xml_file)

        # Public key from the XML file
        public_key = (
            "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
            "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C21"
            "08A0D6DC7D4AB1A5E1A7955BE"
        )

        assert ocmf.verify_signature(public_key) is True

    def test_verify_invalid_signature(self, test_data_dir: pathlib.Path) -> None:
        """Test that tampered data results in invalid signature.

        Uses real OCMF from XML but tampers with the payload to make signature invalid.
        """
        xml_file = test_data_dir / "src" / "test" / "resources" / "xml" / "test_ocmf_keba_kcp30.xml"

        # Get original valid OCMF
        ocmf_strings = extract_ocmf_strings_from_file(xml_file)
        original_ocmf = ocmf_strings[0]

        # Tamper with the data (change energy value)
        tampered_ocmf = original_ocmf.replace('"RV":0.2597', '"RV":999.9999')

        public_key = (
            "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
            "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C21"
            "08A0D6DC7D4AB1A5E1A7955BE"
        )

        ocmf = OCMF.from_string(tampered_ocmf)
        assert ocmf.verify_signature(public_key) is False

    def test_verify_wrong_public_key(self, test_data_dir: pathlib.Path) -> None:
        """Test that wrong public key results in invalid signature."""
        xml_file = test_data_dir / "src" / "test" / "resources" / "xml" / "test_ocmf_keba_kcp30.xml"

        ocmf = parse_ocmf_from_xml(xml_file)

        # Use a different public key (from Compleo test data)
        wrong_public_key = (
            "3049301306072a8648ce3d020106082a8648ce3d030101033200041e155ef46fbcc56005769c08"
            "d792127c006c242ccccd96bf7051b6fbc278497036659e7bae57f542776a17c7f8b28600"
        )

        assert ocmf.verify_signature(wrong_public_key) is False

    def test_verify_missing_public_key(self) -> None:
        """Test that verification without public key raises error."""
        ocmf_string = (
            'OCMF|{"FV":"1.0","GI":"Test","GS":"123","GV":"1.0","PG":"T1",'
            '"IS":false,"IL":"NONE","RD":[{"TM":"2022-01-01T12:00:00,000+0000 S",'
            '"TX":"B","RV":0.0,"RI":"1-b:1.8.0","RU":"kWh","ST":"G"}]}|'
            '{"SA":"ECDSA-secp256r1-SHA256","SD":"3046022100abcd1234"}'
        )

        ocmf = OCMF.from_string(ocmf_string)

        with pytest.raises(
            SignatureVerificationError,
            match="Public key is required for signature verification",
        ):
            ocmf.verify_signature()

    def test_verify_malformed_public_key(self) -> None:
        """Test that malformed public key raises error."""
        ocmf_string = (
            'OCMF|{"FV":"1.0","GI":"Test","GS":"123","GV":"1.0","PG":"T1",'
            '"IS":false,"IL":"NONE","RD":[{"TM":"2022-01-01T12:00:00,000+0000 S",'
            '"TX":"B","RV":0.0,"RI":"1-b:1.8.0","RU":"kWh","ST":"G"}]}|'
            '{"SA":"ECDSA-secp256r1-SHA256","SD":"3046022100abcd1234"}'
        )

        ocmf = OCMF.from_string(ocmf_string)

        with pytest.raises(SignatureVerificationError, match="Failed to decode public key"):
            ocmf.verify_signature("not_a_valid_hex_key")

    def test_verify_with_embedded_public_key(self, test_data_dir: pathlib.Path) -> None:
        """Test verification using public key embedded in signature section.

        Uses real OCMF from XML and adds the public key to the signature section.
        """
        xml_file = test_data_dir / "src" / "test" / "resources" / "xml" / "test_ocmf_keba_kcp30.xml"

        # Get original OCMF
        ocmf_strings = extract_ocmf_strings_from_file(xml_file)
        original_ocmf = ocmf_strings[0]

        # Add public key to signature section
        public_key = (
            "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
            "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C21"
            "08A0D6DC7D4AB1A5E1A7955BE"
        )

        # Parse OCMF to get the three parts
        parts = original_ocmf.split("|")
        header = parts[0]
        payload_json = parts[1]
        signature_json = parts[2]

        # Add PK field to signature JSON
        sig_dict = json.loads(signature_json)
        sig_dict["PK"] = public_key
        new_signature_json = json.dumps(sig_dict, separators=(",", ":"))

        # Reconstruct OCMF with embedded public key
        ocmf_with_pk = f"{header}|{payload_json}|{new_signature_json}"

        ocmf = OCMF.from_string(ocmf_with_pk)
        assert ocmf.verify_signature() is True

    def test_signature_algorithm_secp256r1(self, test_data_dir: pathlib.Path) -> None:
        """Test ECDSA-secp256r1-SHA256 signature algorithm."""
        xml_file = test_data_dir / "src" / "test" / "resources" / "xml" / "test_ocmf_keba_kcp30.xml"

        ocmf = parse_ocmf_from_xml(xml_file)

        public_key = (
            "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
            "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C21"
            "08A0D6DC7D4AB1A5E1A7955BE"
        )

        assert ocmf.verify_signature(public_key) is True
        assert ocmf.signature.SA == "ECDSA-secp256r1-SHA256"
