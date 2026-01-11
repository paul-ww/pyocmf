from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from pydantic.types import StringConstraints

from pyocmf.enums.reading import TimeStatus

OCMFTimeFormat = Annotated[
    str,
    StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2},\d{3}[+-]\d{4} [UISR]$"),
]


@dataclass(frozen=True)
class OCMFTimestamp:
    timestamp: datetime
    status: TimeStatus

    def __str__(self) -> str:
        return serialize_ocmf_timestamp(self.timestamp, self.status)

    @classmethod
    def from_string(cls, timestamp_str: str) -> OCMFTimestamp:
        dt, status = parse_ocmf_timestamp(timestamp_str)
        return cls(timestamp=dt, status=status)


def parse_ocmf_timestamp(timestamp_str: str) -> tuple[datetime, TimeStatus]:
    """Parse OCMF timestamp string to datetime and status.

    OCMF format: "2023-06-15T14:30:45,123+0200 S" (note: comma for milliseconds, not period).
    """
    if " " in timestamp_str:
        ts_part, status_part = timestamp_str.rsplit(" ", 1)
        status = TimeStatus(status_part)
    else:
        ts_part = timestamp_str
        status = TimeStatus.UNKNOWN_OR_UNSYNCHRONIZED

    ts_normalized = ts_part.replace(",", ".")

    dt = datetime.fromisoformat(ts_normalized)

    return dt, status


def serialize_ocmf_timestamp(dt: datetime, status: TimeStatus = TimeStatus.SYNCHRONIZED) -> str:
    """Serialize datetime to OCMF timestamp format.

    Requires timezone-aware datetime. Uses comma for milliseconds (OCMF requirement).
    """
    if dt.tzinfo is None:
        error_message = "Datetime must be timezone-aware for OCMF format"
        raise ValueError(error_message)

    iso_str = dt.isoformat(timespec="milliseconds")

    ocmf_str = iso_str.replace(".", ",")

    return f"{ocmf_str} {status.value}"
