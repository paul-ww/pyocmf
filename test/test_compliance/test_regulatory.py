from __future__ import annotations

import decimal

from pyocmf.compliance import (
    IssueCode,
    check_eichrecht_reading,
    check_eichrecht_transaction,
    validate_transaction_pair,
)
from pyocmf.core.reading import MeterReadingReason, MeterStatus
from pyocmf.enums.identifiers import IdentificationType, UserAssignmentStatus
from pyocmf.enums.units import EnergyUnit

from ..helpers import (
    assert_has_issue,
    assert_no_errors,
    create_test_payload,
    create_test_reading,
    create_transaction_pair,
)


class TestEichrechtReadingValidation:
    def test_valid_reading_passes(self) -> None:
        reading = create_test_reading(
            tx=MeterReadingReason.END,
            rv="100.5",
            st=MeterStatus.OK,
            ef="",
        )
        issues = check_eichrecht_reading(reading)
        assert len(issues) == 0

    def test_meter_status_not_ok_fails(self) -> None:
        reading = create_test_reading(
            tx=MeterReadingReason.END,
            st=MeterStatus.TIMEOUT,
        )
        issues = check_eichrecht_reading(reading)
        assert_has_issue(issues, IssueCode.METER_STATUS, "must be 'G'")

    def test_error_flags_present_fails(self) -> None:
        reading = create_test_reading(
            tx=MeterReadingReason.END,
            ef="E",
        )
        issues = check_eichrecht_reading(reading)
        assert_has_issue(issues, IssueCode.ERROR_FLAGS)

    def test_unsynchronized_time_warns(self) -> None:
        reading = create_test_reading(
            timestamp="2023-01-01T12:00:00,000+0000 U",
            tx=MeterReadingReason.END,
        )
        issues = check_eichrecht_reading(reading)
        assert_has_issue(issues, IssueCode.TIME_SYNC)

    def test_cl_zero_at_begin_passes(self) -> None:
        reading = create_test_reading(
            tx=MeterReadingReason.BEGIN,
            rv="50.0",
            cl=decimal.Decimal(0),
        )
        issues = check_eichrecht_reading(reading, is_begin=True)
        cl_issues = [i for i in issues if "CL" in i.code]
        assert len(cl_issues) == 0

    def test_cl_positive_at_end_passes(self) -> None:
        reading = create_test_reading(
            tx=MeterReadingReason.END,
            rv="100.5",
            cl=decimal.Decimal("0.5"),
        )
        issues = check_eichrecht_reading(reading, is_begin=False)
        cl_issues = [i for i in issues if "CL" in i.code]
        assert len(cl_issues) == 0


