import os
import pytest
import pathlib
from pyocmf.ocmf import OCMF


@pytest.fixture
def valid_xml_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent / "resources" / "ocmf" / "ok.xml"


def test_parse_ok_xml(valid_xml_path: pathlib.Path) -> None:
    # Adjust the path as needed based on your project structure
    assert os.path.exists(valid_xml_path), f"Test file not found: {valid_xml_path}"
    result = OCMF.from_xml(valid_xml_path)
    assert result, f"Parsing {valid_xml_path} failed"
