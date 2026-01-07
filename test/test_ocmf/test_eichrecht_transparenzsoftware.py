"""Tests for Eichrecht compliance using Transparenzsoftware XML test files.

This module tests our Eichrecht compliance checking against the official
Transparenzsoftware test suite to ensure compatibility and correctness.
"""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

import pytest

from pyocmf.compliance import IssueSeverity, check_eichrecht_transaction
from pyocmf.utils.xml import OcmfContainer

if TYPE_CHECKING:
    from pyocmf.utils.xml import OcmfRecord


@pytest.fixture
def transparenzsoftware_xml_dir() -> pathlib.Path:
    """Return the path to the Transparenzsoftware XML test resources."""
    return (
        pathlib.Path(__file__).parent.parent
        / "resources"
        / "transparenzsoftware"
        / "src"
        / "test"
        / "resources"
        / "xml"
    )


def get_transaction_pair(
    xml_path: pathlib.Path,
) -> tuple[OcmfRecord, OcmfRecord] | None:
    """Extract begin and end transaction from an XML file.

    Identifies transaction pairs by examining the TX (transaction) field
    in the OCMF readings data.

    Args:
        xml_path: Path to the XML file

    Returns:
        Tuple of (begin_record, end_record) if both present, None otherwise
    """
    try:
        container = OcmfContainer.from_xml(xml_path)
    except (ValueError, FileNotFoundError):
        return None

    if len(container) < 2:
        return None

    begin_record: OcmfRecord | None = None
    end_record: OcmfRecord | None = None

    for record in container:
        # Check if this record contains a begin reading (TX='B')
        if record.ocmf.payload.RD:
            for reading in record.ocmf.payload.RD:
                if reading.TX and reading.TX.value == "B":
                    begin_record = record
                    break
                if reading.TX and reading.TX.is_end_reading():
                    end_record = record
                    break

    if begin_record and end_record:
        return (begin_record, end_record)

    return None


@pytest.mark.parametrize(
    ("xml_file", "should_pass", "description"),
    [
        # These files should pass Eichrecht validation
        (
            "test_ocmf_ebee_01.xml",
            True,
            "ebee charger transaction - start and end with same meter value",
        ),
        # These files should fail Eichrecht validation
        (
            "test_ocmf_ebee_02.xml",
            False,
            "ebee charger transaction with value regression (end < begin)",
        ),
    ],
)
def test_eichrecht_compliance_from_transparenzsoftware(
    transparenzsoftware_xml_dir: pathlib.Path,
    xml_file: str,
    should_pass: bool,
    description: str,
) -> None:
    """Test Eichrecht compliance for Transparenzsoftware XML files.

    This test validates that our Eichrecht compliance checker produces
    expected results for the official Transparenzsoftware test suite.

    Args:
        transparenzsoftware_xml_dir: Directory containing XML test files
        xml_file: Name of the XML file to test
        should_pass: Whether the transaction should pass Eichrecht validation
        description: Human-readable description of the test case
    """
    xml_path = transparenzsoftware_xml_dir / xml_file

    if not xml_path.exists():
        pytest.skip(f"Test file not found: {xml_file}")

    transaction_pair = get_transaction_pair(xml_path)

    if transaction_pair is None:
        pytest.skip(f"Could not extract transaction pair from {xml_file}")

    assert transaction_pair is not None  # for type checker
    begin_record, end_record = transaction_pair

    begin_payload = begin_record.ocmf.payload
    end_payload = end_record.ocmf.payload

    issues = check_eichrecht_transaction(begin_payload, end_payload)

    errors = [issue for issue in issues if issue.severity == IssueSeverity.ERROR]
    warnings = [issue for issue in issues if issue.severity == IssueSeverity.WARNING]

    if should_pass:
        if errors:
            error_msgs = "\n".join(f"  - {issue}" for issue in errors)
            pytest.fail(
                f"Expected {xml_file} to pass Eichrecht validation, but got errors:\n{error_msgs}\n"
                f"Description: {description}"
            )
    else:
        if not errors:
            warning_msgs = "\n".join(f"  - {issue}" for issue in warnings) if warnings else "None"
            pytest.fail(
                f"Expected {xml_file} to fail Eichrecht validation, but it passed.\n"
                f"Warnings: {warning_msgs}\n"
                f"Description: {description}"
            )


def test_transparenzsoftware_test_files_exist(
    transparenzsoftware_xml_dir: pathlib.Path,
) -> None:
    """Verify that the Transparenzsoftware test files are available.

    This test ensures the git submodule is properly initialized.
    """
    assert transparenzsoftware_xml_dir.exists(), (
        "Transparenzsoftware XML directory not found. Did you run 'git submodule update --init --recursive'?"
    )

    xml_files = list(transparenzsoftware_xml_dir.glob("*.xml"))
    assert len(xml_files) > 0, "No XML test files found in Transparenzsoftware directory"


def test_transaction_pair_extraction_valid(
    transparenzsoftware_xml_dir: pathlib.Path,
) -> None:
    """Test that we can correctly extract transaction pairs from valid files."""
    xml_path = transparenzsoftware_xml_dir / "test_ocmf_ebee_01.xml"

    if not xml_path.exists():
        pytest.skip("Test file not found")

    pair = get_transaction_pair(xml_path)
    assert pair is not None, "Should extract transaction pair"

    begin_record, end_record = pair
    assert begin_record.ocmf.payload.RD is not None
    assert end_record.ocmf.payload.RD is not None
    assert len(begin_record.ocmf.payload.RD) > 0
    assert len(end_record.ocmf.payload.RD) > 0


def test_transaction_pair_extraction_invalid(
    transparenzsoftware_xml_dir: pathlib.Path,
) -> None:
    """Test that extraction returns None for files without complete transactions."""
    xml_path = transparenzsoftware_xml_dir / "test_ocmf_keba_kcp30.xml"

    if not xml_path.exists():
        pytest.skip("Test file not found")

    pair = get_transaction_pair(xml_path)
    assert pair is None, "Should not extract pair from single-value file"
