import pydantic
import pytest

from pyocmf.core import Payload
from pyocmf.enums.identifiers import IdentificationType


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

    def test_iso14443_rejects_invalid_length(self) -> None:
        with pytest.raises(pydantic.ValidationError, match="does not match format"):
            Payload(
                PG="T1",
                GS="000001",
                IS=True,
                IT=IdentificationType.ISO14443,
                ID="1234567890abcdef",  # 16 chars - too long for ISO14443
                RD=[],
            )

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

    def test_iso15693_requires_16_hex_chars(self) -> None:
        with pytest.raises(pydantic.ValidationError, match="does not match format"):
            Payload(
                PG="T1",
                GS="000001",
                IS=True,
                IT=IdentificationType.ISO15693,
                ID="E007000012345",  # Only 14 chars
                RD=[],
            )

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

    def test_emaid_requires_14_15_alphanumeric(self) -> None:
        with pytest.raises(pydantic.ValidationError, match="does not match format"):
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
        with pytest.raises(pydantic.ValidationError, match="does not match format"):
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
        with pytest.raises(pydantic.ValidationError, match="not a valid phone number"):
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
