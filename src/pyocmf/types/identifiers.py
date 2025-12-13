import base64
import enum
import re
from typing import Annotated

import pydantic
from pydantic import AfterValidator, WithJsonSchema
from pydantic_extra_types import phone_numbers

from pyocmf.exceptions import Base64DecodingError, HexDecodingError


def validate_hex_string(value: str) -> str:
    if not isinstance(value, str):
        msg = "string required"
        raise TypeError(msg)
    if not re.fullmatch(r"^[0-9a-fA-F]+$", value):
        msg = "invalid hexadecimal string"
        raise HexDecodingError(msg)
    return value


HexStr = Annotated[
    str,
    AfterValidator(validate_hex_string),
    WithJsonSchema({"type": "string", "pattern": "^[0-9a-fA-F]+$"}, mode="validation"),
]


def validate_base64_string(value: str) -> str:
    if not isinstance(value, str):
        msg = "string required"
        raise TypeError(msg)
    try:
        base64.b64decode(value, validate=True)
    except Exception as e:
        msg = "invalid base64 string"
        raise Base64DecodingError(msg) from e
    return value


Base64Str = Annotated[
    str,
    AfterValidator(validate_base64_string),
    WithJsonSchema({"type": "string", "format": "base64"}, mode="validation"),
]


TransactionContext = Annotated[str, pydantic.constr(pattern=r"^T[1-9]*$")]
FiscalContext = Annotated[str, pydantic.constr(pattern=r"^F[1-9]*$")]
PaginationString = TransactionContext | FiscalContext


class UserAssignmentStatus(str, enum.Enum):
    # status without assignment
    NO_ASSIGNMENT = "NONE"

    # status with assignment
    UNSECURED = "HEARSAY"
    TRUSTED = "TRUSTED"
    VERIFIED = "VERIFIED"
    CERTIFIED = "CERTIFIED"
    SECURE = "SECURE"

    # errors
    UID_MISMATCH = "MISMATCH"
    CERT_INCORRECT = "INVALID"
    CERT_EXPIRED = "OUTDATED"
    CERT_UNVERIFIED = "UNKNOWN"


class IdentificationFlagRFID(str, enum.Enum):
    NO_ASSIGNMENT_VIA_RFID = "RFID_NONE"
    ASSIGNMENT_VIA_EXTERNAL_RFID_CARD_READER = "RFID_PLAIN"
    ASSIGNMENT_VIA_PROTECTED_RFID_CARD_READER = "RFID_RELATED"
    PREVIOUSLY_KNOWN_SHARED_KEY = "RFID_PSK"


class IdentificationFlagOCPP(str, enum.Enum):
    NO_USER_ASSIGNMENT_BY_OCPP = "OCPP_NONE"
    ASSIGNMENT_BY_OCPP_REMOTESTART_METHOD = "OCPP_RS"
    ASSIGNMENT_BY_OCPP_AUTHORIZE_METHOD = "OCPP_AUTH"
    ASSIGNMENT_BY_OCPP_REMOTESTART_METHOD_TLS = "OCPP_RS_TLS"
    ASSIGNMENT_BY_OCPP_AUTHORIZE_METHOD_TLS = "OCPP_AUTH_TLS"
    ASSIGNMENT_BY_AUTHORIZATION_CACHE_OF_OCPP = "OCPP_CACHE"
    ASSIGNMENT_BY_WHITELIST_FROM_OCPP = "OCPP_WHITELIST"
    CERTIFICATE_OF_BACKEND_USED = "OCPP_CERTIFIED"


class IdentificationFlagIso15118(str, enum.Enum):
    NO_USER_ASSIGNMENT_BY_ISO_15118 = "ISO15118_NONE"
    PLUG_AND_CHARGE_WAS_USED = "ISO15118_PNC"


class IdentificationFlagPLMN(str, enum.Enum):
    NO_USER_ASSIGNMENT = "PLMN_NONE"
    CALL = "PLMN_RING"
    SHORT_MESSAGE = "PLMN_SMS"


class IdentificationType(enum.StrEnum):
    NONE = "NONE"
    DENIED = "DENIED"
    UNDEFINED = "UNDEFINED"
    ISO14443 = "ISO14443"
    ISO15693 = "ISO15693"
    EMAID = "EMAID"
    EVCCID = "EVCCID"
    EVCOID = "EVCOID"
    ISO7812 = "ISO7812"
    CARD_TXN_NR = "CARD_TXN_NR"
    CENTRAL = "CENTRAL"
    CENTRAL_1 = "CENTRAL_1"
    CENTRAL_2 = "CENTRAL_2"
    LOCAL = "LOCAL"
    LOCAL_1 = "LOCAL_1"
    LOCAL_2 = "LOCAL_2"
    PHONE_NUMBER = "PHONE_NUMBER"
    KEY_CODE = "KEY_CODE"


IdentificationFlag = (
    IdentificationFlagRFID
    | IdentificationFlagOCPP
    | IdentificationFlagIso15118
    | IdentificationFlagPLMN
)

# ISO 14443 UID represented as 4 or 7 bytes in hexadecimal notation
ISO14443 = Annotated[str, pydantic.Field(pattern=r"^[0-9a-fA-F]{8}$|^[0-9a-fA-F]{14}$")]
# ISO 15693 UID represented as 8 bytes in hexadecimal notation
ISO15693 = Annotated[str, pydantic.Field(pattern=r"^[0-9a-fA-F]{16}$")]
# Electro-Mobility-Account-ID according to ISO/IEC 15118 (string with length 14 or 15)
EMAID = Annotated[str, pydantic.Field(pattern=r"^[A-Za-z0-9]{14,15}$")]
# ID of an electric vehicle according to ISO/IEC 15118 (maximum length 6 characters)
EVCCID = Annotated[str, pydantic.Field(max_length=6)]
# EV Contract ID according to DIN 91286
EVCOID = str
# Identification card format according to ISO/IEC 7812 (credit and bank cards, etc.)
ISO7812 = str

PHONE_NUMBER = phone_numbers.PhoneNumber

# Union of all possible IdentificationData types
IdentificationData = ISO14443 | ISO15693 | EMAID | EVCCID | EVCOID | ISO7812 | PHONE_NUMBER


class ChargePointIdentificationType(enum.StrEnum):
    EVSEID = "EVSEID"
    CBIDC = "CBIDC"
