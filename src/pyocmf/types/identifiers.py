"""User and charge point identification types for OCMF.

This module defines various identification types, validation functions,
and enums for representing user authentication and charge point identification
in OCMF format.
"""

import enum
from typing import Annotated

import pydantic
from pydantic.types import StringConstraints
from pydantic_extra_types import phone_numbers

# Transaction context: "T" followed by number without leading zeros (e.g., "T1", "T123", not "T0" or "T01")
TransactionContext = Annotated[str, StringConstraints(pattern=r"^T([1-9][0-9]*)$")]
# Fiscal context: "F" followed by number without leading zeros (e.g., "F1", "F456", not "F0" or "F00")
FiscalContext = Annotated[str, StringConstraints(pattern=r"^F([1-9][0-9]*)$")]
PaginationString = TransactionContext | FiscalContext


class UserAssignmentStatus(enum.StrEnum):
    """Security level of user identification and assignment.

    Indicates the trustworthiness and verification level of the user
    identification method used for the charging session.
    """

    NO_ASSIGNMENT = "NONE"
    UNSECURED = "HEARSAY"
    TRUSTED = "TRUSTED"
    VERIFIED = "VERIFIED"
    CERTIFIED = "CERTIFIED"
    SECURE = "SECURE"
    UID_MISMATCH = "MISMATCH"
    CERT_INCORRECT = "INVALID"
    CERT_EXPIRED = "OUTDATED"
    CERT_UNVERIFIED = "UNKNOWN"


class IdentificationFlagRFID(enum.StrEnum):
    """RFID-based user identification methods."""

    NO_ASSIGNMENT_VIA_RFID = "RFID_NONE"
    ASSIGNMENT_VIA_EXTERNAL_RFID_CARD_READER = "RFID_PLAIN"
    ASSIGNMENT_VIA_PROTECTED_RFID_CARD_READER = "RFID_RELATED"
    PREVIOUSLY_KNOWN_SHARED_KEY = "RFID_PSK"


class IdentificationFlagOCPP(enum.StrEnum):
    """OCPP-based user identification methods."""

    NO_USER_ASSIGNMENT_BY_OCPP = "OCPP_NONE"
    ASSIGNMENT_BY_OCPP_REMOTESTART_METHOD = "OCPP_RS"
    ASSIGNMENT_BY_OCPP_AUTHORIZE_METHOD = "OCPP_AUTH"
    ASSIGNMENT_BY_OCPP_REMOTESTART_METHOD_TLS = "OCPP_RS_TLS"
    ASSIGNMENT_BY_OCPP_AUTHORIZE_METHOD_TLS = "OCPP_AUTH_TLS"
    ASSIGNMENT_BY_AUTHORIZATION_CACHE_OF_OCPP = "OCPP_CACHE"
    ASSIGNMENT_BY_WHITELIST_FROM_OCPP = "OCPP_WHITELIST"
    CERTIFICATE_OF_BACKEND_USED = "OCPP_CERTIFIED"


class IdentificationFlagIso15118(enum.StrEnum):
    """ISO 15118-based user identification methods."""

    NO_USER_ASSIGNMENT_BY_ISO_15118 = "ISO15118_NONE"
    PLUG_AND_CHARGE_WAS_USED = "ISO15118_PNC"


class IdentificationFlagPLMN(enum.StrEnum):
    """PLMN (mobile network) based user identification methods."""

    NO_USER_ASSIGNMENT = "PLMN_NONE"
    CALL = "PLMN_RING"
    SHORT_MESSAGE = "PLMN_SMS"


class IdentificationType(enum.StrEnum):
    """Types of user identification credentials."""

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

# ISO14443 RFID card UID: 4 or 7 bytes in hex (e.g., "1A2B3C4D" or "1A2B3C4D5E6F70")
ISO14443 = Annotated[str, pydantic.Field(pattern=r"^[0-9a-fA-F]{8}$|^[0-9a-fA-F]{14}$")]
# ISO15693 RFID card UID: 8 bytes in hex (e.g., "E007000012345678")
ISO15693 = Annotated[str, pydantic.Field(pattern=r"^[0-9a-fA-F]{16}$")]
# EMAID: Electro-Mobility Account ID, 14-15 alphanumeric chars (e.g., "DETNME12345678X")
EMAID = Annotated[str, pydantic.Field(pattern=r"^[A-Za-z0-9]{14,15}$")]
# EVCCID: Electric Vehicle ID, max 6 characters (e.g., "ABC123")
EVCCID = Annotated[str, pydantic.Field(max_length=6)]
# EVCOID per DIN 91286: format like "NL-TNM-012204-5" (Country-Provider-Instance-CheckDigit)
EVCOID = Annotated[str, pydantic.Field(pattern=r"^[A-Z]{2,3}-[A-Z0-9]{2,3}-[0-9]{6}-[0-9]$")]
# ISO7812: Card numbers 8-19 digits (e.g., "4111111111111111" for credit/bank cards)
ISO7812 = Annotated[str, pydantic.Field(pattern=r"^[0-9]{8,19}$")]

PHONE_NUMBER = phone_numbers.PhoneNumber

# Unrestricted ID types: LOCAL, CENTRAL, CARD_TXN_NR, KEY_CODE per spec have no exact format defined
# These can be any string value (e.g., UUID, arbitrary text, etc.)
UnrestrictedID = str

IdentificationData = (
    ISO14443 | ISO15693 | EMAID | EVCCID | EVCOID | ISO7812 | PHONE_NUMBER | UnrestrictedID
)


class ChargePointIdentificationType(enum.StrEnum):
    """Types of charge point identification schemes."""

    EVSEID = "EVSEID"
    CBIDC = "CBIDC"
