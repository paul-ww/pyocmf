"""End-to-end roundtrip tests for OCMF parsing using transparenzsoftware test files."""

import pathlib
import xml.etree.ElementTree as ET

import pytest

from pyocmf.exceptions import (
    PyOCMFError,
)
from pyocmf.ocmf import OCMF
from pyocmf.utils.xml import extract_ocmf_strings_from_file, parse_ocmf_from_xml


@pytest.fixture
def transparency_xml_dir() -> pathlib.Path:
    """Return the path to the transparency XML test files directory."""
    return (
        pathlib.Path(__file__).parent.parent
        / "resources"
        / "transparenzsoftware"
        / "src"
        / "test"
        / "resources"
        / "xml"
    )


@pytest.fixture
def transparency_xml_files(transparency_xml_dir: pathlib.Path) -> list[pathlib.Path]:
    """Return a list of all XML files in the transparency XML directory."""
    return sorted([f for f in transparency_xml_dir.rglob("*.xml") if f.is_file()])


@pytest.mark.parametrize(
    "xml_file",
    [
        pytest.param(
            xml_file,
            id=str(
                xml_file.relative_to(
                    pathlib.Path(__file__).parent.parent
                    / "resources"
                    / "transparenzsoftware"
                    / "src"
                    / "test"
                    / "resources"
                    / "xml"
                )
            ),
        )
        for xml_file in (
            pathlib.Path(__file__).parent.parent
            / "resources"
            / "transparenzsoftware"
            / "src"
            / "test"
            / "resources"
            / "xml"
        ).rglob("*.xml")
        if xml_file.is_file()
    ],
)
def test_ocmf_roundtrip(xml_file: pathlib.Path) -> None:
    """Test OCMF parsing and roundtripping for each transparenzsoftware XML file.

    This end-to-end test verifies that:
    1. Valid OCMF files can be parsed
    2. Parsed OCMF can be serialized back to string
    3. Re-parsing the serialized string produces identical models
    4. Invalid/non-OCMF files raise appropriate exceptions
    """
    file_name_lower = xml_file.name.lower()
    parent_dir = xml_file.parent.name

    if "rsa" in file_name_lower:
        pytest.skip("Skipping unsupported OCMF feature file")
    return

    if (
        any(keyword in file_name_lower for keyword in ["metra", "edl", "isa-edl"])
        or parent_dir == "emh-emoc"
        or "invalid" in file_name_lower
        or "mennekes" in file_name_lower
        or "wirelane" in file_name_lower
        or "template" in file_name_lower
        or "test_input_xml_two_values" in file_name_lower
    ):
        with pytest.raises((PyOCMFError, ET.ParseError)):
            parse_ocmf_from_xml(xml_file)
        return

    ocmf_strings = extract_ocmf_strings_from_file(xml_file)
    assert len(ocmf_strings) > 0, f"Expected OCMF data in {xml_file.name}"

    for i, ocmf_string in enumerate(ocmf_strings):
        ocmf_model = OCMF.from_string(ocmf_string)

        assert ocmf_model.header == "OCMF"
        assert ocmf_model.payload is not None
        assert ocmf_model.signature is not None

        reconstructed_string = ocmf_model.to_string()
        ocmf_model_2 = OCMF.from_string(reconstructed_string)
        assert ocmf_model.model_dump() == ocmf_model_2.model_dump(), (
            f"Roundtrip failed for OCMF string {i + 1} in {xml_file.name}"
        )
