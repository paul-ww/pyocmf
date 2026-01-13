"""Utility functions for CLI."""

from __future__ import annotations

import pathlib
from enum import StrEnum

from pyocmf.constants import OCMF_PREFIX
from pyocmf.core.ocmf import OCMF
from pyocmf.utils.xml import OcmfContainer


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


def load_xml_container(xml_path: str) -> OcmfContainer:
    """Load and validate XML file, returning container with OCMF records."""
    path = pathlib.Path(xml_path)
    if not path.exists():
        raise FileNotFoundError(xml_path)
    return OcmfContainer.from_xml(path)


def load_ocmf(ocmf_input: str) -> OCMF:
    """Load OCMF from string or file, handling both formats."""
    input_type = detect_input_type(ocmf_input)

    if input_type == InputType.XML:
        container = load_xml_container(ocmf_input)
        return container[0].ocmf

    return OCMF.from_string(ocmf_input)
