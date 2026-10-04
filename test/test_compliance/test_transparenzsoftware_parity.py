"""Eichrecht parity with the Transparenzsoftware law checks.

Ports the cases of OCMFVerifiedDataTest and OCMFVerificationParserTest, plus the
transaction outcomes the Transparenzsoftware reports for its XML corpus.
Known divergences are strict xfails so fixing them surfaces immediately.
"""

from __future__ import annotations

import pathlib
import warnings

import pytest

from pyocmf.compliance import IssueCode, IssueSeverity, check_eichrecht_transaction
from pyocmf.compliance.models import EichrechtIssue
from pyocmf.core import OCMF
from pyocmf.crypto.availability import CRYPTOGRAPHY_AVAILABLE
from pyocmf.enums.identifiers import UserAssignmentStatus
from pyocmf.enums.reading import MeterReadingReason, MeterStatus
from pyocmf.enums.units import EnergyUnit
from pyocmf.utils.xml import OcmfContainer

from ..helpers import (
    assert_has_error,
    assert_has_issue,
    assert_no_errors,
    create_test_payload,
    create_test_reading,
    create_transaction_pair,
    get_transaction_pair,
)

IMPORT_OBIS = "01-00:01.08.00*FF"
EXPORT_OBIS = "01-00:02.08.00*FF"
DURATION_OBIS = "01-00:00.08.06*FF"

# testEfT_Result: Iskra meter flagging a time error ("t") on both readings
EF_T_OCMF = (
    'OCMF|{"FV":"1.0","GI":"eSystemsMtg OcppChargePoint_v0 ESY-00101.01.2201234567",'
    '"GS":"000007","GV":"PWR P0037","PG":"T241","MV":"Iskra","MM":"WM3M4C","MS":"W4155775",'
    '"MF":"2.05","IS":true,"IT":"UNDEFINED","ID":"0480423a4b5880","CT":"CBIDC",'
    '"CI":"KHStation","RD":[{"TM":"2023-04-14T11:51:06,000+0000 S","TX":"B","RV":80.77,'
    '"RI":"1-b:1.8.0","RU":"kWh","RT":"AC","EF":"t","ST":"G"},'
    '{"TM":"2023-04-14T11:54:43,000+0000 S","TX":"E","RV":80.97,"RI":"1-b:1.8.0",'
    '"RU":"kWh","RT":"AC","EF":"t","ST":"G"}]}|'
    '{"SD":"30450220331E469735684E31F6F5903457C6DD8873CEAE1DFDBE4001FFBF94D124481DE7'
    '022100B8375F730A0B719B99B2DB89BA5B03CFDF4CE1A8829816BF7BBB75C3042C289D"}'
)
EF_T_PUBLIC_KEY = (
    "3059301306072A8648CE3D020106082A8648CE3D03010703420004890ADD61803B4665C9BFC3F4E4"
    "0C4696DF54C8FB8E067613CC465D7EA67411C0A9517C0D1A021B0859A829B85D5F6FA567047E5CBD"
    "91CD9C01F643003FEA3646"
)


def _errors(issues: list[EichrechtIssue]) -> set[IssueCode]:
    return {issue.code for issue in issues if issue.severity == IssueSeverity.ERROR}


def _single_payload_errors(xml_path: pathlib.Path) -> set[IssueCode]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        record = OcmfContainer.from_xml(xml_path)[0]
    return _errors(record.ocmf.check_eichrecht())


def _pair_errors(xml_path: pathlib.Path) -> set[IssueCode]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        pair = get_transaction_pair(xml_path)
    assert pair is not None
    begin, end = pair
    return _errors(check_eichrecht_transaction(begin.ocmf.payload, end.ocmf.payload))


