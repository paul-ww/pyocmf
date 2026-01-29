from __future__ import annotations

import decimal
from typing import TYPE_CHECKING

from pyocmf.core import OCMF, Payload, Signature
from pyocmf.core.reading import MeterReadingReason, MeterStatus, OCMFTimestamp, Reading
from pyocmf.enums.identifiers import IdentificationType, UserAssignmentStatus
from pyocmf.enums.units import EnergyUnit
from pyocmf.exceptions import PyOCMFError
from pyocmf.models import OBIS
from pyocmf.utils.xml import OcmfContainer

if TYPE_CHECKING:
    import pathlib

    from pyocmf.compliance.models import EichrechtIssue
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


def tm(timestamp_str: str) -> OCMFTimestamp:
    """Create OCMFTimestamp from string."""
    return OCMFTimestamp.from_string(timestamp_str)


def obis(code_str: str) -> OBIS:
    """Create OBIS code from string."""
    return OBIS.from_string(code_str)


def decimal_value(value: str | float | int) -> decimal.Decimal:
    """Create Decimal value from number or string."""
    return decimal.Decimal(str(value))


def create_test_reading(
    timestamp: str = "2023-01-01T12:00:00,000+0000 S",
    tx: MeterReadingReason = MeterReadingReason.BEGIN,
    rv: str | decimal.Decimal = "50.0",
    ri: str | OBIS = "01-00:B2.08.00*FF",
    ru: EnergyUnit = EnergyUnit.KWH,
    st: MeterStatus = MeterStatus.OK,
    ef: str = "",
    cl: decimal.Decimal | None = None,
) -> Reading:
    """Create a test Reading with sensible defaults."""
    return Reading(
        TM=OCMFTimestamp.from_string(timestamp),
        TX=tx,
        RV=decimal.Decimal(str(rv)) if not isinstance(rv, decimal.Decimal) else rv,
        RI=OBIS.from_string(ri) if isinstance(ri, str) else ri,
        RU=ru,
        ST=st,
        EF=ef or None,
        CL=cl,
    )


def create_test_payload(
    pagination: str = "T1",
    gateway_serial: str = "12345",
    meter_serial: str | None = None,
    readings: list[Reading] | None = None,
    identification_status: bool = False,
    identification_level: UserAssignmentStatus | None = UserAssignmentStatus.NO_ASSIGNMENT,
    identification_type: IdentificationType = IdentificationType.NONE,
    identification_data: str | None = None,
    **kwargs,
) -> Payload:
    """Create a test Payload with sensible defaults."""
    if readings is None:
        readings = [create_test_reading()]

    return Payload(
        FV="1.0",
        GI="TEST_GW",
        GS=gateway_serial,
        MS=meter_serial,
        GV="1.0",
        PG=pagination,
        RD=readings,
        IS=identification_status,
        IL=identification_level,
        IT=identification_type,
        ID=identification_data,
        **kwargs,
    )


def create_test_ocmf(
    payload: Payload | None = None,
    signature_data: str = "deadbeef",
    **payload_kwargs,
) -> OCMF:
    """Create a test OCMF with sensible defaults."""
    if payload is None:
        payload = create_test_payload(**payload_kwargs)

    signature = Signature(SD=signature_data)
    return OCMF(header="OCMF", payload=payload, signature=signature)


def create_transaction_pair(
    begin_serial: str = "12345",
    end_serial: str | None = None,
    begin_pagination: str = "T1",
    end_pagination: str | None = None,
    begin_timestamp: str = "2023-01-01T12:00:00,000+0000 S",
    end_timestamp: str = "2023-01-01T13:00:00,000+0000 S",
    begin_value: str | decimal.Decimal = "50.0",
    end_value: str | decimal.Decimal = "100.0",
    obis_code: str = "01-00:B2.08.00*FF",
    unit: EnergyUnit = EnergyUnit.KWH,
    identification_type: IdentificationType = IdentificationType.ISO14443,
    identification_data: str = "12345678",
) -> tuple[OCMF, OCMF]:
    """Create a pair of begin/end OCMF objects for transaction testing."""
    if end_serial is None:
        end_serial = begin_serial

    if end_pagination is None:
        begin_num = int(begin_pagination[1:])
        end_pagination = f"{begin_pagination[0]}{begin_num + 1}"

    begin_reading = create_test_reading(
        timestamp=begin_timestamp,
        tx=MeterReadingReason.BEGIN,
        rv=begin_value,
        ri=obis_code,
        ru=unit,
        cl=decimal.Decimal(0) if obis_code.startswith(("01-00:B", "01-00:C")) else None,
    )

    end_reading = create_test_reading(
        timestamp=end_timestamp,
        tx=MeterReadingReason.END,
        rv=end_value,
        ri=obis_code,
        ru=unit,
    )

    begin = create_test_ocmf(
        pagination=begin_pagination,
        gateway_serial=begin_serial,
        readings=[begin_reading],
        identification_status=True,
        identification_level=UserAssignmentStatus.VERIFIED,
        identification_type=identification_type,
        identification_data=identification_data,
    )

    end = create_test_ocmf(
        pagination=end_pagination,
        gateway_serial=end_serial,
        readings=[end_reading],
        identification_status=True,
        identification_level=UserAssignmentStatus.VERIFIED,
        identification_type=identification_type,
        identification_data=identification_data,
    )

    return begin, end


def assert_has_issue(
    issues: list[EichrechtIssue],
    code: str,
    message_fragment: str | None = None,
) -> None:
    """Assert that issues list contains an issue with the given code.

    Optionally check for a message fragment within the issue message.
    """
    matching = [i for i in issues if i.code == code or i.code.value == code]
    assert matching, f"Expected issue with code {code}, got: {[i.code for i in issues]}"

    if message_fragment:
        assert any(message_fragment in i.message for i in matching), (
            f"Expected fragment '{message_fragment}' in: {[i.message for i in matching]}"
        )


def assert_no_errors(issues: list[EichrechtIssue]) -> None:
    """Assert that issues list contains no ERROR severity issues."""
    from pyocmf.compliance.models import IssueSeverity

    errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
    assert len(errors) == 0, (
        f"Expected no errors, got: {[f'{e.code}: {e.message}' for e in errors]}"
    )


def assert_has_error(issues: list[EichrechtIssue], code: str | None = None) -> None:
    """Assert that issues list contains at least one ERROR severity issue."""
    from pyocmf.compliance.models import IssueSeverity

    errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
    assert len(errors) > 0, "Expected at least one error"

    if code:
        assert any(i.code == code or i.code.value == code for i in errors), (
            f"Expected error with code {code}, got: {[e.code for e in errors]}"
        )


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
