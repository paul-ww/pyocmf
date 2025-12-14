"""Custom exception classes for the pyocmf library."""


class PyOCMFError(Exception):
    """Base exception for all pyocmf errors."""


class XmlParsingError(PyOCMFError):
    """Error parsing XML file structure or content."""


class DataNotFoundError(PyOCMFError):
    """OCMF data not found in provided source."""


class OcmfFormatError(PyOCMFError):
    """Invalid OCMF string format."""


class OcmfPayloadError(PyOCMFError):
    """Error in OCMF payload section parsing or validation."""


class OcmfSignatureError(PyOCMFError):
    """Error in OCMF signature section parsing or validation."""


class EncodingError(PyOCMFError, ValueError):
    """Error encoding or decoding data.

    Inherits from ValueError for compatibility with Pydantic validation.
    """


class HexDecodingError(EncodingError):
    """Error decoding hexadecimal string."""


class Base64DecodingError(EncodingError):
    """Error decoding base64 string."""


class ValidationError(PyOCMFError, ValueError):
    """Error validating data format or content.

    Inherits from ValueError for compatibility with Pydantic validation.
    """


class PublicKeyError(PyOCMFError):
    """Error related to public key handling."""


class SignatureVerificationError(PyOCMFError):
    """Error verifying cryptographic signature."""
