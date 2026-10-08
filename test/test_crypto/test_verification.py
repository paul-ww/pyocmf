import base64
import pathlib

import pytest

from pyocmf.core import OCMF
from pyocmf.enums.crypto import CurveType
from pyocmf.exceptions import SignatureVerificationError
from pyocmf.utils.xml import OcmfContainer, OcmfRecord

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

    def test_verify_with_base64_public_key(
        self, keba_ocmf_string: str, keba_public_key: str
    ) -> None:
        base64_key = base64.b64encode(bytes.fromhex(keba_public_key)).decode("ascii")
        assert OCMF.from_string(keba_ocmf_string).verify_signature(base64_key) is True

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
            match=r"Public key curve mismatch.*secp256r1.*secp192r1",
        ):
            ocmf.verify_signature(secp192r1_public_key)


class TestSecp192k1Fallback:
    """secp192k1 is verified with the ecdsa package, as OpenSSL lacks the curve."""

    @staticmethod
    def _record(transparency_xml_dir: pathlib.Path) -> OcmfRecord:
        return OcmfContainer.from_xml(
            transparency_xml_dir / "test_ocmf_transaction_two_values.xml"
        )[0]

    def test_public_key_metadata(self, transparency_xml_dir: pathlib.Path) -> None:
        public_key = self._record(transparency_xml_dir).public_key
        assert public_key is not None
        assert public_key.curve == CurveType.SECP192K1
        assert public_key.size == 192
        assert public_key.block_length == 24

    def test_valid_signature(self, transparency_xml_dir: pathlib.Path) -> None:
        assert self._record(transparency_xml_dir).verify_signature() is True

    def test_tampered_payload(self, transparency_xml_dir: pathlib.Path) -> None:
        record = self._record(transparency_xml_dir)
        tampered = record.ocmf.to_string().replace('"RV":3.51824', '"RV":4.51824')
        assert OCMF.from_string(tampered).verify_signature(record.public_key) is False

    def test_malformed_signature(self, transparency_xml_dir: pathlib.Path) -> None:
        record = self._record(transparency_xml_dir)
        signature = record.ocmf.to_string().rsplit('"SD":"', 1)[0]
        broken = OCMF.from_string(f'{signature}"SD":"3001"}}')
        assert broken.verify_signature(record.public_key) is False

    def test_point_off_curve(self, transparency_xml_dir: pathlib.Path) -> None:
        record = self._record(transparency_xml_dir)
        assert record.public_key is not None
        key = bytes.fromhex(record.public_key.key)
        off_curve = (key[:-1] + bytes([key[-1] ^ 1])).hex()
        with pytest.raises(SignatureVerificationError, match="Failed to parse public key"):
            record.ocmf.verify_signature(off_curve)
