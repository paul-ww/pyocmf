"""Open Charge Metering Format (OCMF) Library.

Parsing, validation, and compliance checking for OCMF metering data from
electric vehicle charging stations.
"""

from importlib.metadata import version

__version__ = version("pyocmf")

from pyocmf.compliance import (
    EichrechtIssue,
    IssueCode,
    IssueSeverity,
    check_eichrecht_reading,
    check_eichrecht_transaction,
    validate_transaction_pair,
)
from pyocmf.core import OCMF, Payload, Reading, Signature
from pyocmf.enums.crypto import SignatureMethod
from pyocmf.enums.identifiers import IdentificationType, UserAssignmentStatus
from pyocmf.enums.reading import MeterReadingReason, MeterStatus, ReadingType, TimeStatus
from pyocmf.enums.units import EnergyUnit
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
from pyocmf.models import OBIS, CableLossCompensation, OCMFTimestamp, PublicKey
from pyocmf.registries.obis import get_obis_info, is_billing_relevant
from pyocmf.utils.xml import OcmfContainer, OcmfRecord

__all__ = [
    # Version
    "__version__",
    # Core models
    "OCMF",
    "Payload",
    "Reading",
    "Signature",
    # Data models
    "PublicKey",
    "CableLossCompensation",
    "OBIS",
    "OCMFTimestamp",
    # Common enums
    "MeterStatus",
    "TimeStatus",
    "MeterReadingReason",
    "ReadingType",
    "IdentificationType",
    "UserAssignmentStatus",
    "SignatureMethod",
    "EnergyUnit",
    # Compliance
    "EichrechtIssue",
    "IssueCode",
    "IssueSeverity",
    "check_eichrecht_reading",
    "check_eichrecht_transaction",
    "validate_transaction_pair",
    # Utilities
    "OcmfContainer",
    "OcmfRecord",
    # Registries
    "get_obis_info",
    "is_billing_relevant",
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
]
