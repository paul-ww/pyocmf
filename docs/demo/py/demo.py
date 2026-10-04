"""Analysis functions for the browser demo, called from JavaScript via Pyodide.

Each function returns a JSON string so the JavaScript side never handles Python objects.
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import warnings
from typing import TYPE_CHECKING, Any

import pyocmf
from pyocmf import (
    OCMF,
    IssueSeverity,
    OcmfContainer,
    PyOCMFError,
    SpecWarning,
    check_eichrecht_transaction,
)
from pyocmf.enums.reading import MeterReadingReason, is_end_reason

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyocmf.compliance import EichrechtIssue
    from pyocmf.core import Payload, Reading


def runtime_info() -> str:
    python = f"{sys.version_info.major}.{sys.version_info.minor}"
    return json.dumps({"python": python, "pyocmf": pyocmf.__version__})


def analyze_text(text: str, public_key: str | None, strict: bool) -> str:
    def parse() -> list[tuple[OCMF, str | None]]:
        return [(OCMF.from_string(text, strict=strict), public_key or None)]

    return _analyze(parse, given_key_source="input")


def analyze_xml(content: str, strict: bool) -> str:
    def parse() -> list[tuple[OCMF, str | None]]:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "upload.xml"
            path.write_text(content, encoding="utf-8")
            container = OcmfContainer.from_xml(path, strict=strict)
        return [
            (record.ocmf, record.public_key.key if record.public_key else None)
            for record in container
        ]

    return _analyze(parse, given_key_source="file")


def _analyze(parse: Callable[[], list[tuple[OCMF, str | None]]], given_key_source: str) -> str:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", SpecWarning)
        try:
            parsed = parse()
        except PyOCMFError as e:
            return json.dumps({"ok": False, "error": str(e), "errorType": type(e).__name__})

    deviations = _unique(str(w.message) for w in caught if issubclass(w.category, SpecWarning))
    records = [_record(ocmf, key, given_key_source) for ocmf, key in parsed]
    return json.dumps({
        "ok": True,
        "records": records,
        "transaction": _transaction([ocmf for ocmf, _ in parsed]),
        "specDeviations": deviations,
    })


def _record(ocmf: OCMF, public_key: str | None, given_key_source: str) -> dict[str, Any]:
    payload = ocmf.payload
    signature: dict[str, Any] = {"algorithm": _text(ocmf.signature.SA), "status": "unchecked"}
    # A key appended to the OCMF string (as in QR codes) is used when none is given
    key = public_key or ocmf.embedded_public_key
    signature["keySource"] = given_key_source if public_key else "record" if key else None
    if key:
        try:
            valid = ocmf.verify_signature(key)
            signature["status"] = "valid" if valid else "invalid"
        except (PyOCMFError, ImportError) as e:
            signature.update(status="error", message=str(e))

    return {
        "gateway": " · ".join(v for v in (payload.GI, payload.GS) if v) or None,
        "meter": " · ".join(v for v in (payload.MV, payload.MM, payload.MS) if v) or None,
        "pagination": payload.PG,
        "identification": _identification(payload),
        "signature": signature,
        "issues": _issues(ocmf.check_eichrecht()),
        "energy": _energy(payload.RD),
        "readings": [_reading(r) for r in payload.RD],
    }


def _transaction(records: list[OCMF]) -> dict[str, Any] | None:
    begins = [o for o in records if _has_begin(o.payload) and not _has_end(o.payload)]
    ends = [o for o in records if _has_end(o.payload) and not _has_begin(o.payload)]
    if not begins or not ends:
        return None
    begin, end = begins[0].payload, ends[-1].payload
    return {
        "pagination": [begin.PG, end.PG],
        "issues": _issues(check_eichrecht_transaction(begin, end)),
        "energy": _energy([*begin.RD, *end.RD]),
    }


def _has_begin(payload: Payload) -> bool:
    return any(r.TX == MeterReadingReason.BEGIN for r in payload.RD)


def _has_end(payload: Payload) -> bool:
    return any(is_end_reason(r.TX) for r in payload.RD)


def _energy(readings: list[Reading]) -> dict[str, Any] | None:
    relevant = [r for r in readings if r.RI is not None and r.RI.is_law_relevant]
    begin = next((r for r in relevant if r.TX == MeterReadingReason.BEGIN), None)
    end = next((r for r in reversed(relevant) if is_end_reason(r.TX)), None)
    if begin is None or end is None or begin.RV is None or end.RV is None or begin.RU != end.RU:
        return None
    try:
        seconds = int((end.timestamp - begin.timestamp).total_seconds())
    except TypeError:
        seconds = None
    return {
        "value": str(end.RV - begin.RV),
        "unit": _text(begin.RU),
        "seconds": seconds,
    }


def _issues(issues: list[EichrechtIssue]) -> list[dict[str, str | None]]:
    ordered = sorted(issues, key=lambda i: i.severity != IssueSeverity.ERROR)
    return [
        {
            "severity": issue.severity.value,
            "code": issue.code.value,
            "field": issue.field,
            "message": issue.message,
        }
        for issue in ordered
    ]


def _reading(reading: Reading) -> dict[str, str | None]:
    return {
        "tx": _text(reading.TX),
        "time": reading.TM.timestamp.isoformat(sep=" "),
        "sync": _text(reading.time_status),
        "value": str(reading.RV) if reading.RV is not None else None,
        "unit": _text(reading.RU),
        "register": str(reading.RI) if reading.RI is not None else None,
        "status": _text(reading.ST),
        "errorFlags": reading.EF,
    }


def _identification(payload: Payload) -> str | None:
    if payload.ID:
        return f"{_text(payload.IT)} {payload.ID}"
    return _text(payload.IT)


def _text(value: object) -> str | None:
    return None if value is None else str(value)


def _unique(values: Any) -> list[str]:
    return list(dict.fromkeys(values))
