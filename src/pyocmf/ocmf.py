from __future__ import annotations
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
    def from_string(cls, ocmf_string: str) -> "OCMF":
        """Parse an OCMF string into an OCMF model.
        
        Args:
            ocmf_string: The OCMF string in format "OCMF|{payload_json}|{signature_json}"
            
        Returns:
            OCMF: The parsed OCMF model
            
        Raises:
            ValueError: If the string is not in valid OCMF format
        """
        ocmf_text = ocmf_string.strip()
        parts = ocmf_text.split("|", 2)
        
        if len(parts) != 3 or parts[0] != "OCMF":
            raise ValueError("String does not match expected OCMF format 'OCMF|{payload}|{signature}'.")
            
        payload_json = parts[1]
        signature_json = parts[2]

        try:
            payload = Payload.from_flat_dict(json.loads(payload_json))
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid payload JSON: {e}")
            
        try:
            signature = Signature.model_validate_json(signature_json)
        except (json.JSONDecodeError, pydantic.ValidationError) as e:
            raise ValueError(f"Invalid signature JSON: {e}")

        return cls(header="OCMF", payload=payload, signature=signature)
    
    def to_string(self) -> str:
        """Convert the OCMF model to its string representation.
        
        Returns:
            str: The OCMF string in format "OCMF|{payload_json}|{signature_json}"
        """
        payload_json = self.payload.to_flat_dict_json()
        signature_json = self.signature.model_dump_json()
        
        return f"OCMF|{payload_json}|{signature_json}"

    @classmethod
    def from_xml(cls, xml_path) -> "OCMF":
        """Parse an OCMF model from an XML file.
        
        This method is deprecated. Use xml_parser.parse_ocmf_from_xml() instead.
        
        Args:
            xml_path: Path to the XML file
            
        Returns:
            OCMF: The parsed OCMF model
        """
        import warnings
        from pathlib import Path
        from pyocmf.xml_parser import parse_ocmf_from_xml
        
        warnings.warn(
            "OCMF.from_xml() is deprecated. Use pyocmf.xml_parser.parse_ocmf_from_xml() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        return parse_ocmf_from_xml(Path(xml_path))