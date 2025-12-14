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
from pyocmf.utils.xml import (
    OcmfXmlData,
    extract_ocmf_data_from_file,
    extract_ocmf_strings_from_file,
    parse_all_ocmf_from_xml,
    parse_ocmf_from_xml,
    parse_ocmf_with_key_from_xml,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "OCMF",
    # XML utilities
    "OcmfXmlData",
    "extract_ocmf_data_from_file",
    "extract_ocmf_strings_from_file",
    "parse_ocmf_from_xml",
    "parse_ocmf_with_key_from_xml",
    "parse_all_ocmf_from_xml",
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
