from __future__ import annotations

import datetime

import pytest

from pyocmf.enums.reading import TimeStatus
from pyocmf.exceptions import SpecWarning
from pyocmf.models.timestamp import OCMFTimestamp


class TestOCMFTimestamp:
    def test_parses_fields_and_offset(self) -> None:
        # ReadingTest.testTimestampParsing in the Transparenzsoftware
        ts = OCMFTimestamp.from_string("2018-07-24T13:22:04,000+0200 S")
        assert ts.timestamp == datetime.datetime(
            2018, 7, 24, 13, 22, 4, tzinfo=datetime.timezone(datetime.timedelta(hours=2))
        )
        assert ts.status == TimeStatus.SYNCHRONIZED

    def test_parses_milliseconds(self) -> None:
        ts = OCMFTimestamp.from_string("2018-07-24T13:22:04,123+0000 I")
        assert ts.timestamp.microsecond == 123_000

    @pytest.mark.parametrize("status", list(TimeStatus))
    def test_parses_every_time_status(self, status: TimeStatus) -> None:
        ts = OCMFTimestamp.from_string(f"2018-07-24T13:22:04,000+0200 {status.value}")
        assert ts.status == status

    def test_missing_status_defaults_to_unknown(self) -> None:
        ts = OCMFTimestamp.from_string("2018-07-24T13:22:04,000+0200")
        assert ts.status == TimeStatus.UNKNOWN_OR_UNSYNCHRONIZED

    def test_unknown_time_status_warns(self) -> None:
        # The Transparenzsoftware treats unknown letters as "unknown" synchronicity
        with pytest.warns(SpecWarning, match="Time status 'Y'"):
            ts = OCMFTimestamp.from_string("2018-07-24T13:22:04,000+0200 Y")
        assert ts.status == "Y"
        assert str(ts) == "2018-07-24T13:22:04,000+0200 Y"

    def test_rejects_non_iso_datetime(self) -> None:
        with pytest.raises(ValueError, match="isoformat"):
            OCMFTimestamp.from_string("24.07.2018 13:22:04 S")

    def test_serializes_without_offset_colon(self) -> None:
        raw = "2018-07-24T13:22:04,000+0200 S"
        assert str(OCMFTimestamp.from_string(raw)) == raw

    def test_serialize_rejects_naive_datetime(self) -> None:
        ts = OCMFTimestamp(
            timestamp=datetime.datetime(2018, 7, 24, 13, 22, 4),  # ruff: ignore[call-datetime-without-tzinfo]
            status=TimeStatus.SYNCHRONIZED,
        )
        with pytest.raises(ValueError, match="timezone-aware"):
            ts.serialize()
