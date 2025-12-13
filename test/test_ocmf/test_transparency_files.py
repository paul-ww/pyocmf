import pathlib
import xml.etree.ElementTree as ET
from typing import List

import pytest

from pyocmf.xml_parser import parse_ocmf_from_xml


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
    """Return a list of all XML files in the transparency XML directory, including subdirectories."""
    xml_files = []
    # Use rglob to recursively find all XML files
    for file_path in transparency_xml_dir.rglob("*.xml"):
        if file_path.is_file():
            xml_files.append(file_path)
    return sorted(xml_files)  # Sort for consistent test order


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
def test_transparency_xml_file_parsing(xml_file: pathlib.Path) -> None:
    """Test that each transparency XML file can be parsed into an OCMF model.

    This test will help identify which files fail parsing and why.
    Note: Not all files in the transparency software repository are OCMF files,
    so some failures are expected for non-OCMF formats.
    """
    assert xml_file.exists(), f"Test file not found: {xml_file}"

    # Get relative path for better error messages
    rel_path = xml_file.relative_to(
        pathlib.Path(__file__).parent.parent
        / "resources"
        / "transparenzsoftware"
        / "src"
        / "test"
        / "resources"
        / "xml"
    )

    file_name_lower = xml_file.name.lower()
    parent_dir = xml_file.parent.name

    # Known non-OCMF file patterns - verify they raise appropriate exceptions
    if (
        any(keyword in file_name_lower for keyword in ["metra", "edl", "isa-edl"])
        or parent_dir == "emh-emoc"
        or "invalid" in file_name_lower
        or "mennekes" in file_name_lower  # Mennekes proprietary format
        or "wirelane" in file_name_lower  # Wirelane proprietary format
        or "template" in file_name_lower  # Empty template files
        or "test_input_xml_two_values" in file_name_lower  # Non-OCMF test file
    ):
        # These files should raise ValueError or ParseError when parsing
        with pytest.raises((ValueError, ET.ParseError)):
            parse_ocmf_from_xml(xml_file)
        print(f"✓ Correctly rejected non-OCMF file {rel_path}")
    elif (
        "rsa" in file_name_lower  # cannot deal with RSA yet
        or "ocmf-receipt-with_import_and_export" in file_name_lower
        or "ocmf-receipt-with_publickey_and_data" in file_name_lower
    ):
        # These are OCMF files but have unsupported features
        pytest.skip(f"Skipping unsupported content file {rel_path}")
    else:
        # These should be valid OCMF files
        result = parse_ocmf_from_xml(xml_file)
        assert result is not None, f"Parsing {rel_path} returned None"
        assert result.header == "OCMF", f"Expected header 'OCMF', got '{result.header}'"
        assert result.payload is not None, f"Payload is None for {rel_path}"
        assert result.signature is not None, f"Signature is None for {rel_path}"
        print(f"✓ Successfully parsed {rel_path}")


def test_all_transparency_files_exist(
    transparency_xml_files: List[pathlib.Path],
) -> None:
    """Verify that we have transparency XML files to test."""
    assert (
        len(transparency_xml_files) > 0
    ), "No XML files found in transparency_xml directory"

    base_dir = (
        pathlib.Path(__file__).parent.parent
        / "resources"
        / "transparenzsoftware"
        / "src"
        / "test"
        / "resources"
        / "xml"
    )

    print(f"Found {len(transparency_xml_files)} XML files to test:")

    # Group files by directory for better organization
    files_by_dir: dict[str, list[str]] = {}
    for xml_file in transparency_xml_files:
        rel_path = xml_file.relative_to(base_dir)
        dir_name = (
            str(rel_path.parent) if rel_path.parent != pathlib.Path(".") else "root"
        )
        if dir_name not in files_by_dir:
            files_by_dir[dir_name] = []
        files_by_dir[dir_name].append(rel_path.name)

    for dir_name in sorted(files_by_dir.keys()):
        if dir_name == "root":
            print("  Root directory:")
        else:
            print(f"  {dir_name}/:")
        for filename in sorted(files_by_dir[dir_name]):
            print(f"    - {filename}")


def test_transparency_files_summary(transparency_xml_files: List[pathlib.Path]) -> None:
    """Provide a summary of which files can be parsed successfully."""
    successful_files = []
    failed_files = []
    skipped_files = []

    base_dir = (
        pathlib.Path(__file__).parent.parent
        / "resources"
        / "transparenzsoftware"
        / "src"
        / "test"
        / "resources"
        / "xml"
    )

    for xml_file in transparency_xml_files:
        rel_path = xml_file.relative_to(base_dir)
        file_name_lower = xml_file.name.lower()
        parent_dir = xml_file.parent.name

        try:
            result = parse_ocmf_from_xml(xml_file)
            if result is not None:
                successful_files.append(str(rel_path))
            else:
                failed_files.append((str(rel_path), "Returned None"))
        except Exception as e:
            # Check if this is a known non-OCMF file
            if (
                any(
                    keyword in file_name_lower
                    for keyword in ["metra", "edl", "isa-edl"]
                )
                or parent_dir == "emh-emoc"
                or "invalid" in file_name_lower
            ):
                skipped_files.append(
                    (str(rel_path), f"Non-OCMF format: {type(e).__name__}")
                )
            else:
                failed_files.append((str(rel_path), f"{type(e).__name__}: {e}"))

    print("\n=== PARSING SUMMARY ===")
    print(f"Total files: {len(transparency_xml_files)}")
    print(f"Successful: {len(successful_files)}")
    print(f"Failed: {len(failed_files)}")
    print(f"Skipped (non-OCMF): {len(skipped_files)}")

    if successful_files:
        print("\n✓ Successfully parsed files:")
        for filename in successful_files:
            print(f"  - {filename}")

    if failed_files:
        print("\n✗ Failed to parse files:")
        for filename, error in failed_files:
            print(f"  - {filename}: {error}")

    if skipped_files:
        print("\n⚠ Skipped files (non-OCMF format):")
        for filename, reason in skipped_files:
            print(f"  - {filename}: {reason}")

    # This test always passes - it's just for reporting
    assert True
