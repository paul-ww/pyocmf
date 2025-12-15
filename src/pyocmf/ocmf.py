"""OCMF (Open Charge Metering Format) parser and validator.

This module provides the main OCMF class for parsing and validating OCMF strings.
"""

from __future__ import annotations

from typing import Literal

import pydantic

from pyocmf.constants import OCMF_HEADER, OCMF_PREFIX, OCMF_SEPARATOR
from pyocmf.exceptions import (
    HexDecodingError,
    OcmfFormatError,
    OcmfPayloadError,
    OcmfSignatureError,
    SignatureVerificationError,
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
    def from_string(cls, ocmf_string: str) -> OCMF:
        """Parse an OCMF string into an OCMF model.

        Automatically detects whether the input is a plain OCMF string or
        hex-encoded and handles both formats.

        Args:
            ocmf_string: The OCMF string in format "OCMF|{payload_json}|{signature_json}"
                or a hex-encoded version of that format.

        Returns:
            OCMF: The parsed OCMF model

        Raises:
            HexDecodingError: If the string appears to be hex but cannot be decoded
            OcmfFormatError: If the string is not in valid OCMF format
            OcmfPayloadError: If the payload cannot be parsed
            OcmfSignatureError: If the signature cannot be parsed
        """
        ocmf_text = ocmf_string.strip()

        # Auto-detect hex encoding: if it doesn't start with "OCMF|", try hex decoding
        if not ocmf_text.startswith(OCMF_PREFIX):
            try:
                decoded_bytes = bytes.fromhex(ocmf_text)
                ocmf_text = decoded_bytes.decode("utf-8")
            except ValueError as e:
                msg = f"Invalid OCMF string: must start with '{OCMF_PREFIX}' or be valid hex-encoded. {e}"
                raise HexDecodingError(msg) from e
        parts = ocmf_text.split(OCMF_SEPARATOR, 2)

        if len(parts) != 3 or parts[0] != OCMF_HEADER:
            msg = f"String does not match expected OCMF format '{OCMF_HEADER}{OCMF_SEPARATOR}{{payload}}{OCMF_SEPARATOR}{{signature}}'."
            raise OcmfFormatError(msg)

        payload_json = parts[1]
        signature_json = parts[2]

        try:
            payload = Payload.model_validate_json(payload_json)
        except pydantic.ValidationError as e:
            msg = f"Invalid payload JSON: {e}"
            raise OcmfPayloadError(msg) from e

        try:
            signature = Signature.model_validate_json(signature_json)
        except pydantic.ValidationError as e:
            msg = f"Invalid signature JSON: {e}"
            raise OcmfSignatureError(msg) from e

        ocmf = cls(header=OCMF_HEADER, payload=payload, signature=signature)
        ocmf._original_payload_json = payload_json
        return ocmf

    def to_string(self, hex: bool = False) -> str:
        """Convert the OCMF model to its string representation.

        Args:
            hex: If True, return hex-encoded string. Defaults to False.

        Returns:
            str: The OCMF string in format "OCMF|{payload_json}|{signature_json}",
                or hex-encoded if hex=True.
        """
        payload_json = self.payload.model_dump_json(exclude_none=True)
        signature_json = self.signature.model_dump_json(exclude_none=True)
        ocmf_string = OCMF_SEPARATOR.join([OCMF_HEADER, payload_json, signature_json])

        if hex:
            return ocmf_string.encode("utf-8").hex()
        return ocmf_string

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
                missing data, unsupported algorithms, malformed keys/signatures,
                or if the OCMF was not parsed from a string (original payload required).
        """
        from pyocmf import verification

        if self._original_payload_json is None:
            msg = (
                "Cannot verify signature: original payload JSON not available. "
                "Signature verification requires the exact original payload bytes. "
                "Use OCMF.from_string() to parse OCMF data for signature verification."
            )
            raise SignatureVerificationError(msg)

        return verification.verify_signature(
            payload_json=self._original_payload_json,
            signature_data=self.signature.SD,
            signature_method=self.signature.SA,
            signature_encoding=self.signature.SE,
            public_key_hex=public_key_hex,
        )
