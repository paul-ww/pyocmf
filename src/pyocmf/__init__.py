__version__ = "0.2.0"

# Core models
# Compliance
from pyocmf.compliance import (
    EichrechtIssue,
    IssueCode,
    IssueSeverity,
    check_eichrecht_reading,
    check_eichrecht_transaction,
)
from pyocmf.core import OCMF, Payload, Reading, Signature
from pyocmf.enums.crypto import SignatureMethod
from pyocmf.enums.identifiers import IdentificationType, UserAssignmentStatus

# Common enums
from pyocmf.enums.reading import MeterReadingReason, MeterStatus, ReadingType, TimeStatus
from pyocmf.enums.units import EnergyUnit

# Exceptions
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

# Models
from pyocmf.models import OBIS, CableLossCompensation, OCMFTimestamp, PublicKey

# Registries
from pyocmf.registries.obis import get_obis_info, is_billing_relevant

# Utils
from pyocmf.utils.xml import OcmfContainer, OcmfRecord

__all__ = [
    # Version
    "__version__",
    # Core
    "OCMF",
    "Payload",
    "Reading",
    "Signature",
    # Models
    "PublicKey",
    "CableLossCompensation",
    "OBIS",
    "OCMFTimestamp",
    # Common Enums
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
    # Utils
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
