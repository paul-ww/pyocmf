from __future__ import annotations

from typing import Any


class PyOCMFError(Exception):
    """Base class for all pyocmf errors; ``field`` names the OCMF field involved."""

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.field = field
        self.details = details


class XmlParsingError(PyOCMFError):
    """The XML file is not well-formed."""


class DataNotFoundError(PyOCMFError):
    """The XML file contains no OCMF data."""


class OcmfFormatError(PyOCMFError):
    """The string is not structured as OCMF, or carries an appended key in strict mode."""


class OcmfPayloadError(PyOCMFError):
    """The payload section is not valid JSON or fails validation."""


class OcmfSignatureError(PyOCMFError):
    """The signature section is not valid JSON or fails validation."""


class EncodingError(PyOCMFError, ValueError):
    """Base class for errors decoding hex or base64 data."""

    def __init__(
        self,
        message: str,
        *,
        value: str | None = None,
        field: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message, field=field, details=details)
        self.value = value


class HexDecodingError(EncodingError):
    """Data is not valid hex."""


class Base64DecodingError(EncodingError):
    """Data is not valid base64."""


class EncodingTypeError(PyOCMFError, TypeError):
    """Data to decode is not a string."""

    def __init__(
        self,
        message: str,
        *,
        value: object = None,
        expected_type: str | None = None,
        field: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message, field=field, details=details)
        self.value = value
        self.expected_type = expected_type


class SpecViolationError(PyOCMFError, ValueError):
    """Input deviates from the OCMF spec while parsing in strict mode."""


class CryptoError(PyOCMFError):
    """Base class for public key and signature verification errors."""


class PublicKeyError(CryptoError):
    """The public key cannot be parsed or uses an unsupported curve."""

    def __init__(
        self,
        message: str,
        *,
        key_data: str | None = None,
        field: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message, field=field, details=details)
        self.key_data = key_data


class SignatureVerificationError(CryptoError):
    """The signature cannot be checked, e.g. without a key or with a mismatching curve.

    A signature that does not match the payload is not an error: verification
    returns False.
    """

    def __init__(
        self,
        message: str,
        *,
        reason: str | None = None,
        field: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message, field=field, details=details)
        self.reason = reason


class SpecWarning(UserWarning):
    """Input deviates from the OCMF spec but is accepted, as the Transparenzsoftware does."""
