import os
import pytest
import pathlib
from pyocmf.ocmf import OCMF
from pyocmf.transparency import TransparencyXML
from pyocmf.xml_parser import parse_ocmf_from_xml


@pytest.fixture
def valid_xml_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent / "resources" / "ocmf" / "ok.xml"


def test_parse_ok_xml(valid_xml_path: pathlib.Path) -> None:
    # Test the new XML parsing function
    assert os.path.exists(valid_xml_path), f"Test file not found: {valid_xml_path}"
    result = parse_ocmf_from_xml(valid_xml_path)
    assert result, f"Parsing {valid_xml_path} failed"
    
    # Test that the deprecated method still works
    result_deprecated = OCMF.from_xml(valid_xml_path)
    assert result_deprecated, f"Parsing {valid_xml_path} with deprecated method failed"
    
    # Both results should be equal
    assert result.model_dump() == result_deprecated.model_dump()


def test_transparencyxml_parse(valid_xml_path: pathlib.Path) -> None:
    tps = TransparencyXML(valid_xml_path)
    datasets = tps.get_datasets()
    assert len(datasets) == 2, "Should parse two <value> elements"
    signed_data = tps.get_signed_data(format_filter="OCMF")
    assert len(signed_data) == 2, "Should find two OCMF signedData elements"
    public_keys = tps.get_public_keys()
    assert len(public_keys) == 2, "Should find two publicKey elements"
    for sd in signed_data:
        assert sd.text is not None, "signedData text should not be None"
        assert sd.text.startswith("OCMF|"), "signedData text should start with 'OCMF|'"
