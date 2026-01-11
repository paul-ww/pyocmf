from __future__ import annotations

from typing import TYPE_CHECKING

from pyocmf.exceptions import PyOCMFError
from pyocmf.utils.xml import OcmfContainer

if TYPE_CHECKING:
    import pathlib

    from pyocmf.utils.xml import OcmfRecord


def should_skip_xml_file(xml_file: pathlib.Path) -> tuple[bool, str | None]:
    file_name_lower = xml_file.name.lower()
    parent_dir = xml_file.parent.name

    if "rsa" in file_name_lower:
        return True, "Skipping unsupported OCMF feature file"

    skip_keywords = ["metra", "edl", "isa-edl"]
    skip_dirs = ["emh-emoc"]
    skip_patterns = ["invalid", "mennekes", "wirelane", "template", "test_input_xml_two_values"]

    if any(keyword in file_name_lower for keyword in skip_keywords):
        return True, "File contains unsupported format"

    if parent_dir in skip_dirs:
        return True, f"Files in {parent_dir} directory are not supported"

    if any(pattern in file_name_lower for pattern in skip_patterns):
        return True, "File matches skip pattern"

    return False, None


def should_expect_parsing_error(xml_file: pathlib.Path) -> bool:
    file_name_lower = xml_file.name.lower()
    parent_dir = xml_file.parent.name

    error_keywords = ["metra", "edl", "isa-edl"]
    error_dirs = ["emh-emoc"]
    error_patterns = ["invalid", "mennekes", "wirelane", "template", "test_input_xml_two_values"]

    if any(keyword in file_name_lower for keyword in error_keywords):
        return True

    if parent_dir in error_dirs:
        return True

    if any(pattern in file_name_lower for pattern in error_patterns):
        return True

    return False


def parse_xml_with_expected_behavior(xml_file: pathlib.Path) -> OcmfContainer | None:
    if should_expect_parsing_error(xml_file):
        try:
            OcmfContainer.from_xml(xml_file)
        except PyOCMFError:
            return None
        msg = f"Expected {xml_file.name} to raise PyOCMFError, but it parsed successfully"
        raise AssertionError(msg)

    return OcmfContainer.from_xml(xml_file)


def get_transaction_pair(
    xml_path: pathlib.Path,
) -> tuple[OcmfRecord, OcmfRecord] | None:
    try:
        container = OcmfContainer.from_xml(xml_path)
    except (ValueError, FileNotFoundError, PyOCMFError):
        return None

    if len(container) < 2:
        return None

    begin_record: OcmfRecord | None = None
    end_record: OcmfRecord | None = None

    for record in container:
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
