"""Tests for Eichrecht (German calibration law) compliance checking."""

from __future__ import annotations

import decimal

from pyocmf.compliance import (
    IssueCode,
    IssueSeverity,
    check_eichrecht_reading,
    check_eichrecht_transaction,
)
from pyocmf.sections.payload import Payload
from pyocmf.sections.reading import MeterReadingReason, MeterStatus, OCMFTimestamp, Reading
from pyocmf.types.identifiers import IdentificationType, UserAssignmentStatus
from pyocmf.types.obis import OBIS
from pyocmf.types.units import EnergyUnit


class TestEichrechtReadingValidation:
    """Test individual reading compliance checking for Eichrecht."""

    def test_valid_reading_passes(self) -> None:
        """A compliant reading should pass all checks."""
        reading = Reading(
            TM=OCMFTimestamp.from_string("2023-01-01T12:00:00,000+0000 S"),
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("100.5"),
            RI=OBIS.from_string("01-00:B2.08.00*FF"),
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,  # Good status
            EF="",  # No error flags
        )
        issues = check_eichrecht_reading(reading)
        assert len(issues) == 0

    def test_meter_status_not_ok_fails(self) -> None:
        """Meter status must be OK (G) for billing."""
        reading = Reading(
            TM=OCMFTimestamp.from_string("2023-01-01T12:00:00,000+0000 S"),
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("100.5"),
            RI=OBIS.from_string("01-00:B2.08.00*FF"),
            RU=EnergyUnit.KWH,
            ST=MeterStatus.TIMEOUT,  # Not OK!
            EF="",
        )
        issues = check_eichrecht_reading(reading)
        assert any(issue.code == IssueCode.METER_STATUS for issue in issues)
        assert any("must be 'G'" in issue.message for issue in issues)

    def test_error_flags_present_fails(self) -> None:
        """Error flags must be empty for billing."""
        reading = Reading(
            TM=OCMFTimestamp.from_string("2023-01-01T12:00:00,000+0000 S"),
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("100.5"),
            RI=OBIS.from_string("01-00:B2.08.00*FF"),
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
            EF="E",  # Error flag present!
        )
        issues = check_eichrecht_reading(reading)
        assert any(issue.code == IssueCode.ERROR_FLAGS for issue in issues)

    def test_unsynchronized_time_warns(self) -> None:
        """Unsynchronized time should produce a warning."""
        reading = Reading(
            TM=OCMFTimestamp.from_string("2023-01-01T12:00:00,000+0000 U"),
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("100.5"),
            RI=OBIS.from_string("01-00:B2.08.00*FF"),
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
            EF="",
        )
        issues = check_eichrecht_reading(reading)
        assert any(issue.code == IssueCode.TIME_SYNC for issue in issues)
        assert any(issue.severity == IssueSeverity.WARNING for issue in issues)

    def test_cl_zero_at_begin_passes(self) -> None:
        """Cumulated loss = 0 at transaction begin should pass."""
        reading = Reading(
            TM=OCMFTimestamp.from_string("2023-01-01T12:00:00,000+0000 S"),
            TX=MeterReadingReason.BEGIN,
            RV=decimal.Decimal("50.0"),
            RI=OBIS.from_string("01-00:B2.08.00*FF"),
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
            EF="",
            CL=decimal.Decimal(0),  # Correct: 0 at begin
        )
        issues = check_eichrecht_reading(reading, is_begin=True)
        cl_issues = [i for i in issues if "CL" in i.code]
        assert len(cl_issues) == 0

    def test_cl_positive_at_end_passes(self) -> None:
        """Positive cumulated loss at end should pass."""
        reading = Reading(
            TM=OCMFTimestamp.from_string("2023-01-01T12:00:00,000+0000 S"),
            TX=MeterReadingReason.END,
            RV=decimal.Decimal("100.5"),
            RI=OBIS.from_string("01-00:B2.08.00*FF"),
            RU=EnergyUnit.KWH,
            ST=MeterStatus.OK,
            EF="",
            CL=decimal.Decimal("0.5"),  # Valid at end
        )
        issues = check_eichrecht_reading(reading, is_begin=False)
        cl_issues = [i for i in issues if "CL" in i.code]
        assert len(cl_issues) == 0


