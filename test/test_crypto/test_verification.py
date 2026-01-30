import pathlib

import pytest

from pyocmf.core import OCMF
from pyocmf.exceptions import SignatureVerificationError
from pyocmf.utils.xml import OcmfContainer

try:
    from pyocmf.crypto.availability import CRYPTOGRAPHY_AVAILABLE
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

    def test_verify_invalid_signature(
        self,
        keba_ocmf_string_tampered: str,
        keba_public_key: str,
    ) -> None:
        ocmf = OCMF.from_string(keba_ocmf_string_tampered)
        assert ocmf.verify_signature(keba_public_key) is False

    def test_verify_wrong_public_key(self, transparency_xml_dir: pathlib.Path) -> None:
        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

        container = OcmfContainer.from_xml(xml_file)
        ocmf = container[0].ocmf

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

        secp192r1_public_key = (
            "3049301306072a8648ce3d020106082a8648ce3d030101033200041e155ef46fbcc56005769c08"
            "d792127c006c242ccccd96bf7051b6fbc278497036659e7bae57f542776a17c7f8b28600"
        )

        with pytest.raises(
            SignatureVerificationError,
            match="Public key curve mismatch.*secp256r1.*secp192r1",
        ):
            ocmf.verify_signature(secp192r1_public_key)
