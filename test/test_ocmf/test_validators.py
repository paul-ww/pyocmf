from __future__ import annotations

import decimal

import pydantic
import pytest

from pyocmf.core import Payload
from pyocmf.core.reading import MeterReadingReason, MeterStatus, OCMFTimestamp, Reading
from pyocmf.enums.identifiers import (
    IdentificationFlagIso15118,
    IdentificationFlagOCPP,
    IdentificationFlagPLMN,
    IdentificationFlagRFID,
    IdentificationType,
)
from pyocmf.enums.units import EnergyUnit
from pyocmf.models import OBIS


# Helper functions to construct typed objects from strings
def tm(timestamp_str: str) -> OCMFTimestamp:
    return OCMFTimestamp.from_string(timestamp_str)


def obis(code_str: str) -> OBIS:
    return OBIS.from_string(code_str)


class TestCLValidators:
    def test_cl_valid_with_accumulation_register_b0(self) -> None:
        reading = Reading(
            TM=tm("2023-01-01T12:00:00,000+0000 S"),
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("100.5"),
            RI=obis("01-00:B0.08.00*FF"),  # B0 = Total Import Mains Energy
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
            CL=decimal.Decimal("0.5"),  # Valid with accumulation register
        )
        assert reading.CL == decimal.Decimal("0.5")

    def test_cl_valid_with_accumulation_register_c3(self) -> None:
        reading = Reading(
            TM=tm("2023-01-01T12:00:00,000+0000 S"),
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("50.0"),
            RI=obis("01-00:C3.08.00*FF"),  # C3 = Transaction Export Device Energy
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
            CL=decimal.Decimal("0.2"),
        )
        assert reading.CL == decimal.Decimal("0.2")

    def test_cl_rejected_with_non_accumulation_register(self) -> None:
        with pytest.raises(
            ValueError, match="can only appear when RI indicates an accumulation register"
        ):
            Reading(
                TM=tm("2023-01-01T12:00:00,000+0000 S"),
                TX=MeterReadingReason.END,
                RV=decimal.Decimal("100.5"),
                RI=obis("01-00:01.08.00*FF"),  # Not a B0-B3 or C0-C3 register
                RU=EnergyUnit.KWH,
                ST=MeterStatus.OK,
                CL=decimal.Decimal("0.5"),  # Should fail
            )

    def test_cl_must_be_zero_at_transaction_begin(self) -> None:
        # Valid: CL=0 at begin
        reading = Reading(
            TM=tm("2023-01-01T12:00:00,000+0000 S"),
            TX=MeterReadingReason.BEGIN,
            RV=decimal.Decimal("50.0"),
            RI=obis("01-00:B3.08.00*FF"),
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
            CL=decimal.Decimal(0),  # Must be 0
        )
        assert reading.CL == decimal.Decimal(0)

    def test_cl_rejected_when_nonzero_at_begin(self) -> None:
        with pytest.raises(ValueError, match="must be 0 when TX=B"):
            Reading(
                TM=tm("2023-01-01T12:00:00,000+0000 S"),
                TX=MeterReadingReason.BEGIN,
                RV=decimal.Decimal("50.0"),
                RI=obis("01-00:B3.08.00*FF"),
                RU=EnergyUnit.KWH,
                ST=MeterStatus.OK,
                CL=decimal.Decimal("0.5"),  # Should fail - must be 0 at begin
            )

    def test_cl_must_be_non_negative(self) -> None:
        with pytest.raises(ValueError, match="must be non-negative"):
            Reading(
                TM=tm("2023-01-01T12:00:00,000+0000 S"),
                TX=MeterReadingReason.END,
                RV=decimal.Decimal("100.0"),
                RI=obis("01-00:B0.08.00*FF"),
                RU=EnergyUnit.KWH,
                ST=MeterStatus.OK,
                CL=decimal.Decimal("-0.5"),  # Should fail
            )

    def test_cl_none_is_allowed(self) -> None:
        reading = Reading(
            TM=tm("2023-01-01T12:00:00,000+0000 S"),
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("100.0"),
            RI=obis("01-00:B0.08.00*FF"),
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
            CL=None,  # Optional
        )
        assert reading.CL is None


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

    def test_cannot_mix_rfid_and_ocpp_flags(self) -> None:
        with pytest.raises(ValueError, match="cannot mix flags from different sources"):
            Payload(
                PG="T1",
                IS=True,
                IF=[
                    IdentificationFlagRFID.ASSIGNMENT_VIA_EXTERNAL_RFID_CARD_READER,
                    IdentificationFlagOCPP.ASSIGNMENT_BY_OCPP_REMOTESTART_METHOD,
                ],
                IT=IdentificationType.ISO14443,
                ID="1A2B3C4D",
                GS="12345",
                RD=[],
            )

    def test_cannot_mix_iso15118_and_plmn_flags(self) -> None:
        with pytest.raises(ValueError, match="cannot mix flags from different sources"):
            Payload(
                PG="T1",
                IS=True,
                IF=[
                    IdentificationFlagIso15118.PLUG_AND_CHARGE_WAS_USED,
                    IdentificationFlagPLMN.CALL,
                ],
                IT=IdentificationType.ISO14443,
                ID="1A2B3C4D",
                GS="12345",
                RD=[],
            )

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


