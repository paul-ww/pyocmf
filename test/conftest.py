import pathlib

import pytest

from pyocmf.core import OCMF, Payload
from pyocmf.core.reading import Reading

from .helpers import create_test_ocmf, create_test_payload, create_test_reading


@pytest.fixture
def test_data_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "resources" / "transparenzsoftware"


@pytest.fixture
def transparency_xml_dir(test_data_dir: pathlib.Path) -> pathlib.Path:
    return test_data_dir / "src" / "test" / "resources" / "xml"


@pytest.fixture
def transparency_xml_files(transparency_xml_dir: pathlib.Path) -> list[pathlib.Path]:
    return sorted([f for f in transparency_xml_dir.rglob("*.xml") if f.is_file()])


@pytest.fixture
def test_reading() -> Reading:
    """Fixture providing a basic test reading."""
    return create_test_reading()


@pytest.fixture
def test_payload() -> Payload:
    """Fixture providing a basic test payload."""
    return create_test_payload()


@pytest.fixture
def test_ocmf() -> OCMF:
    """Fixture providing a basic test OCMF."""
    return create_test_ocmf()
