from __future__ import annotations

import pathlib

import pytest

from pyocmf.compliance import IssueSeverity, check_eichrecht_transaction

from .helpers import get_transaction_pair


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
    transparency_xml_dir: pathlib.Path,
    xml_file: str,
    should_pass: bool,
    description: str,
) -> None:
    # Validates that our Eichrecht compliance checker produces expected results
    # for the official Transparenzsoftware test suite
    xml_path = transparency_xml_dir / xml_file

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
    transparency_xml_dir: pathlib.Path,
) -> None:
    # Ensures the git submodule is properly initialized
    assert transparency_xml_dir.exists(), (
        "Transparenzsoftware XML directory not found. "
        "Did you run 'git submodule update --init --recursive'?"
    )

    xml_files = list(transparency_xml_dir.glob("*.xml"))
    assert len(xml_files) > 0, "No XML test files found in Transparenzsoftware directory"


def test_transaction_pair_extraction_valid(
    transparency_xml_dir: pathlib.Path,
) -> None:
    xml_path = transparency_xml_dir / "test_ocmf_ebee_01.xml"

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
    transparency_xml_dir: pathlib.Path,
) -> None:
    xml_path = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"

    if not xml_path.exists():
        pytest.skip("Test file not found")

    pair = get_transaction_pair(xml_path)
    assert pair is None, "Should not extract pair from single-value file"
