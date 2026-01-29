from __future__ import annotations

from pyocmf.compliance import validate_transaction_pair
from pyocmf.core.reading import MeterReadingReason

from ..helpers import create_transaction_pair


class TestTransactionPairValidation:
    def test_valid_transaction_pair(self) -> None:
        begin, end = create_transaction_pair()
        assert validate_transaction_pair(begin, end) is True

    def test_missing_readings_in_begin(self) -> None:
        begin, end = create_transaction_pair()
        begin.payload.RD = []
        assert validate_transaction_pair(begin, end) is False

    def test_wrong_begin_tx_type(self) -> None:
        begin, end = create_transaction_pair()
        begin.payload.RD[0].TX = MeterReadingReason.CHARGING
        assert validate_transaction_pair(begin, end) is False

    def test_wrong_end_tx_type(self) -> None:
        begin, end = create_transaction_pair()
        end.payload.RD[0].TX = MeterReadingReason.CHARGING
        assert validate_transaction_pair(begin, end) is False

    def test_serial_number_mismatch(self) -> None:
        begin, end = create_transaction_pair(begin_serial="12345", end_serial="99999")
        assert validate_transaction_pair(begin, end) is False

    def test_pagination_not_consecutive(self) -> None:
        begin, end = create_transaction_pair(begin_pagination="T1", end_pagination="T5")
        assert validate_transaction_pair(begin, end) is False

    def test_pagination_consecutive_passes(self) -> None:
        begin, end = create_transaction_pair(begin_pagination="T3", end_pagination="T4")
        assert validate_transaction_pair(begin, end) is True

    def test_timestamp_regression(self) -> None:
        begin, end = create_transaction_pair(
            begin_timestamp="2023-01-01T13:00:00,000+0000 S",
            end_timestamp="2023-01-01T12:00:00,000+0000 S",
        )
        assert validate_transaction_pair(begin, end) is False

    def test_value_regression(self) -> None:
        begin, end = create_transaction_pair(begin_value="100.0", end_value="50.0")
        assert validate_transaction_pair(begin, end) is False

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
