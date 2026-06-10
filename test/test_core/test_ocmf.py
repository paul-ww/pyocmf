from __future__ import annotations

import json

import pytest

from pyocmf.core import OCMF
from pyocmf.enums.reading import ReadingType
from pyocmf.exceptions import (
    HexDecodingError,
    OcmfFormatError,
    OcmfPayloadError,
    OcmfSignatureError,
    SignatureVerificationError,
)

from ..helpers import create_test_ocmf

VALID_OCMF_STRING = (
    'OCMF|{"FV":"1.0","GI":"ABL SBC-301","GS":"808829900001","PG":"T12345",'
    '"MS":"BQ27400330016","IS":true,"IL":"VERIFIED","IF":["RFID_PLAIN","OCPP_RS_TLS"],'
    '"IT":"ISO14443","ID":"1F2D3A4F","RD":['
    '{"TM":"2018-07-24T13:22:04,000+0200 S","TX":"B","RV":2935.600,'
    '"RI":"01-00:B2.08.00*FF","RU":"kWh","RT":"DC","EF":"","ST":"G"},'
    '{"TM":"2018-07-24T13:26:04,000+0200 S","TX":"E","RV":2965.1}'
    ']}|{"SD":"1234567890ABCDEF"}'
)


class TestFromString:
    def test_parses_valid_string(self) -> None:
        ocmf = OCMF.from_string(VALID_OCMF_STRING)
        assert ocmf.header == "OCMF"
        assert ocmf.payload.GS == "808829900001"
        assert len(ocmf.payload.RD) == 2

    def test_parses_hex_encoded_string(self) -> None:
        hex_string = VALID_OCMF_STRING.encode("utf-8").hex()
        ocmf = OCMF.from_string(hex_string)
        assert ocmf.payload.GS == "808829900001"

    def test_invalid_prefix_and_not_hex_raises(self) -> None:
        with pytest.raises(HexDecodingError):
            OCMF.from_string("NOT-OCMF-AND-NOT-HEX")

    def test_missing_signature_section_raises(self) -> None:
        with pytest.raises(OcmfFormatError):
            OCMF.from_string('OCMF|{"PG":"T1"}')

    def test_invalid_payload_json_raises(self) -> None:
        with pytest.raises(OcmfPayloadError):
            OCMF.from_string('OCMF|{"PG":"T1"}|{"SD":"abcd"}')

    def test_invalid_signature_json_raises(self) -> None:
        valid_payload = VALID_OCMF_STRING.split("|")[1]
        with pytest.raises(OcmfSignatureError):
            OCMF.from_string(f"OCMF|{valid_payload}|not-json")


class TestReadingFields:
    def test_rt_is_parsed(self) -> None:
        ocmf = OCMF.from_string(VALID_OCMF_STRING)
        assert ocmf.payload.RD[0].RT == ReadingType.DC

    def test_reading_inheritance_fills_omitted_fields(self) -> None:
        # Per spec, fields identical to the previous reading may be omitted
        ocmf = OCMF.from_string(VALID_OCMF_STRING)
        second = ocmf.payload.RD[1]
        assert str(second.RI) == "01-00:B2.08.00*FF"
        assert second.RU == "kWh"
        assert second.RT == ReadingType.DC
        assert second.ST == "G"

    def test_rv_kept_as_decimal_with_exact_places(self) -> None:
        # Spec: the number representation must not be transformed (2935.600 != 2935.6)
        ocmf = OCMF.from_string(VALID_OCMF_STRING)
        assert str(ocmf.payload.RD[0].RV) == "2935.600"


class TestToString:
    def test_roundtrip_preserves_model(self) -> None:
        ocmf = OCMF.from_string(VALID_OCMF_STRING)
        reparsed = OCMF.from_string(ocmf.to_string())
        assert reparsed.payload == ocmf.payload
        assert reparsed.signature == ocmf.signature

    def test_hex_roundtrip(self) -> None:
        ocmf = OCMF.from_string(VALID_OCMF_STRING)
        reparsed = OCMF.from_string(ocmf.to_string(hex=True))
        assert reparsed.payload == ocmf.payload

    def test_rv_serialized_as_json_number(self) -> None:
        # OCMF spec Table 7: RV is of JSON type Number, not String
        ocmf = OCMF.from_string(VALID_OCMF_STRING)
        payload_json = ocmf.to_string().split("|")[1]
        assert isinstance(json.loads(payload_json)["RD"][0]["RV"], float)

    def test_rv_decimal_places_preserved(self) -> None:
        ocmf = OCMF.from_string(VALID_OCMF_STRING)
        payload_json = ocmf.to_string().split("|")[1]
        assert '"RV":2935.600' in payload_json

    def test_ri_serialized_as_string(self) -> None:
        # OCMF spec Table 7: RI is of JSON type String, not an object
        ocmf = OCMF.from_string(VALID_OCMF_STRING)
        payload_json = ocmf.to_string().split("|")[1]
        assert json.loads(payload_json)["RD"][0]["RI"] == "01-00:B2.08.00*FF"

    def test_timestamp_serialized_without_offset_colon(self) -> None:
        # OCMF spec requires a four-digit timezone offset, e.g. +0200
        ocmf = OCMF.from_string(VALID_OCMF_STRING)
        payload_json = ocmf.to_string().split("|")[1]
        tm = json.loads(payload_json)["RD"][0]["TM"]
        assert tm == "2018-07-24T13:22:04,000+0200 S"

    def test_rt_survives_roundtrip(self) -> None:
        ocmf = OCMF.from_string(VALID_OCMF_STRING)
        reparsed = OCMF.from_string(ocmf.to_string())
        assert reparsed.payload.RD[0].RT == ReadingType.DC

    def test_signature_extension_fields_survive_roundtrip(self) -> None:
        # Spec reserves U-Z (vendor) and A-F (processing) prefixed keys in the
        # signature section
        valid_payload = VALID_OCMF_STRING.split("|")[1]
        ocmf = OCMF.from_string(f'OCMF|{valid_payload}|{{"SD":"abcd","XV":"vendor-data"}}')
        signature_json = ocmf.to_string().split("|")[2]
        assert json.loads(signature_json)["XV"] == "vendor-data"


class TestVerifySignature:
    def test_constructed_ocmf_cannot_verify(self) -> None:
        # Verification needs the exact original payload bytes
        ocmf = create_test_ocmf()
        with pytest.raises(SignatureVerificationError, match="original payload JSON"):
            ocmf.verify_signature("04deadbeef")
