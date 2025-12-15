"""Tests for the CLI module."""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

import pytest

from pyocmf.cli import app
from pyocmf.utils.xml import OcmfContainer

if TYPE_CHECKING:
    from typer.testing import CliRunner

try:
    from typer.testing import CliRunner

    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False

try:
    from pyocmf.verification import CRYPTOGRAPHY_AVAILABLE
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

pytestmark = pytest.mark.skipif(not TYPER_AVAILABLE, reason="typer not installed")


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture providing a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_ocmf_string() -> str:
    """Fixture providing a sample OCMF string."""
    return (
        'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5",'
        '"PG":"T32","IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE",'
        '"ISO15118_NONE","PLMN_NONE"],"IT":"NONE","ID":"",'
        '"RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"",'
        '"ST":"G","RV":0.2596,"RI":"1-b:1.8.0","RU":"kWh"},'
        '{"TM":"2019-08-13T10:03:36,000+0000 R","TX":"E","EF":"",'
        '"ST":"G","RV":0.2597,"RI":"1-b:1.8.0","RU":"kWh"}]}|'
        '{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9'
        '022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}'
    )


@pytest.fixture
def sample_public_key() -> str:
    """Fixture providing a sample public key."""
    return (
        "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
        "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C2"
        "108A0D6DC7D4AB1A5E1A7955BE"
    )


class TestCliValidation:
    """Tests for basic CLI validation functionality."""

    def test_validate_valid_ocmf(self, cli_runner: CliRunner, sample_ocmf_string: str) -> None:
        """Test validating a valid OCMF string."""
        result = cli_runner.invoke(app, [sample_ocmf_string])

        assert result.exit_code == 0
        assert "Successfully parsed OCMF string" in result.stdout
        assert "OCMF validation passed" in result.stdout

    def test_validate_invalid_ocmf(self, cli_runner: CliRunner) -> None:
        """Test validating an invalid OCMF string."""
        result = cli_runner.invoke(app, ["INVALID|data|here"])

        assert result.exit_code == 1
        assert "OCMF validation failed" in result.stdout

    def test_validate_with_verbose(self, cli_runner: CliRunner, sample_ocmf_string: str) -> None:
        """Test validation with verbose output."""
        result = cli_runner.invoke(app, [sample_ocmf_string, "--verbose"])

        assert result.exit_code == 0
        assert "OCMF Structure:" in result.stdout
        assert "Payload:" in result.stdout
        assert "Readings:" in result.stdout
        assert "Signature:" in result.stdout
        assert "KEBA_KCP30" in result.stdout

    def test_validate_hex_encoded(self, cli_runner: CliRunner, sample_ocmf_string: str) -> None:
        """Test validating hex-encoded OCMF string (auto-detected)."""
        from pyocmf.ocmf import OCMF

        ocmf = OCMF.from_string(sample_ocmf_string)
        hex_string = ocmf.to_string(hex=True)

        result = cli_runner.invoke(app, [hex_string])

        assert result.exit_code == 0
        assert "Successfully parsed OCMF string" in result.stdout
        assert "OCMF validation passed" in result.stdout

    def test_validate_malformed_hex(self, cli_runner: CliRunner) -> None:
        """Test validating malformed hex string (auto-detected as hex)."""
        result = cli_runner.invoke(app, ["not_valid_hex"])

        assert result.exit_code == 1
        assert "OCMF validation failed" in result.stdout


class TestCliSignatureVerification:
    """Tests for CLI signature verification functionality."""

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_verify_valid_signature(
        self,
        cli_runner: CliRunner,
        sample_ocmf_string: str,
        sample_public_key: str,
    ) -> None:
        """Test verifying a valid signature."""
        result = cli_runner.invoke(app, [sample_ocmf_string, "--public-key", sample_public_key])

        assert result.exit_code == 0
        assert "Signature verification: VALID" in result.stdout
        assert "ECDSA-secp256r1-SHA256" in result.stdout

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_verify_invalid_signature(self, cli_runner: CliRunner, sample_public_key: str) -> None:
        """Test verifying an invalid signature (tampered data)."""
        tampered_ocmf = (
            'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5",'
            '"PG":"T32","IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE",'
            '"ISO15118_NONE","PLMN_NONE"],"IT":"NONE","ID":"",'
            '"RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"",'
            '"ST":"G","RV":999.9999,"RI":"1-b:1.8.0","RU":"kWh"},'
            '{"TM":"2019-08-13T10:03:36,000+0000 R","TX":"E","EF":"",'
            '"ST":"G","RV":0.2597,"RI":"1-b:1.8.0","RU":"kWh"}]}|'
            '{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9'
            '022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}'
        )

        result = cli_runner.invoke(app, [tampered_ocmf, "--public-key", sample_public_key])

        assert result.exit_code == 1
        assert "Signature verification: INVALID" in result.stdout
        assert "signature does not match" in result.stdout

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_verify_malformed_public_key(
        self, cli_runner: CliRunner, sample_ocmf_string: str
    ) -> None:
        """Test verification with malformed public key."""
        result = cli_runner.invoke(app, [sample_ocmf_string, "--public-key", "not_a_valid_key"])

        assert result.exit_code == 1
        assert "Signature verification failed" in result.stdout

    def test_signature_present_without_key(
        self, cli_runner: CliRunner, sample_ocmf_string: str
    ) -> None:
        """Test that CLI suggests verification when signature present but no key provided."""
        result = cli_runner.invoke(app, [sample_ocmf_string])

        assert result.exit_code == 0
        assert "Signature present but not verified" in result.stdout
        assert "use --public-key to verify" in result.stdout


class TestCliRealData:
    """Tests using real OCMF data from XML test files."""

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_verify_real_keba_data(
        self, cli_runner: CliRunner, transparency_xml_dir: pathlib.Path
    ) -> None:
        """Test verification with real KEBA data from XML file."""
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"
        container = OcmfContainer.from_xml(xml_file)

        assert len(container) > 0
        entry = container[0]

        if entry.public_key is None:
            pytest.skip("Public key not available in test data")

        result = cli_runner.invoke(
            app,
            [
                entry.original_string,
                "--public-key",
                entry.public_key.key_hex,
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        assert "Signature verification: VALID" in result.stdout
        assert "KEBA_KCP30" in result.stdout

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_validate_xml_file_auto_detect(
        self, cli_runner: CliRunner, transparency_xml_dir: pathlib.Path
    ) -> None:
        """Test validating XML file with auto-detection (no --xml flag needed)."""
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        result = cli_runner.invoke(app, [str(xml_file)])

        assert result.exit_code == 0
        assert "Found" in result.stdout
        assert "OCMF entry(ies) in XML file" in result.stdout
        assert "Successfully parsed OCMF string" in result.stdout
        assert "Signature verification: VALID" in result.stdout
