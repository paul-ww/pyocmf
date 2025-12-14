"""OCMF (Open Charge Metering Format) parser and validator.

This module provides the main OCMF class for parsing and validating OCMF strings.
"""

from __future__ import annotations

import json
from typing import Literal

import pydantic

from pyocmf.exceptions import (
    HexDecodingError,
    OcmfFormatError,
    OcmfPayloadError,
    OcmfSignatureError,
)
from pyocmf.sections.payload import Payload
from pyocmf.sections.signature import Signature


class OCMF(pydantic.BaseModel):
    """OCMF data model representing the complete OCMF structure.

    The OCMF format consists of three pipe-separated sections:
    - Header: Always "OCMF"
    - Payload: JSON object containing meter readings and metadata
    - Signature: JSON object containing cryptographic signature data
    """

    header: Literal["OCMF"]
    payload: Payload
    signature: Signature
    _original_payload_json: str | None = pydantic.PrivateAttr(default=None)

    @classmethod
    def from_hex(cls, ocmf_hex: str) -> OCMF:
        """Parse a hex-encoded OCMF string into an OCMF model.

        Args:
            ocmf_hex: The hex-encoded OCMF string
        Returns:
            OCMF: The parsed OCMF model
        Raises:
            HexDecodingError: If the string is not valid hexadecimal
        """
        try:
            decoded_bytes = bytes.fromhex(ocmf_hex.strip())
            decoded_string = decoded_bytes.decode("utf-8")
        except ValueError as e:
            msg = f"Invalid hex-encoded OCMF string: {e}"
            raise HexDecodingError(msg) from e

        return cls.from_string(decoded_string)

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

        ocmf = cls(header="OCMF", payload=payload, signature=signature)
        ocmf._original_payload_json = payload_json
        return ocmf

    def to_string(self) -> str:
        """Convert the OCMF model to its string representation.

        Returns:
            str: The OCMF string in format "OCMF|{payload_json}|{signature_json}"
        """
        payload_json = self.payload.to_flat_dict_json()
        signature_json = self.signature.model_dump_json()

        return f"OCMF|{payload_json}|{signature_json}"

    def to_hex(self) -> str:
        """Convert the OCMF model to its hex-encoded string representation.

        Returns:
            str: The hex-encoded OCMF string
        """
        ocmf_string = self.to_string()
        ocmf_bytes = ocmf_string.encode("utf-8")
        return ocmf_bytes.hex()

    def verify_signature(self, public_key_hex: str) -> bool:
        """Verify the cryptographic signature of the OCMF data.

        Args:
            public_key_hex: Hex-encoded public key (required per OCMF spec).
                The spec requires public keys to be transmitted out-of-band,
                separately from the OCMF data.

        Returns:
            bool: True if signature is valid, False otherwise

        Raises:
            SignatureVerificationError: If verification cannot be performed due to
                missing data, unsupported algorithms, or malformed keys/signatures
        """
        payload_json = self._original_payload_json or self.payload.to_flat_dict_json()
        return self.signature.verify(payload_json, public_key_hex)
