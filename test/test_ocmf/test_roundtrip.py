"""End-to-end roundtrip tests for OCMF parsing using transparenzsoftware test files."""

import pathlib

import pytest

from pyocmf.ocmf import OCMF
from pyocmf.sections.payload import Payload
from pyocmf.sections.signature import Signature

from .helpers import parse_xml_with_expected_behavior, should_skip_xml_file


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate test parameters for test_ocmf_roundtrip."""
    if "xml_file" in metafunc.fixturenames:
        transparency_xml_dir = (
            metafunc.config.rootpath
            / "test"
            / "resources"
            / "transparenzsoftware"
            / "src"
            / "test"
            / "resources"
            / "xml"
        )
        xml_files = sorted([f for f in transparency_xml_dir.rglob("*.xml") if f.is_file()])
        metafunc.parametrize(
            "xml_file",
            [
                pytest.param(xml_file, id=str(xml_file.relative_to(transparency_xml_dir)))
                for xml_file in xml_files
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
    should_skip, skip_reason = should_skip_xml_file(xml_file)
    if should_skip:
        pytest.skip(skip_reason or "File should be skipped")

    container = parse_xml_with_expected_behavior(xml_file)

    if container is None:
        return

    assert len(container) > 0, f"Expected OCMF data in {xml_file.name}"

    for entry in container:
        ocmf_model = entry.ocmf

        assert ocmf_model.header == "OCMF"
        assert isinstance(ocmf_model.payload, Payload)
        assert isinstance(ocmf_model.signature, Signature)

        roundtrip_model = OCMF.from_string(ocmf_model.to_string(hex=True))

        assert ocmf_model.header == roundtrip_model.header
        assert ocmf_model.payload == roundtrip_model.payload
        assert ocmf_model.signature == roundtrip_model.signature
