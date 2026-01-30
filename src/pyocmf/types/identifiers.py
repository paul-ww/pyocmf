from typing import Annotated

import pydantic
from pydantic.types import StringConstraints
from pydantic_extra_types import phone_numbers

# Pagination types (OCMF spec Table 2)
TransactionContext = Annotated[str, StringConstraints(pattern=r"^T([0-9]+)$")]
FiscalContext = Annotated[str, StringConstraints(pattern=r"^F([0-9]+)$")]
PaginationString = TransactionContext | FiscalContext

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
UnrestrictedID = str

IdentificationData = (
    ISO14443 | ISO15693 | EMAID | EVCCID | EVCOID | ISO7812 | PHONE_NUMBER | UnrestrictedID
)

__all__ = [
    "TransactionContext",
    "FiscalContext",
    "PaginationString",
    "ISO14443",
    "ISO15693",
    "EMAID",
    "EVCCID",
    "EVCOID",
    "ISO7812",
    "PHONE_NUMBER",
    "UnrestrictedID",
    "IdentificationData",
]
