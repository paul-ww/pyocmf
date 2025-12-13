from __future__ import annotations

import json
from typing import Literal

import pydantic

from pyocmf.exceptions import OcmfFormatError, OcmfPayloadError, OcmfSignatureError
from pyocmf.sections.payload import Payload
from pyocmf.sections.signature import Signature


class OCMF(pydantic.BaseModel):
    header: Literal["OCMF"]
    payload: Payload
    signature: Signature

    @classmethod
    def from_string(cls, ocmf_string: str) -> OCMF:
        """Parse an OCMF string into an OCMF model.

        Args:
            ocmf_string: The OCMF string in format "OCMF|{payload_json}|{signature_json}"

        Returns:
            OCMF: The parsed OCMF model

        Raises:
            OcmfFormatError: If the string is not in valid OCMF format
            OcmfPayloadError: If the payload cannot be parsed
            OcmfSignatureError: If the signature cannot be parsed
        """
        ocmf_text = ocmf_string.strip()
        parts = ocmf_text.split("|", 2)

        if len(parts) != 3 or parts[0] != "OCMF":
            msg = "String does not match expected OCMF format 'OCMF|{payload}|{signature}'."
            raise OcmfFormatError(msg)

        payload_json = parts[1]
        signature_json = parts[2]

        try:
            payload = Payload.from_flat_dict(json.loads(payload_json))
        except (json.JSONDecodeError, ValueError) as e:
            msg = f"Invalid payload JSON: {e}"
            raise OcmfPayloadError(msg) from e

        try:
            signature = Signature.model_validate_json(signature_json)
        except (json.JSONDecodeError, pydantic.ValidationError) as e:
            msg = f"Invalid signature JSON: {e}"
            raise OcmfSignatureError(msg) from e

        return cls(header="OCMF", payload=payload, signature=signature)

    def to_string(self) -> str:
        """Convert the OCMF model to its string representation.

        Returns:
            str: The OCMF string in format "OCMF|{payload_json}|{signature_json}"
        """
        payload_json = self.payload.to_flat_dict_json()
        signature_json = self.signature.model_dump_json()

        return f"OCMF|{payload_json}|{signature_json}"