class TestEichrechtTransactionValidation:
    """Test transaction pair compliance checking for Eichrecht."""

    def create_valid_begin_payload(self) -> Payload:
        """Create a valid transaction begin payload."""
        return Payload.model_construct(
            FV="1.0",
            GI="TEST_GW",
            GS="12345",
            GV="1.0",
            PG="T1",
            RD=[
                Reading(
                    TM=OCMFTimestamp.from_string("2023-01-01T12:00:00,000+0000 S"),
                    TX=MeterReadingReason.BEGIN,
                    RV=decimal.Decimal("50.0"),
                    RI=OBIS.from_string("01-00:B2.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.OK,
                    EF="",
                )
            ],
            IS=True,
            IL=UserAssignmentStatus.VERIFIED,
            IT=IdentificationType.ISO14443,
            ID="12345678",
        )

    def create_valid_end_payload(self) -> Payload:
        """Create a valid transaction end payload."""
        return Payload.model_construct(
            FV="1.0",
            GI="TEST_GW",
            GS="12345",  # Same serial as begin
            GV="1.0",
            PG="T2",
            RD=[
                Reading(
                    TM=OCMFTimestamp.from_string("2023-01-01T13:00:00,000+0000 S"),  # Later time
                    TX=MeterReadingReason.END,
                    RV=decimal.Decimal("100.0"),  # Higher value
                    RI=OBIS.from_string("01-00:B2.08.00*FF"),  # Same OBIS
                    RU=EnergyUnit.KWH,  # Same unit
                    ST=MeterStatus.OK,
                    EF="",
                )
            ],
            IS=True,
            IL=UserAssignmentStatus.VERIFIED,
            IT=IdentificationType.ISO14443,
            ID="12345678",  # Same ID
        )

    def test_valid_transaction_passes(self) -> None:
        """A valid transaction pair should pass all checks."""
        begin = self.create_valid_begin_payload()
        end = self.create_valid_end_payload()
        issues = check_eichrecht_transaction(begin, end)
        # May have warnings but no errors
        errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
        assert len(errors) == 0

    def test_missing_readings_fails(self) -> None:
        """Transaction must have readings in both begin and end."""
        begin = self.create_valid_begin_payload()
        end = self.create_valid_end_payload()
        end.RD = []  # Remove readings

        issues = check_eichrecht_transaction(begin, end)
        assert any(issue.code == IssueCode.NO_READINGS for issue in issues)

    def test_wrong_begin_tx_type_fails(self) -> None:
        """Begin reading must have TX=B."""
        begin = self.create_valid_begin_payload()
        begin.RD[0].TX = MeterReadingReason.CHARGING  # Wrong type!

        end = self.create_valid_end_payload()
        issues = check_eichrecht_transaction(begin, end)
        assert any(issue.code == IssueCode.BEGIN_TX for issue in issues)

    def test_wrong_end_tx_type_fails(self) -> None:
        """End reading must have TX in end types (E/L/R/A/P)."""
        begin = self.create_valid_begin_payload()
        end = self.create_valid_end_payload()
        end.RD[0].TX = MeterReadingReason.CHARGING  # Wrong type!

        issues = check_eichrecht_transaction(begin, end)
        assert any(issue.code == IssueCode.END_TX for issue in issues)

    def test_serial_mismatch_fails(self) -> None:
        """Serial numbers must match between begin and end."""
        begin = self.create_valid_begin_payload()
        end = self.create_valid_end_payload()
        end.GS = "99999"  # Different serial!

        issues = check_eichrecht_transaction(begin, end)
        assert any(issue.code == IssueCode.SERIAL_MISMATCH for issue in issues)

    def test_obis_mismatch_fails(self) -> None:
        """OBIS codes must match between begin and end."""
        begin = self.create_valid_begin_payload()
        end = self.create_valid_end_payload()
        end.RD[0].RI = OBIS.from_string("01-00:C2.08.00*FF")  # Different OBIS!

        issues = check_eichrecht_transaction(begin, end)
        assert any(issue.code == IssueCode.OBIS_MISMATCH for issue in issues)

    def test_unit_mismatch_fails(self) -> None:
        """Units must match between begin and end."""
        begin = self.create_valid_begin_payload()
        end = self.create_valid_end_payload()
        end.RD[0].RU = EnergyUnit.WH  # Different unit!

        issues = check_eichrecht_transaction(begin, end)
        assert any(issue.code == IssueCode.UNIT_MISMATCH for issue in issues)

    def test_value_regression_fails(self) -> None:
        """End value must be >= begin value."""
        begin = self.create_valid_begin_payload()
        end = self.create_valid_end_payload()
        end.RD[0].RV = decimal.Decimal("25.0")  # Less than begin!

        issues = check_eichrecht_transaction(begin, end)
        assert any(issue.code == IssueCode.VALUE_REGRESSION for issue in issues)

    def test_time_regression_fails(self) -> None:
        """End timestamp must be >= begin timestamp."""
        begin = self.create_valid_begin_payload()
        end = self.create_valid_end_payload()
        end.RD[0].TM = OCMFTimestamp.from_string("2023-01-01T11:00:00,000+0000 S")  # Earlier time!

        issues = check_eichrecht_transaction(begin, end)
        assert any(issue.code == IssueCode.TIME_REGRESSION for issue in issues)

    def test_id_mismatch_warns(self) -> None:
        """Identification data mismatch should produce a warning."""
        begin = self.create_valid_begin_payload()
        end = self.create_valid_end_payload()
        end.ID = "87654321"  # Different ID

        issues = check_eichrecht_transaction(begin, end)
        id_issues = [i for i in issues if i.code == IssueCode.ID_MISMATCH]
        assert len(id_issues) > 0
        assert id_issues[0].severity == IssueSeverity.WARNING
