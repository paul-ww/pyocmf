from __future__ import annotations

import decimal
import pathlib

import pytest

from pyocmf.compliance import IssueCode, IssueSeverity
from pyocmf.utils.xml import CONTEXT_BEGIN, CONTEXT_END, OcmfContainer

from ..helpers import create_transaction_pair, write_xml


class TestTransactionAttributes:
    def test_reads_transaction_id_and_context(self, tmp_path: pathlib.Path) -> None:
        begin, end = create_transaction_pair()
        xml = write_xml(tmp_path / "t.xml", [(begin, 7, CONTEXT_BEGIN), (end, 7, CONTEXT_END)])

        container = OcmfContainer.from_xml(xml)

        assert [(r.transaction_id, r.context) for r in container] == [
            (7, CONTEXT_BEGIN),
            (7, CONTEXT_END),
        ]

    def test_missing_or_invalid_transaction_id_is_none(self, tmp_path: pathlib.Path) -> None:
        begin, end = create_transaction_pair()
        xml = write_xml(tmp_path / "t.xml", [(begin, None, None), (end, None, CONTEXT_END)])
        xml.write_text(xml.read_text().replace("<value>", '<value transactionId="abc">', 1))

        container = OcmfContainer.from_xml(xml)

        assert [r.transaction_id for r in container] == [None, None]

    def test_transactions_group_records_in_file_order(self, tmp_path: pathlib.Path) -> None:
        begin1, end1 = create_transaction_pair(begin_pagination="T1")
        begin2, end2 = create_transaction_pair(begin_pagination="T5")
        values = [
            (begin1, 1, CONTEXT_BEGIN),
            (begin2, 2, CONTEXT_BEGIN),
            (end1, 1, CONTEXT_END),
            (end2, 2, CONTEXT_END),
        ]

        transactions = OcmfContainer.from_xml(write_xml(tmp_path / "t.xml", values)).transactions()

        assert {tid: [r.ocmf.payload.PG for r in rs] for tid, rs in transactions.items()} == {
            1: ["T1", "T2"],
            2: ["T5", "T6"],
        }


class TestCheckEichrecht:
    def test_transaction_is_checked_as_pair(self, transparency_xml_dir: pathlib.Path) -> None:
        xml_file = transparency_xml_dir / "test_ocmf_ebee_01.xml"

        results = OcmfContainer.from_xml(xml_file).check_eichrecht()

        assert len(results) == 1
        assert results[0].transaction_id == 15060
        assert len(results[0].records) == 2
        assert results[0].is_compliant

    def test_regression_between_records_is_an_error(
        self, transparency_xml_dir: pathlib.Path
    ) -> None:
        xml_file = transparency_xml_dir / "test_ocmf_ebee_02.xml"

        results = OcmfContainer.from_xml(xml_file).check_eichrecht()

        assert not results[0].is_compliant
        assert IssueCode.VALUE_REGRESSION in {i.code for i in results[0].issues}

    def test_records_without_transaction_are_checked_on_their_own(
        self, tmp_path: pathlib.Path
    ) -> None:
        begin, end = create_transaction_pair()
        xml = write_xml(tmp_path / "t.xml", [(begin, None, None), (end, None, None)])

        results = OcmfContainer.from_xml(xml).check_eichrecht()

        assert [(r.transaction_id, len(r.records)) for r in results] == [(None, 1), (None, 1)]

    def test_single_record_transaction_is_checked_on_its_own(self, tmp_path: pathlib.Path) -> None:
        begin, _ = create_transaction_pair()
        xml = write_xml(tmp_path / "t.xml", [(begin, 1, CONTEXT_BEGIN)])

        results = OcmfContainer.from_xml(xml).check_eichrecht()

        assert results[0].transaction_id is None
        assert results[0].issues == begin.check_eichrecht()

    def test_results_follow_file_order(self, tmp_path: pathlib.Path) -> None:
        begin, end = create_transaction_pair(begin_pagination="T1")
        other, _ = create_transaction_pair(begin_pagination="T9")
        values = [(other, None, None), (begin, 3, CONTEXT_BEGIN), (end, 3, CONTEXT_END)]

        results = OcmfContainer.from_xml(write_xml(tmp_path / "t.xml", values)).check_eichrecht()

        assert [r.transaction_id for r in results] == [None, 3]

    @pytest.mark.parametrize("errors_only", [True, False])
    def test_errors_only(self, tmp_path: pathlib.Path, errors_only: bool) -> None:
        begin, end = create_transaction_pair(
            begin_timestamp="2023-01-01T12:00:00,000+0000 I",
            end_value=decimal.Decimal(10),
        )
        xml = write_xml(tmp_path / "t.xml", [(begin, 1, CONTEXT_BEGIN), (end, 1, CONTEXT_END)])

        issues = OcmfContainer.from_xml(xml).check_eichrecht(errors_only=errors_only)[0].issues

        severities = {i.severity for i in issues}
        assert IssueSeverity.ERROR in severities
        assert (IssueSeverity.WARNING in severities) is not errors_only
