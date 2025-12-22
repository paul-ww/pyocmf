"""Tests for OCMF spec compliance validators.

This module tests the cross-field validators that enforce OCMF specification
constraints, ensuring data integrity and spec compliance.
"""

from __future__ import annotations

import decimal

import pydantic
import pytest

from pyocmf.sections.payload import Payload
from pyocmf.sections.reading import MeterReadingReason, MeterStatus, Reading
from pyocmf.types.identifiers import (
    IdentificationFlagIso15118,
    IdentificationFlagOCPP,
    IdentificationFlagPLMN,
    IdentificationFlagRFID,
    IdentificationType,
)
from pyocmf.types.units import EnergyUnit


class TestCLValidators:
    """Test Cumulated Loss (CL) field validators per OCMF spec Table 7."""

    def test_cl_valid_with_accumulation_register_b0(self) -> None:
        """CL should be allowed with B0 accumulation register (Total Import Mains)."""
        reading = Reading(
            TM="2023-01-01T12:00:00,000+0000 S",
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("100.5"),
            RI="01-00:B0.08.00*FF",  # B0 = Total Import Mains Energy
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
            CL=decimal.Decimal("0.5"),  # Valid with accumulation register
        )
        assert reading.CL == decimal.Decimal("0.5")

    def test_cl_valid_with_accumulation_register_c3(self) -> None:
        """CL should be allowed with C3 accumulation register (Transaction Export Device)."""
        reading = Reading(
            TM="2023-01-01T12:00:00,000+0000 S",
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("50.0"),
            RI="01-00:C3.08.00*FF",  # C3 = Transaction Export Device Energy
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
            CL=decimal.Decimal("0.2"),
        )
        assert reading.CL == decimal.Decimal("0.2")

    def test_cl_rejected_with_non_accumulation_register(self) -> None:
        """CL should be rejected when RI is not an accumulation register."""
        with pytest.raises(
            ValueError, match="can only appear when RI indicates an accumulation register"
        ):
            Reading(
                TM="2023-01-01T12:00:00,000+0000 S",
                TX=MeterReadingReason.END,
                RV=decimal.Decimal("100.5"),
                RI="01-00:01.08.00*FF",  # Not a B0-B3 or C0-C3 register
                RU=EnergyUnit.KWH,
                ST=MeterStatus.OK,
                CL=decimal.Decimal("0.5"),  # Should fail
            )

    def test_cl_must_be_zero_at_transaction_begin(self) -> None:
        """CL must be 0 when TX=B (transaction begin)."""
        # Valid: CL=0 at begin
        reading = Reading(
            TM="2023-01-01T12:00:00,000+0000 S",
            TX=MeterReadingReason.BEGIN,
            RV=decimal.Decimal("50.0"),
            RI="01-00:B3.08.00*FF",
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
            CL=decimal.Decimal(0),  # Must be 0
        )
        assert reading.CL == decimal.Decimal(0)

    def test_cl_rejected_when_nonzero_at_begin(self) -> None:
        """CL > 0 should be rejected when TX=B."""
        with pytest.raises(ValueError, match="must be 0 when TX=B"):
            Reading(
                TM="2023-01-01T12:00:00,000+0000 S",
                TX=MeterReadingReason.BEGIN,
                RV=decimal.Decimal("50.0"),
                RI="01-00:B3.08.00*FF",
                RU=EnergyUnit.KWH,
                ST=MeterStatus.OK,
                CL=decimal.Decimal("0.5"),  # Should fail - must be 0 at begin
            )

    def test_cl_must_be_non_negative(self) -> None:
        """CL must be non-negative (losses cannot be negative)."""
        with pytest.raises(ValueError, match="must be non-negative"):
            Reading(
                TM="2023-01-01T12:00:00,000+0000 S",
                TX=MeterReadingReason.END,
                RV=decimal.Decimal("100.0"),
                RI="01-00:B0.08.00*FF",
                RU=EnergyUnit.KWH,
                ST=MeterStatus.OK,
                CL=decimal.Decimal("-0.5"),  # Should fail
            )

    def test_cl_none_is_allowed(self) -> None:
        """CL can be None (optional field)."""
        reading = Reading(
            TM="2023-01-01T12:00:00,000+0000 S",
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("100.0"),
            RI="01-00:B0.08.00*FF",
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
            CL=None,  # Optional
        )
        assert reading.CL is None


