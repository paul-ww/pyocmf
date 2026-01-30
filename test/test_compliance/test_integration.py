from __future__ import annotations

import pathlib

import pytest

from pyocmf.compliance import IssueSeverity, check_eichrecht_transaction

from ..helpers import get_transaction_pair


@pytest.mark.parametrize(
    ("xml_file", "should_pass", "description"),
    [
        (
            "test_ocmf_ebee_01.xml",
            True,
            "ebee charger transaction - start and end with same meter value",
        ),
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
    """Validate Eichrecht compliance checker against official Transparenzsoftware test suite."""
    xml_path = transparency_xml_dir / xml_file

    if not xml_path.exists():
        pytest.skip(f"Test file not found: {xml_file}")

    transaction_pair = get_transaction_pair(xml_path)

    if transaction_pair is None:
        pytest.skip(f"Could not extract transaction pair from {xml_file}")

    assert transaction_pair is not None
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
