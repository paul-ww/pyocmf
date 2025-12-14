"""Tests for PublicKeyInfo model and extraction from XML."""

import pathlib

import pytest

from pyocmf.utils.xml import extract_ocmf_data_from_file

# Check if cryptography is available
try:
    from pyocmf.types.public_key import PublicKey

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not installed"
)


class TestPublicKeyInfo:
    """Test suite for PublicKeyInfo model."""

    def test_parse_secp256r1_key(self) -> None:
        """Test parsing a secp256r1 public key."""
        public_key_hex = (
            "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
            "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C21"
            "08A0D6DC7D4AB1A5E1A7955BE"
        )

        key_info = PublicKey.from_hex(public_key_hex)

        assert key_info.key_hex == public_key_hex
        assert key_info.curve == "secp256r1"
        assert key_info.key_size == 256
        assert key_info.block_length == 32
        assert key_info.key_type_identifier == "ECDSA-secp256r1"

    def test_parse_secp192r1_key(self) -> None:
        """Test parsing a secp192r1 public key."""
        public_key_hex = (
            "3049301306072a8648ce3d020106082a8648ce3d030101033200041e155ef46fbcc56005769c08"
            "d792127c006c242ccccd96bf7051b6fbc278497036659e7bae57f542776a17c7f8b28600"
        )

        key_info = PublicKey.from_hex(public_key_hex)

        assert key_info.curve == "secp192r1"
        assert key_info.key_size == 192
        assert key_info.block_length == 24
        assert key_info.key_type_identifier == "ECDSA-secp192r1"

    def test_matches_signature_algorithm(self) -> None:
        """Test matching key curve to signature algorithm."""
        public_key_hex = (
            "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
            "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C21"
            "08A0D6DC7D4AB1A5E1A7955BE"
        )

        key_info = PublicKey.from_hex(public_key_hex)

        assert key_info.matches_signature_algorithm("ECDSA-secp256r1-SHA256") is True
        assert key_info.matches_signature_algorithm("ECDSA-secp192r1-SHA256") is False
        assert key_info.matches_signature_algorithm("ECDSA-secp384r1-SHA256") is False
        assert key_info.matches_signature_algorithm(None) is False

    def test_parse_invalid_key(self) -> None:
        """Test that invalid key raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse public key"):
            PublicKey.from_hex("not_a_valid_hex_key")

    def test_parse_non_hex(self) -> None:
        """Test that non-hex string raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse public key"):
            PublicKey.from_hex("xyz123")


class TestXmlPublicKeyExtraction:
    """Test suite for extracting PublicKeyInfo from XML files."""

    def test_extract_public_key_info_from_xml(self, transparency_xml_dir: pathlib.Path) -> None:
        """Test extracting PublicKeyInfo from XML file."""
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        ocmf_data_list = extract_ocmf_data_from_file(xml_file)

        assert len(ocmf_data_list) > 0
        ocmf_data = ocmf_data_list[0]

        # public_key_info provides structured metadata
        assert ocmf_data.public_key is not None
        assert ocmf_data.public_key.curve == "secp256r1"
        assert ocmf_data.public_key.key_size == 256
        assert ocmf_data.public_key.block_length == 32
        assert ocmf_data.public_key.key_hex.startswith("3059")

    def test_public_key_info_matches_signature_algorithm(
        self, transparency_xml_dir: pathlib.Path
    ) -> None:
        """Test that extracted key info matches the OCMF signature algorithm."""
        from pyocmf import OCMF

        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        ocmf_data_list = extract_ocmf_data_from_file(xml_file)
        ocmf_data = ocmf_data_list[0]
        ocmf = OCMF.from_string(ocmf_data.ocmf_string)

        assert ocmf_data.public_key is not None
        assert ocmf.signature.SA is not None
        assert ocmf_data.public_key.matches_signature_algorithm(ocmf.signature.SA)

    def test_xml_without_public_key(self, tmp_path: pathlib.Path) -> None:
        """Test XML file without public key element."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<values>
    <value>
        <signedData format="OCMF">OCMF|{"FV":"1.0"}|{"SD":"abc"}</signedData>
    </value>
</values>"""

        xml_file = tmp_path / "no_key.xml"
        xml_file.write_text(xml_content)

        ocmf_data_list = extract_ocmf_data_from_file(xml_file)

        assert len(ocmf_data_list) == 1
        assert ocmf_data_list[0].public_key is None