class TestIFFlagMixing:
    """Test Identification Flag mixing rules per OCMF spec Tables 13-16."""

    def test_rfid_flags_only_allowed(self) -> None:
        """Multiple RFID flags from same table should be allowed."""
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
        """Multiple OCPP flags from same table should be allowed."""
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
        """Mixing RFID and OCPP flags should be rejected."""
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
        """Mixing ISO15118 and PLMN flags should be rejected."""
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
        """All _NONE flags can be mixed (indicates no auth via those methods)."""
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
    """Test RI and RU field group constraint per OCMF spec Table 7."""

    def test_both_ri_and_ru_present_is_valid(self) -> None:
        """Both RI and RU present should be valid."""
        reading = Reading(
            TM="2023-01-01T12:00:00,000+0000 S",
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("100.0"),
            RI="01-00:01.08.00*FF",
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
        )
        assert reading.RI is not None
        assert reading.RU is not None

    def test_both_ri_and_ru_absent_is_valid(self) -> None:
        """Both RI and RU absent should be valid (event-only reading)."""
        # When both are absent, the reading can indicate an event without meter values
        # However, RU is marked as required in the Reading model, so this test
        # is not valid. Skipping this case as the spec allows readings without RI/RU
        # but the current model requires RU.
        pytest.skip("RU is required in current model, cannot test both absent")

    def test_ri_without_ru_fails(self) -> None:
        """RI present without RU should fail."""
        # RU is required so Pydantic will fail before our validator runs
        # This tests that the field is required
        with pytest.raises(pydantic.ValidationError):
            Reading(
                TM="2023-01-01T12:00:00,000+0000 S",
                TX=MeterReadingReason.END,
                RV=decimal.Decimal("100.0"),
                RI="01-00:01.08.00*FF",  # RI present
                RU=None,  # RU absent - should fail
                ST=MeterStatus.OK,
            )

    def test_ru_without_ri_fails(self) -> None:
        """RU present without RI should fail."""
        with pytest.raises(ValueError, match="RI .* and RU .* must both be present or both absent"):
            Reading(
                TM="2023-01-01T12:00:00,000+0000 S",
                TX=MeterReadingReason.END,
                RV=decimal.Decimal("100.0"),
                RI=None,  # RI absent
                RU=EnergyUnit.KWH,  # RU present - should fail
                ST=MeterStatus.OK,
            )


class TestTXSequence:
    """Test transaction sequence validation per OCMF spec Table 7."""

    def test_valid_sequence_begin_to_end(self) -> None:
        """Valid sequence: B → E."""
        payload = Payload(
            PG="T1",
            IS=False,
            IT=IdentificationType.NONE,
            GS="12345",
            RD=[
                {
                    "TM": "2023-01-01T12:00:00,000+0000 S",
                    "TX": "B",
                    "RV": 0.0,
                    "RI": "01-00:01.08.00*FF",
                    "RU": "kWh",
                    "ST": "G",
                },
                {
                    "TM": "2023-01-01T12:10:00,000+0000 S",
                    "TX": "E",
                    "RV": 10.5,
                    "RI": "01-00:01.08.00*FF",
                    "RU": "kWh",
                    "ST": "G",
                },
            ],
        )
        assert len(payload.RD) == 2

    def test_valid_sequence_begin_charging_end(self) -> None:
        """Valid sequence: B → C → E."""
        payload = Payload(
            PG="T1",
            IS=False,
            IT=IdentificationType.NONE,
            GS="12345",
            RD=[
                {
                    "TM": "2023-01-01T12:00:00,000+0000 S",
                    "TX": "B",
                    "RV": 0.0,
                    "RI": "01-00:01.08.00*FF",
                    "RU": "kWh",
                    "ST": "G",
                },
                {
                    "TM": "2023-01-01T12:05:00,000+0000 S",
                    "TX": "C",
                    "RV": 5.0,
                    "RI": "01-00:01.08.00*FF",
                    "RU": "kWh",
                    "ST": "G",
                },
                {
                    "TM": "2023-01-01T12:10:00,000+0000 S",
                    "TX": "E",
                    "RV": 10.5,
                    "RI": "01-00:01.08.00*FF",
                    "RU": "kWh",
                    "ST": "G",
                },
            ],
        )
        assert len(payload.RD) == 3

    def test_end_without_begin_fails(self) -> None:
        """TX=E without TX=B should fail."""
        with pytest.raises(ValueError, match="End.*requires TX=B.*Begin.*first"):
            Payload(
                PG="T1",
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[
                    {
                        "TM": "2023-01-01T12:00:00,000+0000 S",
                        "TX": "C",
                        "RV": 5.0,
                        "RI": "01-00:01.08.00*FF",
                        "RU": "kWh",
                        "ST": "G",
                    },
                    {
                        "TM": "2023-01-01T12:10:00,000+0000 S",
                        "TX": "E",  # No BEGIN before this
                        "RV": 10.5,
                        "RI": "01-00:01.08.00*FF",
                        "RU": "kWh",
                        "ST": "G",
                    },
                ],
            )

    def test_begin_after_end_fails(self) -> None:
        """TX=B after TX=E should fail."""
        with pytest.raises(ValueError, match="Begin.*cannot appear after transaction end"):
            Payload(
                PG="T1",
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[
                    {
                        "TM": "2023-01-01T12:00:00,000+0000 S",
                        "TX": "B",
                        "RV": 0.0,
                        "RI": "01-00:01.08.00*FF",
                        "RU": "kWh",
                        "ST": "G",
                    },
                    {
                        "TM": "2023-01-01T12:10:00,000+0000 S",
                        "TX": "E",
                        "RV": 10.5,
                        "RI": "01-00:01.08.00*FF",
                        "RU": "kWh",
                        "ST": "G",
                    },
                    {
                        "TM": "2023-01-01T12:15:00,000+0000 S",
                        "TX": "B",  # Cannot start new transaction
                        "RV": 10.5,
                        "RI": "01-00:01.08.00*FF",
                        "RU": "kWh",
                        "ST": "G",
                    },
                ],
            )

    def test_charging_after_end_fails(self) -> None:
        """TX=C after TX=E should fail."""
        with pytest.raises(ValueError, match="cannot appear after transaction end"):
            Payload(
                PG="T1",
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[
                    {
                        "TM": "2023-01-01T12:00:00,000+0000 S",
                        "TX": "B",
                        "RV": 0.0,
                        "RI": "01-00:01.08.00*FF",
                        "RU": "kWh",
                        "ST": "G",
                    },
                    {
                        "TM": "2023-01-01T12:10:00,000+0000 S",
                        "TX": "E",
                        "RV": 10.5,
                        "RI": "01-00:01.08.00*FF",
                        "RU": "kWh",
                        "ST": "G",
                    },
                    {
                        "TM": "2023-01-01T12:15:00,000+0000 S",
                        "TX": "C",  # Cannot charge after end
                        "RV": 15.0,
                        "RI": "01-00:01.08.00*FF",
                        "RU": "kWh",
                        "ST": "G",
                    },
                ],
            )


