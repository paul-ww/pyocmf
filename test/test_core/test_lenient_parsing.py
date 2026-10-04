"""Inputs the Transparenzsoftware accepts are parsed, with a SpecWarning for spec deviations."""

from __future__ import annotations

import pathlib
import warnings

import pytest

from pyocmf.compliance import IssueCode, check_eichrecht_transaction
from pyocmf.core import OCMF
from pyocmf.crypto.availability import CRYPTOGRAPHY_AVAILABLE
from pyocmf.exceptions import (
    OcmfFormatError,
    OcmfPayloadError,
    OcmfSignatureError,
    PyOCMFError,
    SignatureVerificationError,
    SpecWarning,
)
from pyocmf.utils.xml import OcmfContainer

from ..conftest import KEBA_OCMF_STRING
from ..helpers import assert_has_error, assert_no_errors, create_transaction_pair

# OCMFVerificationParserTest: pre-1.0 ABL record (FV 0.1, VI/VV keys, IS as level, EI)
ABL_PAYLOAD = (
    '{"FV":"0.1","VI":"ABL","VV":"1.4p3","PG":"T12345","MV":"Phoenix Contact",'
    '"MM":"EEM-350-D-MCB","MS":"BQ27400330016","MF":"1.0","IS":"VERIFIED",'
    '"IF":["RFID_PLAIN","OCPP_RS_TLS"],"IT":"ISO14443","ID":"1F2D3A4F5506C7",'
    '"RD":[{"TM":"2018-07-24T13:22:04,000+0200 S","TX":"B","RV":2935.6,"RI":"1-b:1.8.e",'
    '"RU":"kWh","EI":567,"ST":"G"}]}'
)
ABL_SIGNATURE = (
    '{"SA":"ECDSA-secp256k1-SHA256","SD":"3046022100A7F1FD39278A88432E1AB81229C34CE1066885'
    "D0EAD8810DB900018A4960888302210089004420623749BF75561F29685CD87D6853EC08E83BD1A15C5DAFF9"
    'F03F4115"}'
)
ABL_OCMF = f"OCMF|{ABL_PAYLOAD}|{ABL_SIGNATURE}"
ABL_PUBLIC_KEY = (
    "3056301006072a8648ce3d020106052b8104000a034200044e4970098eeff5e0e286e3a38552679771b8"
    "9315a49dddf66ebac6f176fb02df9841091010e6850510540dad0cf967fd8de0ab25198282b39597ddce"
    "09edf459"
)


def _parse_with_spec_warning(ocmf_string: str, match: str) -> OCMF:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SpecWarning)
        ocmf = OCMF.from_string(ocmf_string)
    with pytest.warns(SpecWarning, match=match):
        OCMF.from_string(ocmf_string)
    return ocmf


def _abl_with(old: str, new: str) -> str:
    assert old in ABL_OCMF
    return ABL_OCMF.replace(old, new)


class TestPre10Format:
    def test_abl_record_parses(self) -> None:
        ocmf = _parse_with_spec_warning(ABL_OCMF, "'VERIFIED' is not a value defined")
        assert ocmf.payload.IS == "VERIFIED"
        assert ocmf.payload.RD[0].model_extra == {"EI": 567}

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not installed")
    def test_abl_signature_verifies(self) -> None:
        # testVerificationResult in the Transparenzsoftware
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SpecWarning)
            ocmf = OCMF.from_string(ABL_OCMF)
        assert ocmf.verify_signature(ABL_PUBLIC_KEY) is True

    def test_unknown_key_instead_of_pg(self) -> None:
        # testLongUnknownKey in the Transparenzsoftware
        ocmf = _parse_with_spec_warning(_abl_with('"PG"', '"PG_foobar"'), "Pagination")
        assert ocmf.payload.PG is None

    def test_reading_without_tx(self) -> None:
        # testAblDataNullValues in the Transparenzsoftware
        ocmf = _parse_with_spec_warning(_abl_with('"TX":"B",', ""), "VERIFIED")
        assert ocmf.payload.RD[0].TX is None

    def test_wrong_header_is_rejected(self) -> None:
        # testFormatWrongName: the Transparenzsoftware rejects this too
        with pytest.raises(PyOCMFError):
            OCMF.from_string(_abl_with("OCMF|", "OCMA|"))


