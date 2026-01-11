import pathlib

import pytest


@pytest.fixture
def test_data_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "resources" / "transparenzsoftware"


@pytest.fixture
def transparency_xml_dir(test_data_dir: pathlib.Path) -> pathlib.Path:
    return test_data_dir / "src" / "test" / "resources" / "xml"


@pytest.fixture
def transparency_xml_files(transparency_xml_dir: pathlib.Path) -> list[pathlib.Path]:
    return sorted([f for f in transparency_xml_dir.rglob("*.xml") if f.is_file()])
