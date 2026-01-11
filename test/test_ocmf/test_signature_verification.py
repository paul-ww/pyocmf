import pathlib

import pytest

from pyocmf.exceptions import SignatureVerificationError
from pyocmf.ocmf import OCMF
from pyocmf.utils.xml import OcmfContainer

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
    return (
        'OCMF|{"FV":"1.0","GI":"Test","GS":"123","GV":"1.0","PG":"T1",'
        '"IS":false,"IL":"NONE","RD":[{"TM":"2022-01-01T12:00:00,000+0000 S",'
        '"TX":"B","RV":0.0,"RI":"1-b:1.8.0","RU":"kWh","ST":"G"}]}|'
        '{"SA":"ECDSA-secp256r1-SHA256","SD":"3046022100abcd1234"}'
    )


class TestSignatureVerification:
    def test_verify_valid_keba_signature(self, transparency_xml_dir: pathlib.Path) -> None:
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        container = OcmfContainer.from_xml(xml_file)
        entry = container[0]

        assert entry.public_key is not None
        assert entry.verify_signature() is True

    def test_verify_invalid_signature(self) -> None:
        # Valid OCMF string with known public key
        public_key = (
            "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
            "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C2"
            "108A0D6DC7D4AB1A5E1A7955BE"
        )

        # Tampered OCMF string (RV changed from 0.2596 to 999.9999)
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

        ocmf = OCMF.from_string(tampered_ocmf)
        assert ocmf.verify_signature(public_key) is False

    def test_verify_wrong_public_key(self, transparency_xml_dir: pathlib.Path) -> None:
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        container = OcmfContainer.from_xml(xml_file)
        ocmf = container[0].ocmf

        # Use a different secp256r1 public key (same curve type, but wrong key)
        # This is a valid secp256r1 key, just not the one that signed this data
        wrong_public_key = (
            "3059301306072a8648ce3d020106082a8648ce3d03010703420004"
            "212d06048b2b1a74bdedd0df839b768f0b700749f1ab041f297e7e0fad0e0fa2"
            "00e93b827c9ce0874b3f1d63dba1fd7d9d881dcbbfedcb228faa7304b4348c36"
        )

        assert ocmf.verify_signature(wrong_public_key) is False

    def test_verify_missing_public_key(self, ocmf_string_without_public_key: str) -> None:
        ocmf = OCMF.from_string(ocmf_string_without_public_key)

        with pytest.raises(TypeError, match="missing 1 required positional argument"):
            ocmf.verify_signature()  # type: ignore[call-arg]

    def test_verify_malformed_public_key(self, ocmf_string_without_public_key: str) -> None:
        ocmf = OCMF.from_string(ocmf_string_without_public_key)

        with pytest.raises(SignatureVerificationError, match="Failed to parse public key"):
            ocmf.verify_signature("not_a_valid_hex_key")

    def test_signature_algorithm_secp256r1(self, transparency_xml_dir: pathlib.Path) -> None:
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        container = OcmfContainer.from_xml(xml_file)
        entry = container[0]

        assert entry.public_key is not None
        assert entry.verify_signature() is True
        assert entry.ocmf.signature.SA == "ECDSA-secp256r1-SHA256"

    def test_verify_key_curve_mismatch(self, transparency_xml_dir: pathlib.Path) -> None:
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        container = OcmfContainer.from_xml(xml_file)
        ocmf = container[0].ocmf
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
