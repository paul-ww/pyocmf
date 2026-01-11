from __future__ import annotations

import decimal

import pydantic
import pytest

from pyocmf.core import Payload
from pyocmf.core.reading import MeterReadingReason, MeterStatus, OCMFTimestamp, Reading
from pyocmf.enums.identifiers import IdentificationType
from pyocmf.enums.units import EnergyUnit
from pyocmf.models import OBIS


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
