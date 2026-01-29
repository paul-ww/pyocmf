from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

import pytest

from pyocmf.cli import app
from pyocmf.core import OCMF

if TYPE_CHECKING:
    from typer.testing import CliRunner

try:
    from typer.testing import CliRunner

    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False

try:
    from pyocmf.crypto.availability import CRYPTOGRAPHY_AVAILABLE
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


pytestmark = pytest.mark.skipif(not TYPER_AVAILABLE, reason="typer not installed")


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def sample_ocmf_string() -> str:
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
    return (
        "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
        "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C2"
        "108A0D6DC7D4AB1A5E1A7955BE"
    )


class TestAllCommand:
    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_all_with_public_key(
        self,
        cli_runner: CliRunner,
        sample_ocmf_string: str,
        sample_public_key: str,
    ) -> None:
        result = cli_runner.invoke(
            app, ["all", sample_ocmf_string, "--public-key", sample_public_key]
        )

        assert result.exit_code == 0
        assert "Signature verification: VALID" in result.stdout
        assert "COMPLIANT" in result.stdout

    def test_all_without_public_key(
        self,
        cli_runner: CliRunner,
        sample_ocmf_string: str,
    ) -> None:
        result = cli_runner.invoke(app, ["all", sample_ocmf_string])

        assert result.exit_code == 0
        assert "No public key available" in result.stdout
        assert "COMPLIANT" in result.stdout

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_all_with_verbose(
        self,
        cli_runner: CliRunner,
        sample_ocmf_string: str,
        sample_public_key: str,
    ) -> None:
        result = cli_runner.invoke(
            app,
            ["all", sample_ocmf_string, "--public-key", sample_public_key, "--verbose"],
        )

        assert result.exit_code == 0
        assert "Signature verification: VALID" in result.stdout
        assert "COMPLIANT WITH WARNINGS" in result.stdout
        assert "OCMF Structure:" in result.stdout


class TestVerifyCommand:
    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_verify_valid_signature(
        self,
        cli_runner: CliRunner,
        sample_ocmf_string: str,
        sample_public_key: str,
    ) -> None:
        result = cli_runner.invoke(
            app, ["verify", sample_ocmf_string, "--public-key", sample_public_key]
        )

        assert result.exit_code == 0
        assert "Signature verification: VALID" in result.stdout
        assert "ECDSA-secp256r1-SHA256" in result.stdout

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_verify_invalid_signature(self, cli_runner: CliRunner, sample_public_key: str) -> None:
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

        result = cli_runner.invoke(
            app, ["verify", tampered_ocmf, "--public-key", sample_public_key]
        )

        assert result.exit_code == 1
        assert "Signature verification: INVALID" in result.stdout
        assert "signature does not match" in result.stdout

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_verify_malformed_public_key(
        self, cli_runner: CliRunner, sample_ocmf_string: str
    ) -> None:
        result = cli_runner.invoke(
            app, ["verify", sample_ocmf_string, "--public-key", "not_a_valid_key"]
        )

        assert result.exit_code == 1
        assert "Signature verification failed" in result.stdout

    def test_verify_without_public_key(
        self, cli_runner: CliRunner, sample_ocmf_string: str
    ) -> None:
        result = cli_runner.invoke(app, ["verify", sample_ocmf_string])

        assert result.exit_code == 0
        assert "No public key provided" in result.stdout
        assert "Signature present but not verified" in result.stdout

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_verify_with_verbose(
        self,
        cli_runner: CliRunner,
        sample_ocmf_string: str,
        sample_public_key: str,
    ) -> None:
        result = cli_runner.invoke(
            app,
            ["verify", sample_ocmf_string, "--public-key", sample_public_key, "--verbose"],
        )

        assert result.exit_code == 0
        assert "Signature verification: VALID" in result.stdout
        assert "OCMF Structure:" in result.stdout
        assert "KEBA_KCP30" in result.stdout

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_verify_hex_encoded(
        self, cli_runner: CliRunner, sample_ocmf_string: str, sample_public_key: str
    ) -> None:
        # Convert to hex using bytes, not OCMF.to_string() which loses _original_payload_json
        hex_string = sample_ocmf_string.encode("utf-8").hex()

        result = cli_runner.invoke(app, ["verify", hex_string, "--public-key", sample_public_key])

        assert result.exit_code == 0
        assert "Signature verification: VALID" in result.stdout

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed")
    def test_verify_xml_file_auto_detect(
        self, cli_runner: CliRunner, transparency_xml_dir: pathlib.Path
    ) -> None:
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        result = cli_runner.invoke(app, ["verify", str(xml_file)])

        assert result.exit_code == 0
        assert "Found" in result.stdout
        assert "OCMF record" in result.stdout
        assert "Signature verification: VALID" in result.stdout