class TestRIRUFieldGroup:
    def test_both_ri_and_ru_present_is_valid(self) -> None:
        reading = Reading(
            TM=tm("2023-01-01T12:00:00,000+0000 S"),
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("100.0"),
            RI=obis("01-00:01.08.00*FF"),
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
        )
        assert reading.RI is not None
        assert reading.RU is not None

    def test_both_ri_and_ru_absent_is_valid(self) -> None:
        # When both are absent, the reading can indicate an event without meter values
        # However, RU is marked as required in the Reading model, so this test
        # is not valid. Skipping this case as the spec allows readings without RI/RU
        # but the current model requires RU.
        pytest.skip("RU is required in current model, cannot test both absent")

    def test_ri_without_ru_fails(self) -> None:
        # RU is required so Pydantic will fail before our validator runs
        # This tests that the field is required
        with pytest.raises(pydantic.ValidationError):
            Reading(
                TM=tm("2023-01-01T12:00:00,000+0000 S"),
                TX=MeterReadingReason.END,
                RV=decimal.Decimal("100.0"),
                RI=obis("01-00:01.08.00*FF"),  # RI present
                RU=None,  # type: ignore[arg-type]  # RU absent - should fail
                ST=MeterStatus.OK,
            )

    def test_ru_without_ri_fails(self) -> None:
        with pytest.raises(ValueError, match="RI .* and RU .* must both be present or both absent"):
            Reading(
                TM=tm("2023-01-01T12:00:00,000+0000 S"),
                TX=MeterReadingReason.END,
                RV=decimal.Decimal("100.0"),
                RI=None,  # RI absent
                RU=EnergyUnit.KWH,  # RU present - should fail
                ST=MeterStatus.OK,
            )


