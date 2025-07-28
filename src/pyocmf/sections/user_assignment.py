import pydantic
from pydantic_extra_types import phone_numbers
from typing import List, Literal
import enum


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


IdentificationType = Literal[
    "NONE",
    "DENIED",
    "UNDEFINED",
    "ISO14443",
    "ISO15693",
    "EMAID",
    "EVCCID",
    "EVCOID",
    "ISO7812",
    "CARD_TXN_NR",
    "CENTRAL",
    "CENTRAL_1",
    "CENTRAL_2",
    "LOCAL",
    "LOCAL_1",
    "LOCAL_2",
    "PHONE_NUMBER",
    "KEY_CODE",
]


IdentificationFlag = (
    IdentificationFlagRFID
    | IdentificationFlagOCPP
    | IdentificationFlagIso15118
    | IdentificationFlagPLMN
)

# "ISO 14443 UID represented as 4 or 7 bytes in hexadecimal notation.",
ISO14443 = pydantic.constr(
    pattern=r"^[0-9a-fA-F]{8}$|^[0-9a-fA-F]{14}$",
)
# "ISO 15693 UID represented as 8 bytes in hexadecimal notation.",
ISO15693 = pydantic.constr(
    pattern=r"^[0-9a-fA-F]{16}$",
)
# "Electro-Mobility-Account-ID according to ISO/IEC 15118 (string with length 14 or 15).",
EMAID = pydantic.constr(
    pattern=r"^[A-Za-z0-9]{14,15}$",
)
# "ID of an electric vehicle according to ISO/IEC 15118 (maximum length 6 characters).",
EVCCID = pydantic.constr(
    max_length=6,
)
# "EV Contract ID according to DIN 91286."
EVCOID = str
# "Identification card format according to ISO/IEC 7812 (credit and bank cards, etc.)."
ISO7812 = str

PHONE_NUMBER = phone_numbers.PhoneNumber

# Union of all possible IdentificationData types
IdentificationData = (
    ISO14443 | ISO15693 | EMAID | EVCCID | EVCOID | ISO7812 | PHONE_NUMBER
)


class UserAssignment(pydantic.BaseModel):
    IS: bool = pydantic.Field(description="Identification Status")
    IL: UserAssignmentStatus | None = pydantic.Field(description="Identification Level")
    IF: List[IdentificationFlag] = pydantic.Field(
        default=[], description="Identification Flags"
    )
    IT: IdentificationType = pydantic.Field(description="Identification Type")
    ID: IdentificationData = pydantic.Field(description="Identification Data")
    TT: str = pydantic.Field(description="Tariff Text")