class TestEichrechtTransactionValidation:
    def test_valid_transaction_passes(self) -> None:
        begin = create_test_payload(
            pagination="T1",
            readings=[create_test_reading(tx=MeterReadingReason.BEGIN, cl=decimal.Decimal(0))],
            identification_status=True,
            identification_level=UserAssignmentStatus.VERIFIED,
            identification_type=IdentificationType.ISO14443,
            identification_data="12345678",
        )
        end = create_test_payload(
            pagination="T2",
            readings=[
                create_test_reading(
                    timestamp="2023-01-01T13:00:00,000+0000 S",
                    tx=MeterReadingReason.END,
                    rv="100.0",
                )
            ],
            identification_status=True,
            identification_level=UserAssignmentStatus.VERIFIED,
            identification_type=IdentificationType.ISO14443,
            identification_data="12345678",
        )
        issues = check_eichrecht_transaction(begin, end)
        assert_no_errors(issues)

    def test_missing_readings_fails(self) -> None:
        begin = create_test_payload(
            readings=[create_test_reading(tx=MeterReadingReason.BEGIN)],
        )
        end = create_test_payload(readings=[])

        issues = check_eichrecht_transaction(begin, end)
        assert_has_issue(issues, IssueCode.NO_READINGS)

    def test_wrong_begin_tx_type_fails(self) -> None:
        begin = create_test_payload(
            readings=[create_test_reading(tx=MeterReadingReason.CHARGING)],
        )
        end = create_test_payload(
            pagination="T2",
            readings=[create_test_reading(tx=MeterReadingReason.END)],
        )
        issues = check_eichrecht_transaction(begin, end)
        assert_has_issue(issues, IssueCode.BEGIN_TX)

    def test_wrong_end_tx_type_fails(self) -> None:
        begin = create_test_payload(
            readings=[create_test_reading(tx=MeterReadingReason.BEGIN)],
        )
        end = create_test_payload(
            pagination="T2",
            readings=[create_test_reading(tx=MeterReadingReason.CHARGING)],
        )
        issues = check_eichrecht_transaction(begin, end)
        assert_has_issue(issues, IssueCode.END_TX)

    def test_serial_mismatch_fails(self) -> None:
        begin = create_test_payload(
            gateway_serial="12345",
            readings=[create_test_reading(tx=MeterReadingReason.BEGIN)],
        )
        end = create_test_payload(
            pagination="T2",
            gateway_serial="99999",
            readings=[create_test_reading(tx=MeterReadingReason.END)],
        )
        issues = check_eichrecht_transaction(begin, end)
        assert_has_issue(issues, IssueCode.SERIAL_MISMATCH)

    def test_obis_mismatch_fails(self) -> None:
        begin = create_test_payload(
            readings=[create_test_reading(tx=MeterReadingReason.BEGIN, ri="01-00:B2.08.00*FF")],
        )
        end = create_test_payload(
            pagination="T2",
            readings=[create_test_reading(tx=MeterReadingReason.END, ri="01-00:C2.08.00*FF")],
        )
        issues = check_eichrecht_transaction(begin, end)
        assert_has_issue(issues, IssueCode.OBIS_MISMATCH)

    def test_unit_mismatch_fails(self) -> None:
        begin = create_test_payload(
            readings=[create_test_reading(tx=MeterReadingReason.BEGIN, ru=EnergyUnit.KWH)],
        )
        end = create_test_payload(
            pagination="T2",
            readings=[create_test_reading(tx=MeterReadingReason.END, ru=EnergyUnit.WH)],
        )
        issues = check_eichrecht_transaction(begin, end)
        assert_has_issue(issues, IssueCode.UNIT_MISMATCH)

    def test_value_regression_fails(self) -> None:
        begin = create_test_payload(
            readings=[create_test_reading(tx=MeterReadingReason.BEGIN, rv="100.0")],
        )
        end = create_test_payload(
            pagination="T2",
            readings=[create_test_reading(tx=MeterReadingReason.END, rv="25.0")],
        )
        issues = check_eichrecht_transaction(begin, end)
        assert_has_issue(issues, IssueCode.VALUE_REGRESSION)

    def test_time_regression_fails(self) -> None:
        begin = create_test_payload(
            readings=[
                create_test_reading(
                    timestamp="2023-01-01T13:00:00,000+0000 S", tx=MeterReadingReason.BEGIN
                )
            ],
        )
        end = create_test_payload(
            pagination="T2",
            readings=[
                create_test_reading(
                    timestamp="2023-01-01T11:00:00,000+0000 S", tx=MeterReadingReason.END
                )
            ],
        )
        issues = check_eichrecht_transaction(begin, end)
        assert_has_issue(issues, IssueCode.TIME_REGRESSION)

    def test_id_mismatch_warns(self) -> None:
        begin = create_test_payload(
            readings=[create_test_reading(tx=MeterReadingReason.BEGIN)],
            identification_type=IdentificationType.ISO14443,
            identification_data="12345678",
        )
        end = create_test_payload(
            pagination="T2",
            readings=[create_test_reading(tx=MeterReadingReason.END)],
            identification_type=IdentificationType.ISO14443,
            identification_data="87654321",
        )
        issues = check_eichrecht_transaction(begin, end)
        assert_has_issue(issues, IssueCode.ID_MISMATCH)


class TestValidateTransactionPair:
    """Tests for the validate_transaction_pair convenience function."""

    def test_valid_pair_passes(self) -> None:
        begin, end = create_transaction_pair()
        assert validate_transaction_pair(begin, end) is True

    def test_pagination_not_consecutive_fails(self) -> None:
        begin, end = create_transaction_pair(begin_pagination="T1", end_pagination="T5")
        assert validate_transaction_pair(begin, end) is False

    def test_pagination_consecutive_passes(self) -> None:
        begin, end = create_transaction_pair(begin_pagination="T3", end_pagination="T4")
        assert validate_transaction_pair(begin, end) is True

    def test_termination_tx_types_accepted(self) -> None:
        for tx_type in [
            MeterReadingReason.END,
            MeterReadingReason.TERMINATION_LOCAL,
            MeterReadingReason.TERMINATION_REMOTE,
            MeterReadingReason.TERMINATION_ABORT,
            MeterReadingReason.TERMINATION_POWER_FAILURE,
        ]:
            begin, end = create_transaction_pair()
            end.payload.RD[0].TX = tx_type
            assert validate_transaction_pair(begin, end) is True
