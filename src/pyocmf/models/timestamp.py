from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from pyocmf.enums.reading import TimeStatus
from pyocmf.types.lenient import warn_spec


@dataclass(frozen=True)
class OCMFTimestamp:
    timestamp: datetime
    status: TimeStatus | str

    def __str__(self) -> str:
        return self.serialize()

    @classmethod
    def from_string(cls, timestamp_str: str) -> OCMFTimestamp:
        """Parse OCMF timestamp string to OCMFTimestamp.

        OCMF format: "2023-06-15T14:30:45,123+0200 S" (note: comma for milliseconds).
        """
        if " " in timestamp_str:
            ts_part, status_part = timestamp_str.rsplit(" ", 1)
            status = _parse_time_status(status_part)
        else:
            ts_part = timestamp_str
            status = TimeStatus.UNKNOWN_OR_UNSYNCHRONIZED

        ts_normalized = ts_part.replace(",", ".")
        dt = datetime.fromisoformat(ts_normalized)

        return cls(timestamp=dt, status=status)

    def serialize(self) -> str:
        """Serialize to OCMF timestamp format.

        Uses comma for milliseconds and a colon-free timezone offset (e.g. +0200)
        as required by the OCMF spec.
        """
        if self.timestamp.tzinfo is None:
            error_message = "Datetime must be timezone-aware for OCMF format"
            raise ValueError(error_message)

        iso_str = self.timestamp.isoformat(timespec="milliseconds")
        ocmf_str = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", iso_str.replace(".", ","))

        return f"{ocmf_str} {self.status}"


def _parse_time_status(value: str) -> TimeStatus | str:
    try:
        return TimeStatus(value)
    except ValueError:
        warn_spec(f"Time status '{value}' is not defined by the OCMF spec (U, I, S, R)")
        return value