class TestPaginationPattern:
    """Test pagination pattern rejects leading zeros per OCMF spec Table 2."""

    def test_valid_transaction_pagination(self) -> None:
        """Valid transaction pagination: T1, T12, T999."""
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
        """Valid fiscal pagination: F1, F42, F999."""
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
        """T0 should be rejected (leading zero)."""
        with pytest.raises(pydantic.ValidationError):
            Payload(
                PG="T0",  # Invalid - leading zero
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[],
            )

    def test_t01_rejected(self) -> None:
        """T01 should be rejected (leading zero)."""
        with pytest.raises(pydantic.ValidationError):
            Payload(
                PG="T01",  # Invalid - leading zero
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[],
            )

    def test_f00_rejected(self) -> None:
        """F00 should be rejected (leading zeros)."""
        with pytest.raises(pydantic.ValidationError):
            Payload(
                PG="F00",  # Invalid - leading zeros
                IS=False,
                IT=IdentificationType.NONE,
                GS="12345",
                RD=[],
            )


class TestIDValidation:
    """Test ID validation with IT types per OCMF spec Table 17."""

    def test_id_none_when_it_none(self) -> None:
        """ID must be None when IT=NONE."""
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
        """ID can be empty string when IT=NONE (backward compatibility)."""
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
        """ID must be None/empty when IT=DENIED."""
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
        """ID must be None/empty when IT=UNDEFINED."""
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
        """ID with a value should fail when IT=NONE."""
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
        """ID with a value should fail when IT=DENIED."""
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
    """Test Tariff Text max length constraint per OCMF spec Table 4."""

    def test_tt_within_250_chars_valid(self) -> None:
        """TT with 250 characters should be valid."""
        tt_250 = "A" * 250
        payload = Payload(
            PG="T1",
            IS=False,
            IT=IdentificationType.NONE,
            TT=tt_250,
            GS="12345",
            RD=[],
        )
        assert len(payload.TT) == 250

    def test_tt_251_chars_rejected(self) -> None:
        """TT with 251 characters should be rejected."""
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
        """TT can be None (optional field)."""
        payload = Payload(
            PG="T1",
            IS=False,
            IT=IdentificationType.NONE,
            TT=None,
            GS="12345",
            RD=[],
        )
        assert payload.TT is None
