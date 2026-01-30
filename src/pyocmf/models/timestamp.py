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
        return self.serialize()

    @classmethod
    def from_string(cls, timestamp_str: str) -> OCMFTimestamp:
        """Parse OCMF timestamp string to OCMFTimestamp.

        OCMF format: "2023-06-15T14:30:45,123+0200 S" (note: comma for milliseconds).
        """
        if " " in timestamp_str:
            ts_part, status_part = timestamp_str.rsplit(" ", 1)
            status = TimeStatus(status_part)
        else:
            ts_part = timestamp_str
            status = TimeStatus.UNKNOWN_OR_UNSYNCHRONIZED

        ts_normalized = ts_part.replace(",", ".")
        dt = datetime.fromisoformat(ts_normalized)

        return cls(timestamp=dt, status=status)

    def serialize(self) -> str:
        """Serialize to OCMF timestamp format.

        Uses comma for milliseconds as required by OCMF spec.
        """
        if self.timestamp.tzinfo is None:
            error_message = "Datetime must be timezone-aware for OCMF format"
            raise ValueError(error_message)

        iso_str = self.timestamp.isoformat(timespec="milliseconds")
        ocmf_str = iso_str.replace(".", ",")

        return f"{ocmf_str} {self.status.value}"
