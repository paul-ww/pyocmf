from __future__ import annotations

import pathlib
from collections.abc import Iterator
from dataclasses import dataclass, field
from xml.etree.ElementTree import Element  # ruff: ignore[suspicious-xml-etree-import]

import defusedxml.ElementTree as ET  # ruff: ignore[camelcase-imported-as-acronym]

from pyocmf.compliance.models import EichrechtIssue, IssueCode, IssueSeverity
from pyocmf.constants import OCMF_HEADER, OCMF_PREFIX
from pyocmf.core.ocmf import OCMF
from pyocmf.exceptions import (
    DataNotFoundError,
    PublicKeyError,
    SignatureVerificationError,
    XmlParsingError,
)
from pyocmf.models.public_key import PublicKey

CONTEXT_BEGIN = "Transaction.Begin"
CONTEXT_END = "Transaction.End"


@dataclass
class OcmfRecord:
    """An OCMF record from an XML file, with the public key stored next to it, if any.

    ``transaction_id`` and ``context`` come from the ``transactionId`` and ``context``
    attributes of the XML value. The Transparenzsoftware uses them to pair the begin
    and end record of a transaction.
    """

    ocmf: OCMF
    public_key: PublicKey | None = None
    transaction_id: int | None = None
    context: str | None = None

    def verify_signature(self) -> bool:
        """Verify with the record's public key, or else a key embedded in the OCMF string.

        Raises:
            SignatureVerificationError: If no key is available or the signature cannot
                be checked

        """
        if self.public_key is None and self.ocmf.embedded_public_key is None:
            msg = "No public key available for signature verification"
            raise SignatureVerificationError(msg)

        return self.ocmf.verify_signature(self.public_key)


@dataclass
class EichrechtResult:
    """Eichrecht issues of one transaction, or of one record checked on its own."""

    records: list[OcmfRecord]
    issues: list[EichrechtIssue] = field(default_factory=list)
    transaction_id: int | None = None

    @property
    def is_compliant(self) -> bool:
        """Whether none of the issues is an error."""
        return not any(issue.severity == IssueSeverity.ERROR for issue in self.issues)


class OcmfContainer:
    """OCMF records read from a Transparenzsoftware XML file, in file order.

    Records that occur more than once are kept once. Supports ``len()``, iteration
    and indexing.
    """

    def __init__(self, entries: list[OcmfRecord]) -> None:
        self._entries = entries

    @classmethod
    def from_xml(cls, xml_path: pathlib.Path | str, *, strict: bool = False) -> OcmfContainer:
        """Parse OCMF data from an XML file.

        Args:
            xml_path: Path to the XML file
            strict: Reject OCMF records that deviate from the spec instead of warning

        Returns:
            OcmfContainer with parsed OCMF entries

        Raises:
            XmlParsingError: If the XML file cannot be parsed
            DataNotFoundError: If no OCMF data is found

        """
        path = pathlib.Path(xml_path)

        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except ET.ParseError as e:
            msg = f"Failed to parse XML file: {e}"
            raise XmlParsingError(msg) from e

        entries = []
        seen_strings: set[str] = set()

        for value_elem in root.findall("value"):
            ocmf_str = _extract_ocmf_string(value_elem)

            if ocmf_str and ocmf_str not in seen_strings:
                ocmf = OCMF.from_string(ocmf_str, strict=strict)
                entries.append(
                    OcmfRecord(
                        ocmf=ocmf,
                        public_key=_extract_public_key(value_elem),
                        transaction_id=_parse_transaction_id(value_elem.get("transactionId")),
                        context=(value_elem.get("context") or "").strip() or None,
                    )
                )
                seen_strings.add(ocmf_str)

        if not entries:
            msg = "No OCMF data found in XML file"
            raise DataNotFoundError(msg)

        return cls(entries)

    @property
    def entries(self) -> list[OcmfRecord]:
        """The records as a list."""
        return self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[OcmfRecord]:
        return iter(self._entries)

    def __getitem__(self, index: int) -> OcmfRecord:
        return self._entries[index]

    def transactions(self) -> dict[int, list[OcmfRecord]]:
        """Group the records by their transaction ID, in file order."""
        groups: dict[int, list[OcmfRecord]] = {}
        for record in self._entries:
            if record.transaction_id is not None:
                groups.setdefault(record.transaction_id, []).append(record)
        return groups

    def check_eichrecht(self, *, errors_only: bool = False) -> list[EichrechtResult]:
        """Check Eichrecht compliance of the file, as the Transparenzsoftware does.

        Records sharing a transaction ID form a transaction. It needs exactly one
        record with the context ``Transaction.Begin`` and one with ``Transaction.End``,
        which are checked as a begin/end pair. Every other record is checked on its own.

        Args:
            errors_only: Leave out warnings

        Returns:
            One result per transaction or standalone record, in file order

        """
        transactions = {tid: rs for tid, rs in self.transactions().items() if len(rs) > 1}
        results: list[EichrechtResult] = []
        for record in self._entries:
            tid = record.transaction_id
            if tid is None or tid not in transactions:
                results.append(EichrechtResult([record], record.ocmf.check_eichrecht()))
            elif record is transactions[tid][0]:
                results.append(_check_transaction(tid, transactions[tid]))

        if errors_only:
            for result in results:
                result.issues = [i for i in result.issues if i.severity == IssueSeverity.ERROR]
        return results


def _check_transaction(transaction_id: int, records: list[OcmfRecord]) -> EichrechtResult:
    begins = [r for r in records if r.context == CONTEXT_BEGIN]
    ends = [r for r in records if r.context == CONTEXT_END]
    issues = [
        *_context_count_issues(begins, CONTEXT_BEGIN, IssueCode.BEGIN_TX, IssueCode.MULTIPLE_BEGIN),
        *_context_count_issues(ends, CONTEXT_END, IssueCode.END_TX, IssueCode.MULTIPLE_END),
    ]
    # Like the Transparenzsoftware, a transaction without one begin and one end is not
    # checked any further
    if not issues:
        issues = begins[0].ocmf.check_eichrecht(ends[0].ocmf)
    return EichrechtResult(records, issues, transaction_id)


def _context_count_issues(
    records: list[OcmfRecord], context: str, missing: IssueCode, multiple: IssueCode
) -> list[EichrechtIssue]:
    if len(records) == 1:
        return []
    message = (
        f"No record with context '{context}' in the transaction"
        if not records
        else f"Expected one record with context '{context}', found {len(records)}"
    )
    return [EichrechtIssue(code=missing if not records else multiple, message=message)]


def _parse_transaction_id(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def _extract_ocmf_string(element: Element) -> str | None:
    sd = element.find("signedData")
    if sd is not None and sd.text:
        text = sd.text.strip()
        if sd.get("format") == OCMF_HEADER or text.startswith(OCMF_PREFIX):
            return text

    ed = element.find("encodedData")
    if ed is not None and ed.get("format") == OCMF_HEADER and ed.text:
        return ed.text.strip()

    return None


def _extract_public_key(element: Element) -> PublicKey | None:
    pk = element.find("publicKey")
    if pk is not None and pk.text:
        try:
            key_str = "".join(pk.text.split())
            return PublicKey.from_string(key_str)
        except (ImportError, ValueError, PublicKeyError):
            return None
    return None
