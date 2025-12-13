"""XML parsing utilities for extracting OCMF data from transparency software XML files."""

from __future__ import annotations

import pathlib
import xml.etree.ElementTree as ET

from pyocmf.exceptions import DataNotFoundError, XmlParsingError
from pyocmf.ocmf import OCMF


def extract_ocmf_strings_from_file(xml_path: pathlib.Path) -> list[str]:
    """Extract all OCMF strings from an XML file.

    Args:
        xml_path: Path to the XML file

    Returns:
        List[str]: List of OCMF strings found in the XML file

    Raises:
        XmlParsingError: If the XML file cannot be parsed
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        msg = f"Failed to parse XML file: {e}"
        raise XmlParsingError(msg) from e

    ocmf_strings = []

    for value_elem in root.findall("value"):
        sd = value_elem.find("signedData")
        if sd is not None and sd.get("format") == "OCMF" and sd.text:
            ocmf_strings.append(sd.text.strip())

    for value_elem in root.findall("value"):
        ed = value_elem.find("encodedData")
        if ed is not None and ed.get("format") == "OCMF" and ed.text:
            encoding = ed.get("encoding", "").lower()
            if encoding == "hex":
                try:
                    decoded_bytes = bytes.fromhex(ed.text.strip())
                    decoded_text = decoded_bytes.decode("utf-8")
                    if decoded_text.strip().startswith("OCMF|"):
                        ocmf_strings.append(decoded_text.strip())
                except (ValueError, UnicodeDecodeError):
                    continue

    for value_elem in root.findall("value"):
        sd = value_elem.find("signedData")
        if (
            sd is not None
            and sd.text is not None
            and sd.text.strip().startswith("OCMF|")
            and sd.text.strip() not in ocmf_strings
        ):
            ocmf_strings.append(sd.text.strip())

    return ocmf_strings


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
    ocmf_strings = extract_ocmf_strings_from_file(xml_path)

    if not ocmf_strings:
        msg = "No OCMF data found in XML file."
        raise DataNotFoundError(msg)

    return OCMF.from_string(ocmf_strings[0])


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

    results = []
    for _i, ocmf_string in enumerate(ocmf_strings):
        results.append(OCMF.from_string(ocmf_string))

    return results
