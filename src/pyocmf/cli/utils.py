"""Utility functions for CLI."""

from __future__ import annotations

import contextlib
import pathlib
import warnings
from enum import StrEnum
from typing import TYPE_CHECKING

from pyocmf.cli.display import console
from pyocmf.constants import OCMF_PREFIX
from pyocmf.core.ocmf import OCMF
from pyocmf.utils.xml import OcmfContainer

if TYPE_CHECKING:
    from collections.abc import Generator


class InputType(StrEnum):
    XML = "xml"
    OCMF_STRING = "ocmf_string"


def detect_input_type(ocmf_input: str) -> InputType:
    """Detect input type from string."""
    if ocmf_input.startswith(OCMF_PREFIX):
        return InputType.OCMF_STRING

    try:
        path = pathlib.Path(ocmf_input)
        if path.exists() and path.is_file():
            return InputType.XML
    except (OSError, ValueError):
        pass

    if ocmf_input.endswith(".xml") or "/" in ocmf_input or "\\" in ocmf_input:
        raise FileNotFoundError(ocmf_input)

    return InputType.OCMF_STRING


@contextlib.contextmanager
def _printed_warnings() -> Generator[None]:
    """Show warnings raised while parsing (e.g. spec deviations) as console lines."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            yield
        finally:
            for message in dict.fromkeys(str(w.message) for w in caught):
                console.print(f"[yellow]⚠[/yellow] {message}")


def parse_ocmf_string(ocmf_input: str, *, strict: bool = False) -> OCMF:
    with _printed_warnings():
        return OCMF.from_string(ocmf_input, strict=strict)


def load_xml_container(xml_path: str, *, strict: bool = False) -> OcmfContainer:
    """Load and validate XML file, returning container with OCMF records."""
    path = pathlib.Path(xml_path)
    if not path.exists():
        raise FileNotFoundError(xml_path)
    with _printed_warnings():
        return OcmfContainer.from_xml(path, strict=strict)


def load_ocmf(ocmf_input: str, *, strict: bool = False) -> OCMF:
    """Load OCMF from string or file, handling both formats."""
    input_type = detect_input_type(ocmf_input)

    if input_type == InputType.XML:
        container = load_xml_container(ocmf_input, strict=strict)
        return container[0].ocmf

    return parse_ocmf_string(ocmf_input, strict=strict)