class TestTransactionPairLawChecks:
    """OCMFVerifiedDataTest: lawConform() on begin/end payloads."""

    def test_law_ok(self) -> None:
        begin, end = create_transaction_pair()
        assert_no_errors(check_eichrecht_transaction(begin.payload, end.payload))

    def test_stop_contains_start(self) -> None:
        begin, end = create_transaction_pair()
        end.payload.RD[0].TX = MeterReadingReason.BEGIN
        assert_has_error(check_eichrecht_transaction(begin.payload, end.payload), IssueCode.END_TX)

    def test_start_contains_stop(self) -> None:
        begin, end = create_transaction_pair()
        begin.payload.RD[0].TX = MeterReadingReason.TERMINATION_LOCAL
        issues = check_eichrecht_transaction(begin.payload, end.payload)
        assert_has_error(issues, IssueCode.BEGIN_TX)

    @pytest.mark.parametrize(
        "level",
        [
            UserAssignmentStatus.UID_MISMATCH,
            UserAssignmentStatus.CERT_INCORRECT,
            UserAssignmentStatus.CERT_EXPIRED,
            UserAssignmentStatus.CERT_UNVERIFIED,
        ],
    )
    @pytest.mark.parametrize("side", ["begin", "end"])
    def test_contract_status_error(self, level: UserAssignmentStatus, side: str) -> None:
        begin, end = create_transaction_pair()
        (begin if side == "begin" else end).payload.IL = level
        issues = check_eichrecht_transaction(begin.payload, end.payload)
        assert_has_issue(issues, IssueCode.ID_LEVEL_INVALID, side)

    def test_meter_error_code(self) -> None:
        begin, end = create_transaction_pair()
        end.payload.RD[0].ST = MeterStatus.OTHER_ERROR
        issues = check_eichrecht_transaction(begin.payload, end.payload)
        assert_has_error(issues, IssueCode.METER_STATUS)

    def test_energy_error_flag(self) -> None:
        begin, end = create_transaction_pair()
        end.payload.RD[0].EF = "E"
        issues = check_eichrecht_transaction(begin.payload, end.payload)
        assert_has_error(issues, IssueCode.ERROR_FLAGS)

    @pytest.mark.xfail(strict=True, reason="Transparenzsoftware rejects multiple start readings")
    def test_multiple_start_values(self) -> None:
        begin, end = create_transaction_pair()
        begin.payload.RD.append(begin.payload.RD[0].model_copy())
        assert_has_error(check_eichrecht_transaction(begin.payload, end.payload))

    @pytest.mark.xfail(
        strict=True, reason="Transparenzsoftware rejects a begin payload containing a stop reading"
    )
    def test_begin_payload_containing_stop_reading(self) -> None:
        begin, end = create_transaction_pair()
        begin.payload.RD.append(end.payload.RD[0].model_copy())
        assert_has_error(check_eichrecht_transaction(begin.payload, end.payload))

    @pytest.mark.xfail(
        strict=True,
        reason="pyocmf compares RD[0]/RD[-1]; Transparenzsoftware compares law-relevant "
        "(energy import) readings only",
    )
    def test_compares_law_relevant_readings_only(self) -> None:
        begin_readings = [
            create_test_reading(tx=MeterReadingReason.BEGIN, rv="10", ri=IMPORT_OBIS),
            create_test_reading(tx=MeterReadingReason.BEGIN, rv="4", ri=EXPORT_OBIS),
        ]
        end_readings = [
            create_test_reading(
                timestamp="2023-01-01T13:00:00,000+0000 S",
                tx=MeterReadingReason.END,
                rv="20",
                ri=IMPORT_OBIS,
            ),
            create_test_reading(
                timestamp="2023-01-01T13:00:00,000+0000 S",
                tx=MeterReadingReason.END,
                rv="4",
                ri=EXPORT_OBIS,
            ),
        ]
        begin = create_test_payload(pagination="T1", readings=begin_readings)
        end = create_test_payload(pagination="T2", readings=end_readings)
        assert_no_errors(check_eichrecht_transaction(begin, end))

    @pytest.mark.xfail(
        strict=True,
        reason="Spec increments PG per record, so intermediate records leave gaps "
        "between begin and end; pyocmf requires end == begin + 1",
    )
    def test_pagination_gap_from_intermediate_records(self) -> None:
        begin, end = create_transaction_pair(begin_pagination="T1", end_pagination="T3")
        assert_no_errors(check_eichrecht_transaction(begin.payload, end.payload))


