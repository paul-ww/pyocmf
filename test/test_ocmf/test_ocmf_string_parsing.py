"""Test script to extract and parse all OCMF strings from XML files."""

import pathlib
import pytest
from typing import List
from pyocmf.xml_parser import extract_ocmf_strings_from_xml
from pyocmf.ocmf import OCMF


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
    xml_files = []
    for file_path in transparency_xml_dir.rglob("*.xml"):
        if file_path.is_file():
            xml_files.append(file_path)
    return sorted(xml_files)


def test_extract_all_ocmf_strings_from_xml_files(transparency_xml_files: List[pathlib.Path]) -> None:
    """Extract all OCMF strings from XML files and test parsing them."""
    all_ocmf_strings = []
    successful_parses = 0
    failed_parses = 0
    
    for xml_file in transparency_xml_files:
        try:
            ocmf_strings = extract_ocmf_strings_from_xml(xml_file)
            if ocmf_strings:
                rel_path = xml_file.relative_to(
                    pathlib.Path(__file__).parent.parent / "resources" / "transparenzsoftware"
                )
                print(f"Found {len(ocmf_strings)} OCMF strings in {rel_path}")
                
                for i, ocmf_string in enumerate(ocmf_strings):
                    all_ocmf_strings.append((xml_file, i, ocmf_string))
                    
                    try:
                        ocmf_model = OCMF.from_string(ocmf_string)
                        successful_parses += 1
                        
                        # Test round-trip: convert back to string and parse again
                        reconstructed_string = ocmf_model.to_string()
                        OCMF.from_string(reconstructed_string)
                        
                    except Exception as e:
                        failed_parses += 1
                        print(f"  ✗ Failed to parse OCMF string {i+1}: {e}")
                        
        except Exception:
            # Skip files that can't be parsed as XML
            pass
    
    print("\nSummary:")
    print(f"Total OCMF strings found: {len(all_ocmf_strings)}")
    print(f"Successfully parsed: {successful_parses}")
    print(f"Failed to parse: {failed_parses}")
    
    # At least some OCMF strings should be found and parsed successfully
    assert len(all_ocmf_strings) > 0, "No OCMF strings found in any XML files"
    assert successful_parses > 0, "No OCMF strings could be parsed successfully"


def test_keba_test_xml_specific():
    """Test the specific keba_test.xml file that was provided."""
    xml_path = (
        pathlib.Path(__file__).parent.parent
        / "resources"
        / "transparenzsoftware"
        / "src"
        / "test"
        / "resources"
        / "xml"
        / "keba_test.xml"
    )
    
    if not xml_path.exists():
        pytest.skip(f"keba_test.xml not found at {xml_path}")
    
    ocmf_strings = extract_ocmf_strings_from_xml(xml_path)
    
    # The keba_test.xml should have multiple OCMF strings
    assert len(ocmf_strings) > 0, "No OCMF strings found in keba_test.xml"
    
    # Test parsing each OCMF string
    for i, ocmf_string in enumerate(ocmf_strings):
        ocmf_model = OCMF.from_string(ocmf_string)
        
        # Basic validation
        assert ocmf_model.header == "OCMF"
        assert ocmf_model.payload is not None
        assert ocmf_model.signature is not None
        
        # Test round-trip
        reconstructed = ocmf_model.to_string()
        ocmf_model_2 = OCMF.from_string(reconstructed)
        
        # Models should be equal
        assert ocmf_model.model_dump() == ocmf_model_2.model_dump()
        
        print(f"✓ Successfully parsed and round-tripped OCMF string {i+1}")


def test_ocmf_string_parsing_basic():
    """Test basic OCMF string parsing functionality."""
    # This is an example OCMF string - we'll create a simple one for testing
    ocmf_string = 'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"16913115","GV":"2080000","PG":"T12345","IS":false,"IF":[],"ID":"","RD":[{"TM":"2023-01-01T12:00:00,000+0100 U","TX":"B","EF":"","ST":"G","RV":1234.56,"RI":"1-b:1.8.0","RU":"kWh"}]}|{"SD":"3046022100E09BE3AB97B453FDB9643079108005436724A84DF2B299F219A92BCC2F021F23022100E01212F1CDCD4A8DCAD157FD69E4CACF18272D4093A9C5D59B9E67F0846F1312"}'
    
    # Test parsing
    ocmf_model = OCMF.from_string(ocmf_string)
    
    assert ocmf_model.header == "OCMF"
    assert ocmf_model.payload.FV == "1.0"
    assert ocmf_model.payload.GI == "KEBA_KCP30"
    assert ocmf_model.payload.GS == "16913115"
    assert len(ocmf_model.payload.RD) == 1
    
    # Test round-trip
    reconstructed = ocmf_model.to_string()
    ocmf_model_2 = OCMF.from_string(reconstructed)
    
    assert ocmf_model.model_dump() == ocmf_model_2.model_dump()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
