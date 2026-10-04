from __future__ import annotations

import pathlib
from collections.abc import Iterator
from dataclasses import dataclass
from xml.etree.ElementTree import Element  # ruff: ignore[suspicious-xml-etree-import]

import defusedxml.ElementTree as ET  # ruff: ignore[camelcase-imported-as-acronym]

from pyocmf.constants import OCMF_HEADER, OCMF_PREFIX
from pyocmf.core.ocmf import OCMF
from pyocmf.exceptions import (
    DataNotFoundError,
    PublicKeyError,
    SignatureVerificationError,
    XmlParsingError,
)
from pyocmf.models.public_key import PublicKey


@dataclass
class OcmfRecord:
    """An OCMF record from an XML file, with the public key stored next to it, if any."""

    ocmf: OCMF
    public_key: PublicKey | None = None

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
                public_key = _extract_public_key(value_elem)
                entries.append(OcmfRecord(ocmf=ocmf, public_key=public_key))
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
