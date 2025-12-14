"""Tests for cryptographic signature verification."""

import pytest

from pyocmf.exceptions import SignatureVerificationError
from pyocmf.ocmf import OCMF

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

    def test_verify_valid_keba_signature(self) -> None:
        """Test verification of valid KEBA KCP30 signature."""
        ocmf_string = (
            'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5","PG":"T32",'
            '"IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE","ISO15118_NONE","PLMN_NONE"],'
            '"IT":"NONE","ID":"","RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"",'
            '"ST":"G","RV":0.2596,"RI":"1-b:1.8.0","RU":"kWh"},'
            '{"TM":"2019-08-13T10:03:36,000+0000 R","TX":"E","EF":"","ST":"G","RV":0.2597,'
            '"RI":"1-b:1.8.0","RU":"kWh"}]}|'
            '{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9'
            '022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}'
        )

        public_key = (
            "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
            "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C21"
            "08A0D6DC7D4AB1A5E1A7955BE"
        )

        ocmf = OCMF.from_string(ocmf_string)
        assert ocmf.verify_signature(public_key) is True

    def test_verify_invalid_signature(self) -> None:
        """Test that tampered data results in invalid signature."""
        ocmf_string = (
            'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5","PG":"T32",'
            '"IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE","ISO15118_NONE","PLMN_NONE"],'
            '"IT":"NONE","ID":"","RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"",'
            '"ST":"G","RV":0.2596,"RI":"1-b:1.8.0","RU":"kWh"},'
            '{"TM":"2019-08-13T10:03:36,000+0000 R","TX":"E","EF":"","ST":"G","RV":999.9999,'
            '"RI":"1-b:1.8.0","RU":"kWh"}]}|'
            '{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9'
            '022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}'
        )

        public_key = (
            "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
            "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C21"
            "08A0D6DC7D4AB1A5E1A7955BE"
        )

        ocmf = OCMF.from_string(ocmf_string)
        assert ocmf.verify_signature(public_key) is False

    def test_verify_wrong_public_key(self) -> None:
        """Test that wrong public key results in invalid signature."""
        ocmf_string = (
            'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5","PG":"T32",'
            '"IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE","ISO15118_NONE","PLMN_NONE"],'
            '"IT":"NONE","ID":"","RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"",'
            '"ST":"G","RV":0.2596,"RI":"1-b:1.8.0","RU":"kWh"},'
            '{"TM":"2019-08-13T10:03:36,000+0000 R","TX":"E","EF":"","ST":"G","RV":0.2597,'
            '"RI":"1-b:1.8.0","RU":"kWh"}]}|'
            '{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9'
            '022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}'
        )

        wrong_public_key = (
            "3049301306072a8648ce3d020106082a8648ce3d030101033200041e155ef46fbcc56005769c08"
            "d792127c006c242ccccd96bf7051b6fbc278497036659e7bae57f542776a17c7f8b28600"
        )

        ocmf = OCMF.from_string(ocmf_string)
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

    def test_verify_with_embedded_public_key(self) -> None:
        """Test verification using public key embedded in signature section."""
        ocmf_string = (
            'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5","PG":"T32",'
            '"IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE","ISO15118_NONE","PLMN_NONE"],'
            '"IT":"NONE","ID":"","RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"",'
            '"ST":"G","RV":0.2596,"RI":"1-b:1.8.0","RU":"kWh"},'
            '{"TM":"2019-08-13T10:03:36,000+0000 R","TX":"E","EF":"","ST":"G","RV":0.2597,'
            '"RI":"1-b:1.8.0","RU":"kWh"}]}|'
            '{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9'
            '022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699",'
            '"PK":"3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB'
            "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C21"
            '08A0D6DC7D4AB1A5E1A7955BE"}'
        )

        ocmf = OCMF.from_string(ocmf_string)
        assert ocmf.verify_signature() is True

    def test_signature_algorithm_secp256r1(self) -> None:
        """Test ECDSA-secp256r1-SHA256 signature algorithm."""
        ocmf_string = (
            'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5","PG":"T32",'
            '"IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE","ISO15118_NONE","PLMN_NONE"],'
            '"IT":"NONE","ID":"","RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"",'
            '"ST":"G","RV":0.2596,"RI":"1-b:1.8.0","RU":"kWh"},'
            '{"TM":"2019-08-13T10:03:36,000+0000 R","TX":"E","EF":"","ST":"G","RV":0.2597,'
            '"RI":"1-b:1.8.0","RU":"kWh"}]}|'
            '{"SA":"ECDSA-secp256r1-SHA256",'
            '"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9'
            '022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}'
        )

        public_key = (
            "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
            "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C21"
            "08A0D6DC7D4AB1A5E1A7955BE"
        )

        ocmf = OCMF.from_string(ocmf_string)
        assert ocmf.verify_signature(public_key) is True
        assert ocmf.signature.SA == "ECDSA-secp256r1-SHA256"
