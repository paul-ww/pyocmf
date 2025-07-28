import pathlib
import pytest
from typing import List
from pyocmf.ocmf import OCMF


@pytest.fixture
def transparency_xml_dir() -> pathlib.Path:
    """Return the path to the transparency XML test files directory."""
    return pathlib.Path(__file__).parent.parent / "resources" / "transparency_xml"


@pytest.fixture
def transparency_xml_files(transparency_xml_dir: pathlib.Path) -> List[pathlib.Path]:
    """Return a list of all XML files in the transparency XML directory."""
    xml_files = []
    for file_path in transparency_xml_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == '.xml':
            xml_files.append(file_path)
    return sorted(xml_files)  # Sort for consistent test order


@pytest.mark.parametrize("xml_file", [
    pytest.param(xml_file, id=xml_file.name) 
    for xml_file in (pathlib.Path(__file__).parent.parent / "resources" / "transparency_xml").iterdir()
    if xml_file.is_file() and xml_file.suffix.lower() == '.xml'
])
def test_transparency_xml_file_parsing(xml_file: pathlib.Path) -> None:
    """Test that each transparency XML file can be parsed into an OCMF model.
    
    This test will help identify which files fail parsing and why.
    """
    assert xml_file.exists(), f"Test file not found: {xml_file}"
    
    try:
        result = OCMF.from_xml(xml_file)
        assert result is not None, f"Parsing {xml_file.name} returned None"
        assert result.header == "OCMF", f"Expected header 'OCMF', got '{result.header}'"
        assert result.payload is not None, f"Payload is None for {xml_file.name}"
        assert result.signature is not None, f"Signature is None for {xml_file.name}"
        print(f"✓ Successfully parsed {xml_file.name}")
        
    except Exception as e:
        pytest.fail(f"Failed to parse {xml_file.name}: {type(e).__name__}: {e}")


def test_all_transparency_files_exist(transparency_xml_files: List[pathlib.Path]) -> None:
    """Verify that we have transparency XML files to test."""
    assert len(transparency_xml_files) > 0, "No XML files found in transparency_xml directory"
    print(f"Found {len(transparency_xml_files)} XML files to test:")
    for xml_file in transparency_xml_files:
        print(f"  - {xml_file.name}")


def test_transparency_files_summary(transparency_xml_files: List[pathlib.Path]) -> None:
    """Provide a summary of which files can be parsed successfully."""
    successful_files = []
    failed_files = []
    
    for xml_file in transparency_xml_files:
        try:
            result = OCMF.from_xml(xml_file)
            if result is not None:
                successful_files.append(xml_file.name)
            else:
                failed_files.append((xml_file.name, "Returned None"))
        except Exception as e:
            failed_files.append((xml_file.name, f"{type(e).__name__}: {e}"))
    
    print("\n=== PARSING SUMMARY ===")
    print(f"Total files: {len(transparency_xml_files)}")
    print(f"Successful: {len(successful_files)}")
    print(f"Failed: {len(failed_files)}")
    
    if successful_files:
        print("\n✓ Successfully parsed files:")
        for filename in successful_files:
            print(f"  - {filename}")
    
    if failed_files:
        print("\n✗ Failed to parse files:")
        for filename, error in failed_files:
            print(f"  - {filename}: {error}")
    
    # This test always passes - it's just for reporting
    assert True
