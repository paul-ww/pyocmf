"""Tests for PublicKey model and extraction from XML."""

import pathlib

import pytest

from pyocmf.exceptions import PublicKeyError
from pyocmf.utils.xml import OcmfContainer

# Check if cryptography is available
try:
    from pyocmf.types.public_key import PublicKey

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not installed"
)


class TestPublicKey:
    """Test suite for PublicKey model."""

    def test_parse_secp256r1_key(self) -> None:
        """Test parsing a secp256r1 public key."""
        public_key_hex = (
            "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
            "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C21"
            "08A0D6DC7D4AB1A5E1A7955BE"
        )

        key_info = PublicKey.from_string(public_key_hex)

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

        key_info = PublicKey.from_string(public_key_hex)

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

        key_info = PublicKey.from_string(public_key_hex)

        assert key_info.matches_signature_algorithm("ECDSA-secp256r1-SHA256") is True
        assert key_info.matches_signature_algorithm("ECDSA-secp192r1-SHA256") is False
        assert key_info.matches_signature_algorithm("ECDSA-secp384r1-SHA256") is False
        assert key_info.matches_signature_algorithm(None) is False

    def test_parse_invalid_key(self) -> None:
        """Test that valid hex but invalid key raises PublicKeyError."""
        # This is valid hex but not a valid DER-encoded public key
        with pytest.raises(PublicKeyError, match="Failed to parse public key"):
            PublicKey.from_string("0123456789abcdef")

    def test_parse_invalid_encoding(self) -> None:
        """Test that invalid encoding raises error."""
        from pyocmf.exceptions import Base64DecodingError

        # Contains characters that are neither valid hex nor valid base64
        with pytest.raises(Base64DecodingError):
            PublicKey.from_string("not_valid!!!")


class TestXmlPublicKeyExtraction:
    """Test suite for extracting PublicKey from XML files."""

    def test_extract_public_key_from_xml(self, transparency_xml_dir: pathlib.Path) -> None:
        """Test extracting PublicKey from XML file."""
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        container = OcmfContainer.from_xml(xml_file)

        assert len(container) > 0
        entry = container[0]

        # public_key provides structured metadata
        assert entry.public_key is not None
        assert entry.public_key.curve == "secp256r1"
        assert entry.public_key.key_size == 256
        assert entry.public_key.block_length == 32
        assert entry.public_key.key_hex.startswith("3059")

    def test_public_key_matches_signature_algorithm(
        self, transparency_xml_dir: pathlib.Path
    ) -> None:
        """Test that extracted key info matches the OCMF signature algorithm."""
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        container = OcmfContainer.from_xml(xml_file)
        entry = container[0]

        assert entry.public_key is not None
        assert entry.ocmf.signature.SA is not None
        assert entry.public_key.matches_signature_algorithm(entry.ocmf.signature.SA)
