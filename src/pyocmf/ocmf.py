from __future__ import annotations
import pathlib
import xml.etree.ElementTree as ET
import json

import pydantic
from typing import Literal
from pyocmf.sections.payload import Payload
from pyocmf.sections.signature import Signature

class OCMF(pydantic.BaseModel):
    header: Literal["OCMF"]
    payload: Payload
    signature: Signature

    @classmethod
    def from_xml(cls, xml_path: pathlib.Path) -> OCMF:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the first signedData element with format="OCMF"
        signed_data_elem = None
        for value_elem in root.findall("value"):
            sd = value_elem.find("signedData")
            if sd is not None and sd.get("format") == "OCMF":
                signed_data_elem = sd
                break
        if signed_data_elem is None:
            raise ValueError("No signedData element with format='OCMF' found.")

        if signed_data_elem.text is None:
            raise ValueError("signedData element is empty.")
        # Parse the signedData string: OCMF|{payload_json}|{signature_json}
        parts = signed_data_elem.text.split("|", 2)
        if len(parts) != 3 or parts[0] != "OCMF":
            raise ValueError("signedData does not match expected OCMF format.")
        header = parts[0]
        payload_json = parts[1]
        signature_json = parts[2]

        payload = Payload.from_flat_dict(json.loads(payload_json))
        signature = Signature.model_validate_json(signature_json)

        return cls(header=header, payload=payload, signature=signature)