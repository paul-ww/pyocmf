from __future__ import annotations

from typing import Literal

import pydantic

from pyocmf import compliance
from pyocmf.compliance.models import EichrechtIssue, IssueSeverity
from pyocmf.constants import OCMF_HEADER, OCMF_PREFIX, OCMF_SEPARATOR
from pyocmf.core.payload import Payload
from pyocmf.core.signature import Signature
from pyocmf.crypto import verification
from pyocmf.exceptions import (
    HexDecodingError,
    OcmfFormatError,
    OcmfPayloadError,
    OcmfSignatureError,
    SignatureVerificationError,
)
from pyocmf.models.public_key import PublicKey


class OCMF(pydantic.BaseModel):
    """OCMF data model with three pipe-separated sections: header, payload, and signature."""

    header: Literal["OCMF"]
    payload: Payload
    signature: Signature
    _original_payload_json: str | None = pydantic.PrivateAttr(default=None)

    @classmethod
    def from_string(cls, ocmf_string: str) -> OCMF:
        """Parse an OCMF string into an OCMF model.

        Automatically detects whether the input is plain text (starts with "OCMF|")
        or hex-encoded and handles both formats.
        """
        ocmf_text = ocmf_string.strip()

        if not ocmf_text.startswith(OCMF_PREFIX):
            try:
                decoded_bytes = bytes.fromhex(ocmf_text)
                ocmf_text = decoded_bytes.decode("utf-8")
            except ValueError as e:
                msg = (
                    f"Invalid OCMF string: must start with '{OCMF_PREFIX}' or be "
                    f"valid hex-encoded. {e}"
                )
                raise HexDecodingError(msg) from e
        parts = ocmf_text.split(OCMF_SEPARATOR, 2)

        if len(parts) != 3 or parts[0] != OCMF_HEADER:
            msg = (
                f"String does not match expected OCMF format "
                f"'{OCMF_HEADER}{OCMF_SEPARATOR}{{payload}}{OCMF_SEPARATOR}{{signature}}'."
            )
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
        """Convert the OCMF model to string format "OCMF|{payload}|{signature}".

        Set hex=True to return hex-encoded string instead of plain text.
        """
        payload_json = self.payload.model_dump_json(exclude_none=True)
        signature_json = self.signature.model_dump_json(exclude_none=True)
        ocmf_string = OCMF_SEPARATOR.join([OCMF_HEADER, payload_json, signature_json])

        if hex:
            return ocmf_string.encode("utf-8").hex()
        return ocmf_string

    def verify_signature(self, public_key: PublicKey | str) -> bool:
        """Verify the cryptographic signature of the OCMF data.

        Per OCMF spec, public keys must be transmitted out-of-band (separately from OCMF data).
        Requires that the OCMF was parsed from a string (not constructed programmatically)
        because signature verification needs the exact original payload bytes.
        """
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
            public_key_hex=public_key.key if isinstance(public_key, PublicKey) else public_key,
        )

    def check_eichrecht(
        self, other: OCMF | None = None, *, errors_only: bool = False
    ) -> list[EichrechtIssue]:
        """Check German calibration law (Eichrecht) compliance.

        Validates that OCMF data complies with German Eichrecht requirements
        (MID 2014/32/EU and PTB) for billing-relevant meter readings.

        Provide 'other' OCMF to check transaction pair (begin + end).
        Set errors_only=True to filter out warnings.
        """
        if other is None:
            if not self.payload.RD:
                return [
                    EichrechtIssue(
                        code=compliance.IssueCode.NO_READINGS,
                        message="No readings (RD) present in payload",
                        field="RD",
                    )
                ]

            issues = []
            for i, reading in enumerate(self.payload.RD):
                reading_issues = compliance.check_eichrecht_reading(
                    reading, is_begin=(i == 0 and reading.TX.value == "B")
                )
                issues.extend(reading_issues)
        else:
            issues = compliance.check_eichrecht_transaction(self.payload, other.payload)

        if errors_only:
            issues = [issue for issue in issues if issue.severity == IssueSeverity.ERROR]

        return issues

    @property
    def is_eichrecht_compliant(self) -> bool:
        issues = self.check_eichrecht(errors_only=True)
        return len(issues) == 0

    def verify(
        self,
        public_key: PublicKey | str,
        other: OCMF | None = None,
        eichrecht: bool = True,
    ) -> tuple[bool, list[EichrechtIssue]]:
        """Verify both cryptographic signature and legal compliance.

        Combines signature verification and Eichrecht compliance checking.
        Returns (signature_valid, compliance_issues).
        Set eichrecht=False to skip compliance checking.
        """
        signature_valid = self.verify_signature(public_key)
        compliance_issues = self.check_eichrecht(other) if eichrecht else []
        return signature_valid, compliance_issues
