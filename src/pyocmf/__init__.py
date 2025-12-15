"""Python library for parsing and validating Open Charge Metering Format (OCMF) data."""

__version__ = "0.1.0"

from pyocmf.exceptions import (
    Base64DecodingError,
    CryptoError,
    DataNotFoundError,
    EncodingError,
    EncodingTypeError,
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
from pyocmf.utils.xml import OcmfContainer, OcmfRecord

__all__ = [
    # Version
    "__version__",
    # Core
    "OCMF",
    # XML utilities
    "OcmfContainer",
    "OcmfRecord",
    # Exceptions - Base
    "PyOCMFError",
    # Exceptions - OCMF parsing
    "OcmfFormatError",
    "OcmfPayloadError",
    "OcmfSignatureError",
    # Exceptions - Validation
    "ValidationError",
    # Exceptions - Encoding
    "EncodingError",
    "EncodingTypeError",
    "HexDecodingError",
    "Base64DecodingError",
    # Exceptions - Data
    "DataNotFoundError",
    "XmlParsingError",
    # Exceptions - Cryptography
    "CryptoError",
    "SignatureVerificationError",
    "PublicKeyError",
    "OcmfRecord",
]