class TestTXSequence:
    def test_valid_sequence_begin_to_end(self) -> None:
        payload = Payload(
            PG="T1",
            IS=False,
            IT=IdentificationType.NONE,
            GS="12345",
            RD=[
                Reading(
                    TM=tm("2023-01-01T12:00:00,000+0000 S"),
                    TX=MeterReadingReason.BEGIN,
                    RV=decimal.Decimal("0.0"),
                    RI=obis("01-00:01.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.OK,
                ),
                Reading(
                    TM=tm("2023-01-01T12:10:00,000+0000 S"),
                    TX=MeterReadingReason.END,
                    RV=decimal.Decimal("10.5"),
                    RI=obis("01-00:01.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.OK,
                ),
            ],
        )
        assert len(payload.RD) == 2

    def test_valid_sequence_begin_charging_end(self) -> None:
        payload = Payload(
            PG="T1",
            IS=False,
            IT=IdentificationType.NONE,
            GS="12345",
            RD=[
                Reading(
                    TM=tm("2023-01-01T12:00:00,000+0000 S"),
                    TX=MeterReadingReason.BEGIN,
                    RV=decimal.Decimal("0.0"),
                    RI=obis("01-00:01.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.OK,
                ),
                Reading(
                    TM=tm("2023-01-01T12:05:00,000+0000 S"),
                    TX=MeterReadingReason.CHARGING,
                    RV=decimal.Decimal("5.0"),
                    RI=obis("01-00:01.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.OK,
                ),
                Reading(
                    TM=tm("2023-01-01T12:10:00,000+0000 S"),
                    TX=MeterReadingReason.END,
                    RV=decimal.Decimal("10.5"),
                    RI=obis("01-00:01.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.OK,
                ),
            ],
        )
        assert len(payload.RD) == 3

    def test_end_without_begin_fails(self) -> None:
        with pytest.raises(ValueError, match="End.*requires TX=B.*Begin.*first"):
            Payload(
                PG="T1",
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[
                    Reading(
                        TM=tm("2023-01-01T12:00:00,000+0000 S"),
                        TX=MeterReadingReason.CHARGING,
                        RV=decimal.Decimal("5.0"),
                        RI=obis("01-00:01.08.00*FF"),
                        RU=EnergyUnit.KWH,
                        ST=MeterStatus.OK,
                    ),
                    Reading(
                        TM=tm("2023-01-01T12:10:00,000+0000 S"),
                        TX=MeterReadingReason.END,  # No BEGIN before this
                        RV=decimal.Decimal("10.5"),
                        RI=obis("01-00:01.08.00*FF"),
                        RU=EnergyUnit.KWH,
                        ST=MeterStatus.OK,
                    ),
                ],
            )

    def test_begin_after_end_fails(self) -> None:
        with pytest.raises(ValueError, match="Begin.*cannot appear after transaction end"):
            Payload(
                PG="T1",
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[
                    Reading(
                        TM=tm("2023-01-01T12:00:00,000+0000 S"),
                        TX=MeterReadingReason.BEGIN,
                        RV=decimal.Decimal("0.0"),
                        RI=obis("01-00:01.08.00*FF"),
                        RU=EnergyUnit.KWH,
                        ST=MeterStatus.OK,
                    ),
                    Reading(
                        TM=tm("2023-01-01T12:10:00,000+0000 S"),
                        TX=MeterReadingReason.END,
                        RV=decimal.Decimal("10.5"),
                        RI=obis("01-00:01.08.00*FF"),
                        RU=EnergyUnit.KWH,
                        ST=MeterStatus.OK,
                    ),
                    Reading(
                        TM=tm("2023-01-01T12:15:00,000+0000 S"),
                        TX=MeterReadingReason.BEGIN,  # Cannot start new transaction
                        RV=decimal.Decimal("10.5"),
                        RI=obis("01-00:01.08.00*FF"),
                        RU=EnergyUnit.KWH,
                        ST=MeterStatus.OK,
                    ),
                ],
            )

    def test_charging_after_end_fails(self) -> None:
        with pytest.raises(ValueError, match="cannot appear after transaction end"):
            Payload(
                PG="T1",
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[
                    Reading(
                        TM=tm("2023-01-01T12:00:00,000+0000 S"),
                        TX=MeterReadingReason.BEGIN,
                        RV=decimal.Decimal("0.0"),
                        RI=obis("01-00:01.08.00*FF"),
                        RU=EnergyUnit.KWH,
                        ST=MeterStatus.OK,
                    ),
                    Reading(
                        TM=tm("2023-01-01T12:10:00,000+0000 S"),
                        TX=MeterReadingReason.END,
                        RV=decimal.Decimal("10.5"),
                        RI=obis("01-00:01.08.00*FF"),
                        RU=EnergyUnit.KWH,
                        ST=MeterStatus.OK,
                    ),
                    Reading(
                        TM=tm("2023-01-01T12:15:00,000+0000 S"),
                        TX=MeterReadingReason.CHARGING,  # Cannot charge after end
                        RV=decimal.Decimal("15.0"),
                        RI=obis("01-00:01.08.00*FF"),
                        RU=EnergyUnit.KWH,
                        ST=MeterStatus.OK,
                    ),
                ],
            )


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

    def test_t0_rejected(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Payload(
                PG="T0",  # Invalid - leading zero
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[],
            )

    def test_t01_rejected(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Payload(
                PG="T01",  # Invalid - leading zero
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[],
            )

    def test_f00_rejected(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Payload(
                PG="F00",  # Invalid - leading zeros
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[],
            )


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

    def test_id_with_value_when_it_none_fails(self) -> None:
        with pytest.raises(ValueError, match="ID must be None or empty when IT=NONE"):
            Payload(
                PG="T1",
                IS=False,
                IT=IdentificationType.NONE,
                ID="some_id",  # Should fail
                GS="12345",
                RD=[],
            )

    def test_id_with_value_when_it_denied_fails(self) -> None:
        with pytest.raises(ValueError, match="ID must be None or empty when IT=DENIED"):
            Payload(
                PG="T1",
                IS=False,
                IT=IdentificationType.DENIED,
                ID="some_id",  # Should fail
                GS="12345",
                RD=[],
            )


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
