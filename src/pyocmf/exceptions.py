"""Custom exception classes for the pyocmf library."""

from __future__ import annotations


class PyOCMFError(Exception):
    """Base exception for all pyocmf errors."""


class XmlParsingError(PyOCMFError):
    """Error parsing XML file structure or content."""


class DataNotFoundError(PyOCMFError):
    """OCMF data not found in provided source."""


class OcmfFormatError(PyOCMFError):
    """Invalid OCMF string format."""


class OcmfPayloadError(PyOCMFError):
    """Error in OCMF payload section parsing or validation.

    Args:
        message: The error message.
        field: The name of the field that caused the error, if applicable.
        details: Additional error details from validation.
    """

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        details: list[dict] | None = None,
    ) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.field = field
        self.details = details


class OcmfSignatureError(PyOCMFError):
    """Error in OCMF signature section parsing or validation.

    Args:
        message: The error message.
        field: The name of the field that caused the error, if applicable.
        details: Additional error details from validation.
    """

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        details: list[dict] | None = None,
    ) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.field = field
        self.details = details


class EncodingError(PyOCMFError, ValueError):
    """Error encoding or decoding data.

    Inherits from ValueError for compatibility with Pydantic validation.

    Args:
        message: The error message.
        value: The value that failed to encode/decode.
    """

    def __init__(self, message: str, *, value: str | None = None) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.value = value


class HexDecodingError(EncodingError):
    """Error decoding hexadecimal string."""


class Base64DecodingError(EncodingError):
    """Error decoding base64 string."""


class EncodingTypeError(PyOCMFError, TypeError):
    """Type error during encoding/decoding operations.

    Raised when a value of incorrect type is provided to encoding functions.
    Inherits from TypeError for Pythonic type error handling.

    Args:
        message: The error message.
        value: The value that had the wrong type.
        expected_type: The expected type name.
    """

    def __init__(
        self,
        message: str,
        *,
        value: object = None,
        expected_type: str | None = None,
    ) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.value = value
        self.expected_type = expected_type


class ValidationError(PyOCMFError, ValueError):
    """Error validating data format or content.

    Inherits from ValueError for compatibility with Pydantic validation.

    Args:
        message: The error message.
        field: The name of the field that failed validation.
    """

    def __init__(self, message: str, *, field: str | None = None) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.field = field


class CryptoError(PyOCMFError):
    """Base exception for cryptographic operation errors."""


class PublicKeyError(CryptoError):
    """Error related to public key handling.

    Args:
        message: The error message.
        key_data: The key data that caused the error, if available.
    """

    def __init__(self, message: str, *, key_data: str | None = None) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.key_data = key_data


class SignatureVerificationError(CryptoError):
    """Error verifying cryptographic signature.

    Args:
        message: The error message.
        reason: The specific reason verification failed.
    """

    def __init__(self, message: str, *, reason: str | None = None) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.reason = reason