class TestCheckCommand:
    def test_check_compliant_single(self, cli_runner: CliRunner, sample_ocmf_string: str) -> None:
        result = cli_runner.invoke(app, ["check", sample_ocmf_string])

        assert result.exit_code == 0
        assert "COMPLIANT" in result.stdout

    def test_check_non_compliant_single(self, cli_runner: CliRunner) -> None:
        # OCMF with meter status not 'G'
        non_compliant_ocmf = (
            'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5",'
            '"PG":"T32","IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE",'
            '"ISO15118_NONE","PLMN_NONE"],"IT":"NONE","ID":"",'
            '"RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"",'
            '"ST":"E","RV":0.2596,"RI":"1-b:1.8.0","RU":"kWh"}]}|'
            '{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9'
            '022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}'
        )

        result = cli_runner.invoke(app, ["check", non_compliant_ocmf])

        assert result.exit_code == 1
        assert "NOT COMPLIANT" in result.stdout
        assert "error" in result.stdout.lower()

    def test_check_transaction_pair(self, cli_runner: CliRunner) -> None:
        begin_ocmf = (
            'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5",'
            '"PG":"T1","IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE",'
            '"ISO15118_NONE","PLMN_NONE"],"IT":"NONE","ID":"",'
            '"RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"",'
            '"ST":"G","RV":0.0,"RI":"1-b:1.8.0","RU":"kWh"}]}|'
            '{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9'
            '022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}'
        )

        end_ocmf = (
            'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5",'
            '"PG":"T2","IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE",'
            '"ISO15118_NONE","PLMN_NONE"],"IT":"NONE","ID":"",'
            '"RD":[{"TM":"2019-08-13T10:03:36,000+0000 I","TX":"E","EF":"",'
            '"ST":"G","RV":10.5,"RI":"1-b:1.8.0","RU":"kWh"}]}|'
            '{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9'
            '022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}'
        )

        result = cli_runner.invoke(app, ["check", begin_ocmf, end_ocmf])

        assert result.exit_code == 0
        assert "COMPLIANT" in result.stdout
        assert "transaction pair" in result.stdout

    def test_check_invalid_ocmf(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(app, ["check", "INVALID|data|here"])

        assert result.exit_code == 1
        assert "OCMF parsing failed" in result.stdout


class TestInspectCommand:
    def test_inspect_ocmf_string(self, cli_runner: CliRunner, sample_ocmf_string: str) -> None:
        result = cli_runner.invoke(app, ["inspect", sample_ocmf_string])

        assert result.exit_code == 0
        assert "OCMF Structure:" in result.stdout
        assert "Payload:" in result.stdout
        assert "Readings:" in result.stdout
        assert "Signature:" in result.stdout
        assert "KEBA_KCP30" in result.stdout

    def test_inspect_hex_encoded(self, cli_runner: CliRunner, sample_ocmf_string: str) -> None:
        ocmf = OCMF.from_string(sample_ocmf_string)
        hex_string = ocmf.to_string(hex=True)

        result = cli_runner.invoke(app, ["inspect", hex_string])

        assert result.exit_code == 0
        assert "OCMF Structure:" in result.stdout
        assert "KEBA_KCP30" in result.stdout

    def test_inspect_invalid_ocmf(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(app, ["inspect", "not_valid_hex"])

        assert result.exit_code == 1
        assert "OCMF parsing failed" in result.stdout
