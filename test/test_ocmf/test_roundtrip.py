"""End-to-end roundtrip tests for OCMF parsing using transparenzsoftware test files."""

import pathlib
import xml.etree.ElementTree as ET
from typing import List

import pytest

from pyocmf.exceptions import (
    PyOCMFError,
)
from pyocmf.ocmf import OCMF
from pyocmf.xml_parser import extract_ocmf_strings_from_xml, parse_ocmf_from_xml


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
def transparency_xml_files(transparency_xml_dir: pathlib.Path) -> List[pathlib.Path]:
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

    # Files that should NOT contain OCMF data
    if (
        any(keyword in file_name_lower for keyword in ["metra", "edl", "isa-edl"])
        or parent_dir == "emh-emoc"
        or "invalid" in file_name_lower
        or "mennekes" in file_name_lower
        or "wirelane" in file_name_lower
        or "template" in file_name_lower
        or "test_input_xml_two_values" in file_name_lower
    ):
        # Verify these correctly raise exceptions
        with pytest.raises((PyOCMFError, ET.ParseError)):
            parse_ocmf_from_xml(xml_file)
        return

    # Files with unsupported OCMF features (skip for now)
    if (
        "rsa" in file_name_lower
        or "ocmf-receipt-with_import_and_export" in file_name_lower
        or "ocmf-receipt-with_publickey_and_data" in file_name_lower
    ):
        pytest.skip("Skipping unsupported OCMF feature file")
        return

    # Valid OCMF files - test parsing and roundtripping
    ocmf_strings = extract_ocmf_strings_from_xml(xml_file)
    assert len(ocmf_strings) > 0, f"Expected OCMF data in {xml_file.name}"

    for i, ocmf_string in enumerate(ocmf_strings):
        # Parse the OCMF string
        ocmf_model = OCMF.from_string(ocmf_string)

        # Verify basic structure
        assert ocmf_model.header == "OCMF"
        assert ocmf_model.payload is not None
        assert ocmf_model.signature is not None

        # Roundtrip: serialize and re-parse
        reconstructed_string = ocmf_model.to_string()
        ocmf_model_2 = OCMF.from_string(reconstructed_string)

        # Verify models are identical
        assert (
            ocmf_model.model_dump() == ocmf_model_2.model_dump()
        ), f"Roundtrip failed for OCMF string {i+1} in {xml_file.name}"


def test_ocmf_summary(transparency_xml_files: List[pathlib.Path]) -> None:
    """Summary test that counts all OCMF strings found across all files."""
    total_files = 0
    total_ocmf_strings = 0
    successful_roundtrips = 0

    for xml_file in transparency_xml_files:
        try:
            ocmf_strings = extract_ocmf_strings_from_xml(xml_file)
            if ocmf_strings:
                total_files += 1
                total_ocmf_strings += len(ocmf_strings)

                for ocmf_string in ocmf_strings:
                    try:
                        ocmf_model = OCMF.from_string(ocmf_string)
                        reconstructed = ocmf_model.to_string()
                        OCMF.from_string(reconstructed)
                        successful_roundtrips += 1
                    except Exception:
                        pass
        except Exception:
            pass

    print("\n=== OCMF Test Summary ===")
    print(f"Files with OCMF data: {total_files}")
    print(f"Total OCMF strings: {total_ocmf_strings}")
    print(f"Successful roundtrips: {successful_roundtrips}")

    assert total_ocmf_strings > 0, "No OCMF strings found in test files"
    assert successful_roundtrips > 0, "No successful roundtrips"

    # We expect high success rate
    success_rate = successful_roundtrips / total_ocmf_strings
    assert success_rate > 0.95, f"Success rate too low: {success_rate:.1%}"


def test_deprecated_from_xml_api() -> None:
    """Verify the deprecated OCMF.from_xml() method still works."""
    xml_path = (
        pathlib.Path(__file__).parent.parent
        / "resources"
        / "transparenzsoftware"
        / "src"
        / "test"
        / "resources"
        / "xml"
        / "ocmf_sec.xml"
    )

    # Test deprecated method
    with pytest.warns(DeprecationWarning, match="OCMF.from_xml\\(\\) is deprecated"):
        result_deprecated = OCMF.from_xml(xml_path)

    # Test new method
    result_new = parse_ocmf_from_xml(xml_path)

    # Both should produce the same result
    assert result_deprecated.model_dump() == result_new.model_dump()
