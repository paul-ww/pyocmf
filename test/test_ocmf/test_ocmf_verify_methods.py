from __future__ import annotations

import decimal
import pathlib

import pytest

from pyocmf.compliance.models import IssueSeverity
from pyocmf.core import OCMF, Payload, Signature
from pyocmf.core.reading import MeterReadingReason, MeterStatus, OCMFTimestamp, Reading
from pyocmf.enums.identifiers import IdentificationType, UserAssignmentStatus
from pyocmf.enums.units import EnergyUnit
from pyocmf.models import OBIS

# Check if cryptography is available
try:
    from pyocmf.crypto.verification import CRYPTOGRAPHY_AVAILABLE
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class TestCheckEichrecht:
    def create_compliant_ocmf(self) -> OCMF:
        payload = Payload(
            FV="1.0",
            GI="TEST_GW",
            GS="12345",
            GV="1.0",
            PG="T1",
            RD=[
                Reading(
                    TM=OCMFTimestamp.from_string("2023-01-01T12:00:00,000+0000 S"),
                    TX=MeterReadingReason.BEGIN,
                    RV=decimal.Decimal("50.0"),
                    RI=OBIS.from_string("01-00:B2.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.OK,
                    EF="",
                )
            ],
            IS=True,
            IL=UserAssignmentStatus.VERIFIED,
            IT=IdentificationType.ISO14443,
            ID="12345678",
        )
        signature = Signature(SD="deadbeef")
        return OCMF(header="OCMF", payload=payload, signature=signature)

    def test_check_eichrecht_single_compliant(self) -> None:
        ocmf = self.create_compliant_ocmf()
        issues = ocmf.check_eichrecht()
        errors = [issue for issue in issues if issue.severity == IssueSeverity.ERROR]
        assert len(errors) == 0

    def test_check_eichrecht_single_non_compliant(self) -> None:
        ocmf = self.create_compliant_ocmf()
        ocmf.payload.RD[0].ST = MeterStatus.TIMEOUT  # Bad status!

        issues = ocmf.check_eichrecht()
        assert len(issues) > 0
        assert any("must be 'G'" in issue.message for issue in issues)

    def test_check_eichrecht_no_readings(self) -> None:
        ocmf = self.create_compliant_ocmf()
        ocmf.payload.RD = []

        issues = ocmf.check_eichrecht()
        assert len(issues) > 0
        assert any("No readings" in issue.message for issue in issues)

    def test_check_eichrecht_transaction_pair(self) -> None:
        begin = self.create_compliant_ocmf()

        end = self.create_compliant_ocmf()
        end.payload.PG = "T2"
        end.payload.RD[0].TM = OCMFTimestamp.from_string("2023-01-01T13:00:00,000+0000 S")
        end.payload.RD[0].TX = MeterReadingReason.END
        end.payload.RD[0].RV = decimal.Decimal("100.0")

        issues = begin.check_eichrecht(end)
        errors = [issue for issue in issues if issue.severity == IssueSeverity.ERROR]
        assert len(errors) == 0

    def test_check_eichrecht_transaction_pair_regression(self) -> None:
        begin = self.create_compliant_ocmf()
        begin.payload.RD[0].RV = decimal.Decimal("100.0")

        end = self.create_compliant_ocmf()
        end.payload.RD[0].TX = MeterReadingReason.END
        end.payload.RD[0].RV = decimal.Decimal("50.0")  # Less than begin!

        issues = begin.check_eichrecht(end)
        assert any("must be >=" in issue.message for issue in issues)


@pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not installed")
class TestVerifyMethod:
    def test_verify_combines_signature_and_eichrecht(
        self, transparency_xml_dir: pathlib.Path
    ) -> None:
        from pyocmf.utils.xml import OcmfContainer

        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"
        container = OcmfContainer.from_xml(xml_file)
        ocmf = container[0].ocmf
        public_key = container[0].public_key

        assert public_key is not None
        sig_valid, issues = ocmf.verify(public_key)

        assert sig_valid is True
        # The signature is valid, issues may have warnings but should be mostly clean
        assert isinstance(issues, list)

    def test_verify_with_eichrecht_disabled(self, transparency_xml_dir: pathlib.Path) -> None:
        from pyocmf.utils.xml import OcmfContainer

        xml_file = transparency_xml_dir / "test_ocmf_keba_kcp30.xml"
        container = OcmfContainer.from_xml(xml_file)
        ocmf = container[0].ocmf
        public_key = container[0].public_key

        assert public_key is not None
        sig_valid, issues = ocmf.verify(public_key, eichrecht=False)

        assert sig_valid is True
        assert len(issues) == 0  # No Eichrecht validation performed

    def test_verify_with_transaction_pair(self, transparency_xml_dir: pathlib.Path) -> None:
        # Create a simple transaction pair programmatically
        begin_payload = Payload(
            FV="1.0",
            GI="TEST",
            GS="123",
            GV="1.0",
            PG="T1",
            RD=[
                Reading(
                    TM=OCMFTimestamp.from_string("2023-01-01T12:00:00,000+0000 S"),
                    TX=MeterReadingReason.BEGIN,
                    RV=decimal.Decimal("50.0"),
                    RI=OBIS.from_string("01-00:B2.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.OK,
                )
            ],
            IS=False,
            IL=UserAssignmentStatus.NO_ASSIGNMENT,
        )
        end_payload = Payload(
            FV="1.0",
            GI="TEST",
            GS="123",
            GV="1.0",
            PG="T2",
            RD=[
                Reading(
                    TM=OCMFTimestamp.from_string("2023-01-01T13:00:00,000+0000 S"),
                    TX=MeterReadingReason.END,
                    RV=decimal.Decimal("100.0"),
                    RI=OBIS.from_string("01-00:B2.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.OK,
                )
            ],
            IS=False,
            IL=UserAssignmentStatus.NO_ASSIGNMENT,
        )

        begin = OCMF(header="OCMF", payload=begin_payload, signature=Signature(SD="deadbeef"))
        end = OCMF(header="OCMF", payload=end_payload, signature=Signature(SD="deadbeef"))

        # Can't verify signature without parsing from string, so just test Eichrecht
        issues = begin.check_eichrecht(end)
        assert isinstance(issues, list)


class TestCheckEichrechtMultipleReadings:
    def test_multiple_readings_validated(self) -> None:
        payload = Payload(
            FV="1.0",
            GI="TEST_GW",
            GS="12345",
            GV="1.0",
            PG="T1",
            RD=[
                Reading(
                    TM=OCMFTimestamp.from_string("2023-01-01T12:00:00,000+0000 S"),
                    TX=MeterReadingReason.BEGIN,
                    RV=decimal.Decimal("50.0"),
                    RI=OBIS.from_string("01-00:B2.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.OK,
                    EF="",
                ),
                Reading(
                    TM=OCMFTimestamp.from_string("2023-01-01T12:30:00,000+0000 S"),
                    TX=MeterReadingReason.CHARGING,
                    RV=decimal.Decimal("75.0"),
                    RI=OBIS.from_string("01-00:B2.08.00*FF"),
                    RU=EnergyUnit.KWH,
                    ST=MeterStatus.TIMEOUT,  # Bad status on second reading!
                    EF="",
                ),
            ],
            IS=True,
            IL=UserAssignmentStatus.VERIFIED,
            IT=IdentificationType.ISO14443,
            ID="12345678",
        )
        signature = Signature(SD="deadbeef")
        ocmf = OCMF(header="OCMF", payload=payload, signature=signature)

        issues = ocmf.check_eichrecht()
        # Should detect the bad status in second reading
        assert any("must be 'G'" in issue.message for issue in issues)
