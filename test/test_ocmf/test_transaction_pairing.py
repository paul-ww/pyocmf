"""Tests for transaction pairing validation."""

from __future__ import annotations

import decimal

from pyocmf.compliance import validate_transaction_pair
from pyocmf.ocmf import OCMF
from pyocmf.sections.payload import Payload
from pyocmf.sections.reading import MeterReadingReason, MeterStatus, OCMFTimestamp, Reading
from pyocmf.sections.signature import Signature
from pyocmf.types.identifiers import IdentificationType, UserAssignmentStatus
from pyocmf.types.obis import OBIS
from pyocmf.types.units import EnergyUnit


class TestTransactionPairValidation:
    """Test transaction pair validation helper."""

    def create_begin_ocmf(
        self,
        serial: str = "12345",
        pagination: str = "T1",
        timestamp: str = "2023-01-01T12:00:00,000+0000 S",
    ) -> OCMF:
        """Create a transaction begin OCMF record."""
        payload = Payload.model_construct(
            FV="1.0",
            GI="TEST_GW",
            GS=serial,
            GV="1.0",
            PG=pagination,
            RD=[
                Reading(
                    TM=OCMFTimestamp.from_string(timestamp),
                    TX=MeterReadingReason.BEGIN,
                    RV=decimal.Decimal("50.0"),
                    RI=OBIS.from_string("01-00:B2.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.OK,
                )
            ],
            IS=True,
            IL=UserAssignmentStatus.VERIFIED,
            IT=IdentificationType.ISO14443,
            ID="12345678",
        )
        signature = Signature(SD="deadbeef")
        return OCMF(header="OCMF", payload=payload, signature=signature)

    def create_end_ocmf(
        self,
        serial: str = "12345",
        pagination: str = "T2",
        timestamp: str = "2023-01-01T13:00:00,000+0000 S",
        value: str = "100.0",
    ) -> OCMF:
        """Create a transaction end OCMF record."""
        payload = Payload.model_construct(
            FV="1.0",
            GI="TEST_GW",
            GS=serial,
            GV="1.0",
            PG=pagination,
            RD=[
                Reading(
                    TM=OCMFTimestamp.from_string(timestamp),
                    TX=MeterReadingReason.END,
                    RV=decimal.Decimal(value),
                    RI=OBIS.from_string("01-00:B2.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.OK,
                )
            ],
            IS=True,
            IL=UserAssignmentStatus.VERIFIED,
            IT=IdentificationType.ISO14443,
            ID="12345678",
        )
        signature = Signature(SD="deadbeef")
        return OCMF(header="OCMF", payload=payload, signature=signature)

    def test_valid_transaction_pair(self) -> None:
        """A valid transaction pair should pass validation."""
        begin = self.create_begin_ocmf()
        end = self.create_end_ocmf()
        assert validate_transaction_pair(begin, end) is True

    def test_missing_readings_in_begin(self) -> None:
        """Validation should fail if begin has no readings."""
        begin = self.create_begin_ocmf()
        begin.payload.RD = []
        end = self.create_end_ocmf()
        assert validate_transaction_pair(begin, end) is False

    def test_wrong_begin_tx_type(self) -> None:
        """Validation should fail if begin doesn't have TX=B."""
        begin = self.create_begin_ocmf()
        begin.payload.RD[0].TX = MeterReadingReason.CHARGING
        end = self.create_end_ocmf()
        assert validate_transaction_pair(begin, end) is False

    def test_wrong_end_tx_type(self) -> None:
        """Validation should fail if end doesn't have valid end TX type."""
        begin = self.create_begin_ocmf()
        end = self.create_end_ocmf()
        end.payload.RD[0].TX = MeterReadingReason.CHARGING
        assert validate_transaction_pair(begin, end) is False

    def test_serial_number_mismatch(self) -> None:
        """Validation should fail if serial numbers don't match."""
        begin = self.create_begin_ocmf(serial="12345")
        end = self.create_end_ocmf(serial="99999")
        assert validate_transaction_pair(begin, end) is False

    def test_pagination_not_consecutive(self) -> None:
        """Validation should fail if pagination is not consecutive."""
        begin = self.create_begin_ocmf(pagination="T1")
        end = self.create_end_ocmf(pagination="T5")  # Should be T2
        assert validate_transaction_pair(begin, end) is False

    def test_pagination_consecutive_passes(self) -> None:
        """Validation should pass with consecutive pagination."""
        begin = self.create_begin_ocmf(pagination="T3")
        end = self.create_end_ocmf(pagination="T4")
        assert validate_transaction_pair(begin, end) is True

    def test_timestamp_regression(self) -> None:
        """Validation should fail if end timestamp is before begin."""
        begin = self.create_begin_ocmf(timestamp="2023-01-01T13:00:00,000+0000 S")
        end = self.create_end_ocmf(timestamp="2023-01-01T12:00:00,000+0000 S")
        assert validate_transaction_pair(begin, end) is False

    def test_value_regression(self) -> None:
        """Validation should fail if end value is less than begin."""
        begin = self.create_begin_ocmf()
        begin.payload.RD[0].RV = decimal.Decimal("100.0")
        end = self.create_end_ocmf(value="50.0")
        assert validate_transaction_pair(begin, end) is False

    def test_termination_tx_types_accepted(self) -> None:
        """All termination TX types should be accepted as end types."""
        begin = self.create_begin_ocmf()

        # Test all end types
        for tx_type in [
            MeterReadingReason.END,
            MeterReadingReason.TERMINATION_LOCAL,
            MeterReadingReason.TERMINATION_REMOTE,
            MeterReadingReason.TERMINATION_ABORT,
            MeterReadingReason.TERMINATION_POWER_FAILURE,
        ]:
            end = self.create_end_ocmf()
            end.payload.RD[0].TX = tx_type
            assert validate_transaction_pair(begin, end) is True
