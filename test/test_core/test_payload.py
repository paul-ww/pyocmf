from __future__ import annotations

import warnings

import pydantic
import pytest

from pyocmf.core import Payload
from pyocmf.enums.identifiers import (
    IdentificationFlagIso15118,
    IdentificationFlagOCPP,
    IdentificationFlagPLMN,
    IdentificationFlagRFID,
    IdentificationType,
)


class TestIdValidationByType:
    def test_local_type_accepts_any_string(self) -> None:
        # Per spec: LOCAL type accepts any string value
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=True,
            IT=IdentificationType.LOCAL,
            # 32 hex chars - wouldn't be valid for other types
            ID="arbitrary_hex_string_32_chars_long",
            RD=[],
        )
        assert payload.ID == "arbitrary_hex_string_32_chars_long"

    def test_iso14443_accepts_8_hex_chars(self) -> None:
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=True,
            IT=IdentificationType.ISO14443,
            ID="1A2B3C4D",
            RD=[],
        )
        assert payload.ID == "1A2B3C4D"

    def test_iso14443_accepts_14_hex_chars(self) -> None:
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=True,
            IT=IdentificationType.ISO14443,
            ID="1A2B3C4D5E6F70",
            RD=[],
        )
        assert payload.ID == "1A2B3C4D5E6F70"

    def test_iso15693_accepts_16_hex_chars(self) -> None:
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=True,
            IT=IdentificationType.ISO15693,
            ID="E007000012345678",
            RD=[],
        )
        assert payload.ID == "E007000012345678"

    def test_iso14443_warns_on_invalid_length(self) -> None:
        """ISO14443 with non-standard length should emit warning but not fail."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            payload = Payload(
                PG="T1",
                GS="000001",
                IS=True,
                IT=IdentificationType.ISO14443,
                ID="5EEFE0C7F64B050E9FB95C",  # 22 chars - non-standard
                RD=[],
            )
            assert len(w) == 1
            assert "does not match expected format" in str(w[0].message)
            assert "ISO14443" in str(w[0].message)
            assert payload.ID == "5EEFE0C7F64B050E9FB95C"

    def test_iso15693_warns_on_invalid_length(self) -> None:
        """ISO15693 with non-standard length should emit warning but not fail."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            payload = Payload(
                PG="T1",
                GS="000001",
                IS=True,
                IT=IdentificationType.ISO15693,
                ID="112233445566CC",  # 14 chars - expects 16
                RD=[],
            )
            assert len(w) == 1
            assert "does not match expected format" in str(w[0].message)
            assert "ISO15693" in str(w[0].message)
            assert payload.ID == "112233445566CC"

    def test_emaid_requires_14_15_alphanumeric(self) -> None:
        with pytest.raises(pydantic.ValidationError, match="does not match expected format"):
            Payload(
                PG="T1",
                GS="000001",
                IS=True,
                IT=IdentificationType.EMAID,
                ID="DETNME123456",  # Only 12 chars
                RD=[],
            )

    def test_emaid_accepts_14_chars(self) -> None:
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=True,
            IT=IdentificationType.EMAID,
            ID="DETNME12345678",
            RD=[],
        )
        assert payload.ID == "DETNME12345678"

    def test_iso7812_accepts_digits_only(self) -> None:
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=True,
            IT=IdentificationType.ISO7812,
            ID="4111111111111111",
            RD=[],
        )
        assert payload.ID == "4111111111111111"

    def test_iso7812_rejects_non_digits(self) -> None:
        with pytest.raises(pydantic.ValidationError, match="does not match expected format"):
            Payload(
                PG="T1",
                GS="000001",
                IS=True,
                IT=IdentificationType.ISO7812,
                ID="4111111111111ABC",  # Contains letters
                RD=[],
            )

    def test_central_type_accepts_any_string(self) -> None:
        # Per spec: CENTRAL type accepts any string value
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=True,
            IT=IdentificationType.CENTRAL,
            ID="any-arbitrary-string-here",
            RD=[],
        )
        assert payload.ID == "any-arbitrary-string-here"

    def test_central_1_type_accepts_any_string(self) -> None:
        # Per spec: CENTRAL_1 type accepts any string value
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=True,
            IT=IdentificationType.CENTRAL_1,
            ID="uuid-or-anything-goes",
            RD=[],
        )
        assert payload.ID == "uuid-or-anything-goes"

    def test_card_txn_nr_accepts_any_string(self) -> None:
        # Per spec: CARD_TXN_NR type accepts any string value
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=True,
            IT=IdentificationType.CARD_TXN_NR,
            ID="transaction-ref-12345",
            RD=[],
        )
        assert payload.ID == "transaction-ref-12345"

    def test_key_code_accepts_any_string(self) -> None:
        # Per spec: KEY_CODE type accepts any string value
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=True,
            IT=IdentificationType.KEY_CODE,
            ID="secret-key-abc123xyz",
            RD=[],
        )
        assert payload.ID == "secret-key-abc123xyz"

    def test_phone_number_accepts_valid_number(self) -> None:
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=True,
            IT=IdentificationType.PHONE_NUMBER,
            ID="+1 234 567 8901",  # Valid US international format
            RD=[],
        )
        assert payload.ID is not None

    def test_phone_number_accepts_various_formats(self) -> None:
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=True,
            IT=IdentificationType.PHONE_NUMBER,
            ID="+49301234567",  # German format without spaces
            RD=[],
        )
        assert payload.ID is not None

    def test_phone_number_rejects_invalid_format(self) -> None:
        with pytest.raises(pydantic.ValidationError, match="does not match expected format"):
            Payload(
                PG="T1",
                GS="000001",
                IS=True,
                IT=IdentificationType.PHONE_NUMBER,
                ID="not-a-phone",  # Invalid format
                RD=[],
            )

    def test_none_type_accepts_no_id(self) -> None:
        payload = Payload(
            PG="T1",
            GS="000001",
            IS=False,
            IT=IdentificationType.NONE,
            ID=None,
            RD=[],
        )
        assert payload.ID is None


