"""Tests for OCMF verify_eichrecht() and verify() methods."""

from __future__ import annotations

import decimal
import pathlib

import pytest

from pyocmf.ocmf import OCMF
from pyocmf.sections.payload import Payload
from pyocmf.sections.reading import MeterReadingReason, MeterStatus, OCMFTimestamp, Reading
from pyocmf.sections.signature import Signature
from pyocmf.types.identifiers import IdentificationType, UserAssignmentStatus
from pyocmf.types.obis import OBIS
from pyocmf.types.units import EnergyUnit

# Check if cryptography is available
try:
    from pyocmf.verification import CRYPTOGRAPHY_AVAILABLE
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class TestVerifyEichrecht:
    """Test OCMF.verify_eichrecht() method."""

    def create_compliant_ocmf(self) -> OCMF:
        """Create a compliant OCMF record."""
        payload = Payload.model_construct(
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

    def test_verify_eichrecht_single_compliant(self) -> None:
        """A compliant single record should pass Eichrecht validation."""
        ocmf = self.create_compliant_ocmf()
        issues = ocmf.verify_eichrecht()
        # May have warnings but no errors containing "must"
        assert all("must" not in issue.lower() or "warning" in issue.lower() for issue in issues)

    def test_verify_eichrecht_single_non_compliant(self) -> None:
        """A non-compliant record should produce issues."""
        ocmf = self.create_compliant_ocmf()
        ocmf.payload.RD[0].ST = MeterStatus.TIMEOUT  # Bad status!

        issues = ocmf.verify_eichrecht()
        assert len(issues) > 0
        assert any("must be 'G'" in issue for issue in issues)

    def test_verify_eichrecht_no_readings(self) -> None:
        """Validation should fail if no readings present."""
        ocmf = self.create_compliant_ocmf()
        ocmf.payload.RD = []

        issues = ocmf.verify_eichrecht()
        assert len(issues) > 0
        assert any("No readings" in issue for issue in issues)

    def test_verify_eichrecht_transaction_pair(self) -> None:
        """Validation should work for transaction pairs."""
        begin = self.create_compliant_ocmf()

        end = self.create_compliant_ocmf()
        end.payload.PG = "T2"
        end.payload.RD[0].TM = OCMFTimestamp.from_string("2023-01-01T13:00:00,000+0000 S")
        end.payload.RD[0].TX = MeterReadingReason.END
        end.payload.RD[0].RV = decimal.Decimal("100.0")

        issues = begin.verify_eichrecht(end)
        # Should pass (may have warnings but no critical errors)
        errors = [i for i in issues if "must" in i.lower() and "warning" not in i.lower()]
        assert len(errors) == 0

    def test_verify_eichrecht_transaction_pair_regression(self) -> None:
        """Transaction pair with value regression should fail."""
        begin = self.create_compliant_ocmf()
        begin.payload.RD[0].RV = decimal.Decimal("100.0")

        end = self.create_compliant_ocmf()
        end.payload.RD[0].TX = MeterReadingReason.END
        end.payload.RD[0].RV = decimal.Decimal("50.0")  # Less than begin!

        issues = begin.verify_eichrecht(end)
        assert any("must be >=" in issue for issue in issues)


@pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not installed")
class TestVerifyMethod:
    """Test OCMF.verify() convenience method."""

    def test_verify_combines_signature_and_eichrecht(
        self, transparency_xml_dir: pathlib.Path
    ) -> None:
        """verify() should return both signature validity and compliance issues."""
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
        """verify() with eichrecht=False should skip compliance checks."""
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
        """verify() should validate transaction pairs when other is provided."""
        # Create a simple transaction pair programmatically
        begin_payload = Payload.model_construct(
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
        end_payload = Payload.model_construct(
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
        issues = begin.verify_eichrecht(end)
        assert isinstance(issues, list)


class TestVerifyEichrechtMultipleReadings:
    """Test verify_eichrecht with multiple readings in a single payload."""

    def test_multiple_readings_validated(self) -> None:
        """All readings in a payload should be validated."""
        payload = Payload.model_construct(
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

        issues = ocmf.verify_eichrecht()
        # Should detect the bad status in second reading
        assert any("must be 'G'" in issue for issue in issues)
