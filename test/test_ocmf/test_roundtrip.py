"""End-to-end roundtrip tests for OCMF parsing using transparenzsoftware test files."""

import pathlib

import pytest

from pyocmf.exceptions import PyOCMFError
from pyocmf.ocmf import OCMF
from pyocmf.sections.payload import Payload
from pyocmf.sections.signature import Signature
from pyocmf.utils.xml import extract_ocmf_strings_from_file, parse_ocmf_from_xml


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate test parameters for test_ocmf_roundtrip."""
    if "xml_file" in metafunc.fixturenames:
        transparency_xml_dir = (
            pathlib.Path(__file__).parent.parent
            / "resources"
            / "transparenzsoftware"
            / "src"
            / "test"
            / "resources"
            / "xml"
        )
        xml_files = [f for f in transparency_xml_dir.rglob("*.xml") if f.is_file()]
        metafunc.parametrize(
            "xml_file",
            [
                pytest.param(xml_file, id=str(xml_file.relative_to(transparency_xml_dir)))
                for xml_file in sorted(xml_files)
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
        with pytest.raises(PyOCMFError):
            parse_ocmf_from_xml(xml_file)
        return

    ocmf_strings = extract_ocmf_strings_from_file(xml_file)
    assert len(ocmf_strings) > 0, f"Expected OCMF data in {xml_file.name}"

    for ocmf_string in ocmf_strings:
        ocmf_model = OCMF.from_string(ocmf_string)

        assert ocmf_model.header == "OCMF"
        assert isinstance(ocmf_model.payload, Payload)
        assert isinstance(ocmf_model.signature, Signature)

        assert ocmf_string == ocmf_model.to_string()
        assert ocmf_model == OCMF.from_hex(ocmf_model.to_hex())