class TestUnknownCodes:
    @pytest.mark.parametrize(
        ("old", "new", "field", "value"),
        [
            ('"IT":"ISO14443"', '"IT":"VENDOR_TOKEN"', "IT", "VENDOR_TOKEN"),
            ('"IF":["RFID_PLAIN"', '"IF":["RFID_VENDOR"', "IF", ["RFID_VENDOR", "OCPP_RS_TLS"]),
        ],
    )
    def test_unknown_payload_codes(self, old: str, new: str, field: str, value: object) -> None:
        ocmf = _parse_with_spec_warning(_abl_with(old, new), "is not a value defined")
        assert getattr(ocmf.payload, field) == value

    @pytest.mark.parametrize(
        ("old", "new", "field", "value"),
        [
            ('"TX":"B"', '"TX":"Q"', "TX", "Q"),
            ('"ST":"G"', '"ST":"H"', "ST", "H"),
            ('"RU":"kWh"', '"RU":"kVArh"', "RU", "kVArh"),
        ],
    )
    def test_unknown_reading_codes(self, old: str, new: str, field: str, value: object) -> None:
        ocmf = _parse_with_spec_warning(_abl_with(old, new), "is not a value defined")
        assert getattr(ocmf.payload.RD[0], field) == value

    def test_unknown_error_flag(self) -> None:
        ocmf = _parse_with_spec_warning(_abl_with('"ST":"G"', '"EF":"X","ST":"G"'), "EF")
        assert ocmf.payload.RD[0].EF == "X"

    def test_missing_status(self) -> None:
        ocmf = _parse_with_spec_warning(_abl_with(',"ST":"G"', ""), r"Status \(ST\)")
        assert ocmf.payload.RD[0].ST is None

    def test_unknown_time_status(self) -> None:
        ocmf = _parse_with_spec_warning(_abl_with("+0200 S", "+0200 T"), "Time status 'T'")
        assert ocmf.payload.RD[0].time_status == "T"

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not installed")
    def test_unknown_signature_algorithm_parses_but_cannot_verify(self) -> None:
        ocmf = _parse_with_spec_warning(
            _abl_with("secp256k1", "secp999k1"), "is not a value defined"
        )
        with pytest.raises(SignatureVerificationError, match="Unsupported signature algorithm"):
            ocmf.verify_signature(ABL_PUBLIC_KEY)


class TestExceededLimits:
    def test_more_than_four_identification_flags(self) -> None:
        flags = '"IF":["RFID_PLAIN","OCPP_RS_TLS","ISO15118_NONE","PLMN_NONE","OCPP_CACHE"]'
        ocmf = _parse_with_spec_warning(
            _abl_with('"IF":["RFID_PLAIN","OCPP_RS_TLS"]', flags), "At most 4"
        )
        assert len(ocmf.payload.IF) == 5

    def test_long_charge_controller_firmware(self) -> None:
        ocmf = _parse_with_spec_warning(_abl_with('"MF":"1.0"', f'"CF":"{"9" * 30}"'), "CF")
        assert ocmf.payload.CF == "9" * 30

    def test_missing_serial_numbers(self) -> None:
        ocmf = _parse_with_spec_warning(_abl_with('"MS":"BQ27400330016",', ""), "GS")
        assert ocmf.payload.MS is None

    def test_appended_public_key_section(self) -> None:
        ocmf = _parse_with_spec_warning(f"{ABL_OCMF}|{ABL_PUBLIC_KEY}", "fourth OCMF section")
        assert ocmf.signature.SD.startswith("3046")


class TestTimeSynchronicityLawChecks:
    """OCMFVerifiedDataTest time synchronicity cases."""

    def test_unknown_end_time_status_passes(self) -> None:
        # test_law_time_synchron: "T" is not a defined status but not law-relevant
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SpecWarning)
            begin, end = create_transaction_pair(end_timestamp="2023-01-01T13:00:00,000+0000 T")
        assert_no_errors(check_eichrecht_transaction(begin.payload, end.payload))

    def test_relative_begin_requires_relative_end(self) -> None:
        begin, end = create_transaction_pair(
            begin_timestamp="2023-01-01T12:00:00,000+0000 R",
            end_timestamp="2023-01-01T13:00:00,000+0000 S",
        )
        issues = check_eichrecht_transaction(begin.payload, end.payload)
        assert_has_error(issues, IssueCode.TIME_SYNC)

    def test_relative_begin_and_end_passes(self) -> None:
        begin, end = create_transaction_pair(
            begin_timestamp="2023-01-01T12:00:00,000+0000 R",
            end_timestamp="2023-01-01T13:00:00,000+0000 R",
        )
        assert_no_errors(check_eichrecht_transaction(begin.payload, end.payload))


class TestStrictMode:
    def test_spec_compliant_record_parses(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error", SpecWarning)
            ocmf = OCMF.from_string(KEBA_OCMF_STRING, strict=True)
        assert ocmf.payload.GI == "KEBA_KCP30"

    @pytest.mark.parametrize(
        ("ocmf_string", "error", "match"),
        [
            (ABL_OCMF, OcmfPayloadError, "'VERIFIED' is not a value defined"),
            (
                KEBA_OCMF_STRING.replace('{"SD":', '{"SA":"ECDSA-secp999k1-SHA256","SD":'),
                OcmfSignatureError,
                "for SA",
            ),
            (f"{ABL_OCMF}|{ABL_PUBLIC_KEY}", OcmfFormatError, "fourth OCMF section"),
        ],
    )
    def test_deviations_are_rejected(
        self, ocmf_string: str, error: type[PyOCMFError], match: str
    ) -> None:
        with pytest.raises(error, match=match):
            OCMF.from_string(ocmf_string, strict=True)

    def test_strict_mode_does_not_leak(self) -> None:
        with pytest.raises(OcmfPayloadError):
            OCMF.from_string(ABL_OCMF, strict=True)
        with pytest.warns(SpecWarning):
            OCMF.from_string(ABL_OCMF)

    def test_from_xml(self, transparency_xml_dir: pathlib.Path) -> None:
        # VW_OCMF_load.xml carries a 22-character ID declared as ISO14443
        xml_path = transparency_xml_dir / "VW_OCMF_load.xml"
        with pytest.warns(SpecWarning, match="ISO14443"):
            OcmfContainer.from_xml(xml_path)
        with pytest.raises(OcmfPayloadError, match="ISO14443"):
            OcmfContainer.from_xml(xml_path, strict=True)
