"""XML parsing utilities for extracting OCMF data from transparency software XML files."""

from __future__ import annotations

import pathlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from pyocmf.exceptions import DataNotFoundError, XmlParsingError
from pyocmf.ocmf import OCMF
from pyocmf.types.public_key import PublicKey


@dataclass
class OcmfXmlData:
    """Container for OCMF data and associated metadata from XML files.

    The public_key_info field contains structured public key metadata per OCMF
    spec Table 23, including the curve type, key size, and hex-encoded key data.
    """

    ocmf_string: str
    public_key: PublicKey | None = None


def _extract_from_signed_data(value_elem: ET.Element) -> str | None:
    """Extract OCMF string from signedData element with format='OCMF'."""
    sd = value_elem.find("signedData")
    if sd is not None and sd.get("format") == "OCMF" and sd.text:
        return sd.text.strip()
    return None


def _extract_from_encoded_data(value_elem: ET.Element) -> str | None:
    """Extract OCMF string from hex-encoded encodedData element."""
    ed = value_elem.find("encodedData")
    if ed is not None and ed.get("format") == "OCMF" and ed.text:
        encoding = ed.get("encoding", "").lower()
        if encoding == "hex":
            try:
                decoded_bytes = bytes.fromhex(ed.text.strip())
                decoded_text = decoded_bytes.decode("utf-8")
                if decoded_text.strip().startswith("OCMF|"):
                    return decoded_text.strip()
            except (ValueError, UnicodeDecodeError):
                pass
    return None


def _extract_from_any_signed_data(value_elem: ET.Element) -> str | None:
    """Extract OCMF string from any signedData element containing OCMF data."""
    sd = value_elem.find("signedData")
    if sd is not None and sd.text is not None and sd.text.strip().startswith("OCMF|"):
        return sd.text.strip()
    return None


def _extract_public_key_hex(value_elem: ET.Element) -> str | None:
    """Extract public key hex string from publicKey element."""
    pk = value_elem.find("publicKey")
    if pk is not None and pk.text:
        encoding = pk.get("encoding", "").lower()
        if encoding == "hex":
            return pk.text.strip()
    return None


def _extract_public_key(value_elem: ET.Element) -> PublicKey | None:
    """Extract public key with metadata from publicKey element.

    Returns None if cryptography is not installed or key cannot be parsed.
    """
    public_key_hex = _extract_public_key_hex(value_elem)
    if public_key_hex is None:
        return None

    try:
        return PublicKey.from_hex(public_key_hex)
    except (ImportError, ValueError):
        # If cryptography not installed or key parsing fails, return None
        # The raw hex string is still available in OcmfXmlData.public_key
        return None


def extract_ocmf_data_from_file(xml_path: pathlib.Path) -> list[OcmfXmlData]:
    """Extract all OCMF data (strings and public keys) from an XML file.

    Args:
        xml_path: Path to the XML file

    Returns:
        List[OcmfXmlData]: List of OCMF data with associated public keys

    Raises:
        XmlParsingError: If the XML file cannot be parsed
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        msg = f"Failed to parse XML file: {e}"
        raise XmlParsingError(msg) from e

    ocmf_data_list = []
    seen_strings = set()

    for value_elem in root.findall("value"):
        ocmf_str = (
            _extract_from_signed_data(value_elem)
            or _extract_from_encoded_data(value_elem)
            or _extract_from_any_signed_data(value_elem)
        )

        if ocmf_str and ocmf_str not in seen_strings:
            public_key = _extract_public_key(value_elem)
            ocmf_data_list.append(OcmfXmlData(ocmf_string=ocmf_str, public_key=public_key))
            seen_strings.add(ocmf_str)

    return ocmf_data_list


def extract_ocmf_strings_from_file(xml_path: pathlib.Path) -> list[str]:
    """Extract all OCMF strings from an XML file.

    Args:
        xml_path: Path to the XML file

    Returns:
        List[str]: List of OCMF strings found in the XML file

    Raises:
        XmlParsingError: If the XML file cannot be parsed
    """
    return [data.ocmf_string for data in extract_ocmf_data_from_file(xml_path)]


def parse_ocmf_from_xml(xml_path: pathlib.Path) -> OCMF:
    """Parse the first OCMF string found in an XML file.

    Args:
        xml_path: Path to the XML file

    Returns:
        OCMF: The parsed OCMF model

    Raises:
        DataNotFoundError: If no OCMF data is found
        XmlParsingError: If XML parsing fails
    """
    ocmf_data_list = extract_ocmf_data_from_file(xml_path)

    if not ocmf_data_list:
        msg = "No OCMF data found in XML file."
        raise DataNotFoundError(msg)

    return OCMF.from_string(ocmf_data_list[0].ocmf_string)


def parse_ocmf_with_key_from_xml(xml_path: pathlib.Path) -> tuple[OCMF, str | None]:
    """Parse the first OCMF string and public key from an XML file.

    Args:
        xml_path: Path to the XML file

    Returns:
        Tuple[OCMF, str | None]: The parsed OCMF model and optional public key hex string

    Raises:
        DataNotFoundError: If no OCMF data is found
        XmlParsingError: If XML parsing fails
    """
    ocmf_data_list = extract_ocmf_data_from_file(xml_path)

    if not ocmf_data_list:
        msg = "No OCMF data found in XML file."
        raise DataNotFoundError(msg)

    data = ocmf_data_list[0]
    public_key_hex = data.public_key.key_hex if data.public_key else None
    return OCMF.from_string(data.ocmf_string), public_key_hex


def parse_all_ocmf_from_xml(xml_path: pathlib.Path) -> list[OCMF]:
    """Parse all OCMF strings found in an XML file.

    Args:
        xml_path: Path to the XML file

    Returns:
        List[OCMF]: List of parsed OCMF models

    Raises:
        DataNotFoundError: If no OCMF data is found
        XmlParsingError: If XML parsing fails
    """
    ocmf_strings = extract_ocmf_strings_from_file(xml_path)

    if not ocmf_strings:
        msg = "No OCMF data found in XML file."
        raise DataNotFoundError(msg)

    return [OCMF.from_string(ocmf_str) for ocmf_str in ocmf_strings]
