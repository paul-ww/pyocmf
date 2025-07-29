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

        # Also check for encodedData with format="OCMF"
        if signed_data_elem is None:
            for value_elem in root.findall("value"):
                ed = value_elem.find("encodedData")
                if ed is not None and ed.get("format") == "OCMF":
                    # Try to decode hex-encoded OCMF data
                    encoding = ed.get("encoding", "").lower()
                    if encoding == "hex":
                        if ed.text is None:
                            raise ValueError("encodedData element is empty.")
                        try:
                            # Decode hex to bytes
                            decoded_bytes = bytes.fromhex(ed.text.strip())
                            # Try to decode as UTF-8 text
                            decoded_text = decoded_bytes.decode("utf-8")
                            # Check if it contains OCMF format
                            if decoded_text.strip().startswith("OCMF|"):
                                # Create a temporary element for the decoded text
                                signed_data_elem = ET.Element("signedData")
                                signed_data_elem.text = decoded_text.strip()
                                break
                            else:
                                raise ValueError(
                                    "Hex-decoded data does not contain valid OCMF format."
                                )
                        except (ValueError, UnicodeDecodeError) as e:
                            # If hex decoding fails or the result isn't valid OCMF text,
                            # this might be a more complex encoding (e.g., ASN.1/DER wrapped)
                            raise ValueError(
                                f"Failed to decode hex-encoded OCMF data: {e}. This may be ASN.1/DER encoded data which requires specialized parsing."
                            )
                    else:
                        raise ValueError(
                            f"Unsupported encoding for OCMF data: {encoding}"
                        )

        # Fallback: if no signedData with format="OCMF" found, 
        # look for any signedData that contains OCMF data
        if signed_data_elem is None:
            for value_elem in root.findall("value"):
                sd = value_elem.find("signedData")
                if sd is not None and sd.text is not None and sd.text.strip().startswith("OCMF|"):
                    signed_data_elem = sd
                    break
        
        if signed_data_elem is None:
            raise ValueError("No signedData element with OCMF content found.")

        if signed_data_elem.text is None:
            raise ValueError("signedData element is empty.")
        
        # Clean and parse the signedData string: OCMF|{payload_json}|{signature_json}
        ocmf_text = signed_data_elem.text.strip()
        parts = ocmf_text.split("|", 2)
        if len(parts) != 3 or parts[0] != "OCMF":
            raise ValueError("signedData does not match expected OCMF format.")
        payload_json = parts[1]
        signature_json = parts[2]

        payload = Payload.from_flat_dict(json.loads(payload_json))
        signature = Signature.model_validate_json(signature_json)

        return cls(header="OCMF", payload=payload, signature=signature)