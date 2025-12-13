import pathlib
import xml.etree.ElementTree as ET
from typing import List, Optional

from pyocmf.exceptions import XmlParsingError


class SignedData:
    def __init__(self, element: ET.Element):
        self.format = element.get("format")
        self.encoding = element.get("encoding")
        self.transaction_id = element.get("transactionId")
        self.text = element.text


class PublicKey:
    def __init__(self, element: ET.Element):
        self.encoding = element.get("encoding")
        self.text = element.text


class Value:
    def __init__(self, element: ET.Element):
        self.transaction_id = element.get("transactionId")
        self.context = element.get("context")
        self.signed_data = None
        self.public_key = None
        for child in element:
            if child.tag == "signedData":
                self.signed_data = SignedData(child)
            elif child.tag == "publicKey":
                self.public_key = PublicKey(child)


class TransparencyXML:
    def __init__(self, xml_path: pathlib.Path):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise XmlParsingError(f"Failed to parse XML file: {e}") from e
        if root.tag != "values":
            raise XmlParsingError("Root element must be <values>")
        self.values: List[Value] = [Value(elem) for elem in root.findall("value")]

    def get_datasets(self) -> List[Value]:
        return self.values

    def get_signed_data(self, format_filter: Optional[str] = None) -> List[SignedData]:
        result = []
        for value in self.values:
            if value.signed_data:
                if format_filter is None or value.signed_data.format == format_filter:
                    result.append(value.signed_data)
        return result

    def get_public_keys(self) -> List[PublicKey]:
        return [v.public_key for v in self.values if v.public_key]