class TestIFFlagMixing:
    def test_rfid_flags_only_allowed(self) -> None:
        payload = Payload(
            PG="T1",
            IS=True,
            IF=[
                IdentificationFlagRFID.ASSIGNMENT_VIA_EXTERNAL_RFID_CARD_READER,
                IdentificationFlagRFID.ASSIGNMENT_VIA_PROTECTED_RFID_CARD_READER,
            ],
            IT=IdentificationType.ISO14443,
            ID="1A2B3C4D",
            GS="12345",
            RD=[],
        )
        assert len(payload.IF) == 2

    def test_ocpp_flags_only_allowed(self) -> None:
        payload = Payload(
            PG="T1",
            IS=True,
            IF=[
                IdentificationFlagOCPP.ASSIGNMENT_BY_OCPP_REMOTESTART_METHOD,
                IdentificationFlagOCPP.ASSIGNMENT_BY_OCPP_REMOTESTART_METHOD_TLS,
            ],
            IT=IdentificationType.ISO14443,
            ID="1A2B3C4D",
            GS="12345",
            RD=[],
        )
        assert len(payload.IF) == 2

    def test_can_mix_all_none_flags(self) -> None:
        payload = Payload(
            PG="T1",
            IS=False,
            IF=[
                IdentificationFlagRFID.NO_ASSIGNMENT_VIA_RFID,
                IdentificationFlagOCPP.NO_USER_ASSIGNMENT_BY_OCPP,
                IdentificationFlagIso15118.NO_USER_ASSIGNMENT_BY_ISO_15118,
                IdentificationFlagPLMN.NO_USER_ASSIGNMENT,
            ],
            IT=IdentificationType.NONE,
            GS="12345",
            RD=[],
        )
        assert len(payload.IF) == 4


class TestPaginationPattern:
    def test_valid_transaction_pagination(self) -> None:
        for pg in ["T1", "T12", "T999", "T1234567"]:
            payload = Payload(
                PG=pg,
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[],
            )
            assert payload.PG == pg

    def test_valid_fiscal_pagination(self) -> None:
        for pg in ["F1", "F42", "F999", "F7654321"]:
            payload = Payload(
                PG=pg,
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[],
            )
            assert payload.PG == pg


class TestIDValidation:
    def test_id_none_when_it_none(self) -> None:
        payload = Payload(
            PG="T1",
            IS=False,
            IT=IdentificationType.NONE,
            ID=None,  # Must be None
            GS="12345",
            RD=[],
        )
        assert payload.ID is None

    def test_id_empty_string_when_it_none(self) -> None:
        payload = Payload(
            PG="T1",
            IS=False,
            IT=IdentificationType.NONE,
            ID="",  # Empty string also allowed
            GS="12345",
            RD=[],
        )
        assert payload.ID == ""

    def test_id_none_when_it_denied(self) -> None:
        payload = Payload(
            PG="T1",
            IS=False,
            IT=IdentificationType.DENIED,
            ID=None,
            GS="12345",
            RD=[],
        )
        assert payload.ID is None

    def test_id_none_when_it_undefined(self) -> None:
        payload = Payload(
            PG="T1",
            IS=False,
            IT=IdentificationType.UNDEFINED,
            ID=None,
            GS="12345",
            RD=[],
        )
        assert payload.ID is None


class TestTTMaxLength:
    def test_tt_within_250_chars_valid(self) -> None:
        tt_250 = "A" * 250
        payload = Payload(
            PG="T1",
            IS=False,
            IT=IdentificationType.NONE,
            TT=tt_250,
            GS="12345",
            RD=[],
        )
        assert payload.TT is not None
        assert len(payload.TT) == 250

    def test_tt_251_chars_rejected(self) -> None:
        tt_251 = "A" * 251
        with pytest.raises(ValueError, match="String should have at most 250 characters"):
            Payload(
                PG="T1",
                IS=False,
                IT=IdentificationType.NONE,
                TT=tt_251,  # Too long
                GS="12345",
                RD=[],
            )

    def test_tt_none_allowed(self) -> None:
        payload = Payload(
            PG="T1",
            IS=False,
            IT=IdentificationType.NONE,
            TT=None,
            GS="12345",
            RD=[],
        )
        assert payload.TT is None
