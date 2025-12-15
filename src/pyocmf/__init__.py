"""Python library for parsing and validating Open Charge Metering Format (OCMF) data."""

__version__ = "0.1.0"

from pyocmf.exceptions import (
    Base64DecodingError,
    DataNotFoundError,
    EncodingError,
    HexDecodingError,
    OcmfFormatError,
    OcmfPayloadError,
    OcmfSignatureError,
    PublicKeyError,
    PyOCMFError,
    SignatureVerificationError,
    ValidationError,
    XmlParsingError,
)
from pyocmf.ocmf import OCMF
from pyocmf.utils.xml import OcmfContainer, OcmfEntry

__all__ = [
    # Version
    "__version__",
    # Core
    "OCMF",
    # XML utilities
    "OcmfContainer",
    "OcmfEntry",
    # Exceptions
    "PyOCMFError",
    "OcmfFormatError",
    "OcmfPayloadError",
    "OcmfSignatureError",
    "ValidationError",
    "EncodingError",
    "HexDecodingError",
    "Base64DecodingError",
    "DataNotFoundError",
    "SignatureVerificationError",
    "PublicKeyError",
    "XmlParsingError",
]