class TestSinglePayloadTransactionLawChecks:
    """checkLawIntegrityForTransaction() on a payload holding both B and E readings."""

    @staticmethod
    def _payload(begin_value: str, end_value: str) -> OCMF:
        readings = [
            create_test_reading(tx=MeterReadingReason.BEGIN, rv=begin_value, ri=IMPORT_OBIS),
            create_test_reading(
                timestamp="2023-01-01T13:00:00,000+0000 S",
                tx=MeterReadingReason.END,
                rv=end_value,
                ri=IMPORT_OBIS,
                ru=EnergyUnit.KWH,
            ),
        ]
        return OCMF(
            header="OCMF",
            payload=create_test_payload(readings=readings),
            signature={"SD": "00"},
        )

    def test_law_ok(self) -> None:
        assert_no_errors(self._payload("1", "2").check_eichrecht())

    @pytest.mark.xfail(
        strict=True,
        reason="check_eichrecht() without 'other' only checks readings individually; "
        "Transparenzsoftware checks B/E ordering within one payload",
    )
    def test_start_meter_more_than_stop(self) -> None:
        issues = self._payload("15", "5").check_eichrecht()
        assert_has_error(issues, IssueCode.VALUE_REGRESSION)


class TestErrorFlagTime:
    """testEfT_Result: a time error flag ("t") is not law-relevant."""

    @pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not installed")
    def test_signature_verifies(self) -> None:
        assert OCMF.from_string(EF_T_OCMF).verify_signature(EF_T_PUBLIC_KEY) is True

    @pytest.mark.xfail(
        strict=True, reason="pyocmf treats any error flag as an error; only 'E' is law-relevant"
    )
    def test_time_error_flag_is_not_an_error(self) -> None:
        assert_no_errors(OCMF.from_string(EF_T_OCMF).check_eichrecht())


class TestCorpusTransactions:
    """Law outcomes the Transparenzsoftware reports for its XML corpus."""

    @pytest.mark.parametrize(
        "xml_file",
        [
            "test_ocmf_ebee_01.xml",
            "brainpoolP256r1.xml",
            "nistP384_0Wh.xml",
        ],
    )
    def test_pair_passes(self, transparency_xml_dir: pathlib.Path, xml_file: str) -> None:
        assert _pair_errors(transparency_xml_dir / xml_file) == set()

    @pytest.mark.parametrize(
        ("xml_file", "expected_error"),
        [
            ("test_ocmf_ebee_02.xml", IssueCode.VALUE_REGRESSION),
            ("20211007-device-with-evt-ocmf-sss-ses.xml", IssueCode.METER_STATUS),
        ],
    )
    def test_pair_fails(
        self, transparency_xml_dir: pathlib.Path, xml_file: str, expected_error: IssueCode
    ) -> None:
        assert expected_error in _pair_errors(transparency_xml_dir / xml_file)

    @pytest.mark.xfail(
        strict=True,
        reason="End record adds a charging-duration reading (00.08.06) after the energy "
        "reading; pyocmf compares it against the begin energy reading",
    )
    @pytest.mark.parametrize("xml_file", ["OCMF_Test_Data_00.xml", "ocmf_sec.xml"])
    def test_pair_with_trailing_duration_reading_passes(
        self, transparency_xml_dir: pathlib.Path, xml_file: str
    ) -> None:
        assert _pair_errors(transparency_xml_dir / xml_file) == set()

    @pytest.mark.parametrize(
        "xml_file",
        [
            "test_ocmf_keba_kcp30.xml",
            "chargepoint_3.xml",
            "VW_OCMF_load.xml",
            "Ocmf_Example_OBIS_98.8.0_2.8.0.xml",
            "measurements.xml",
            "ocmf_tariff_1.xml",
            "keba_test.xml",
        ],
    )
    def test_single_payload_transaction_passes(
        self, transparency_xml_dir: pathlib.Path, xml_file: str
    ) -> None:
        assert _single_payload_errors(transparency_xml_dir / xml_file) == set()

    @pytest.mark.parametrize(
        "xml_file",
        [
            "isa-ocmf/OCMF-receipt-with_publickey_and_data.xml",
            "isa-ocmf/OCMF-receipt-with_import_and_export.xml",
        ],
    )
    def test_single_payload_meter_error_fails(
        self, transparency_xml_dir: pathlib.Path, xml_file: str
    ) -> None:
        assert IssueCode.METER_STATUS in _single_payload_errors(transparency_xml_dir / xml_file)
