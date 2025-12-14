"""Shared pytest fixtures for all tests."""

import pathlib

import pytest


@pytest.fixture
def test_data_dir() -> pathlib.Path:
    """Return path to test data directory."""
    return pathlib.Path(__file__).parent / "resources" / "transparenzsoftware"


@pytest.fixture
def transparency_xml_dir(test_data_dir: pathlib.Path) -> pathlib.Path:
    """Return the path to the transparency XML test files directory."""
    return test_data_dir / "src" / "test" / "resources" / "xml"


@pytest.fixture
def transparency_xml_files(transparency_xml_dir: pathlib.Path) -> list[pathlib.Path]:
    """Return a list of all XML files in the transparency XML directory."""
    return sorted([f for f in transparency_xml_dir.rglob("*.xml") if f.is_file()])
