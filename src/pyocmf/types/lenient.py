"""Types that accept values outside the OCMF spec and emit a SpecWarning.

The Transparenzsoftware verifies records regardless of unknown codes or exceeded
lengths, so pyocmf accepts them too instead of failing to parse.
"""

from __future__ import annotations

import warnings
from typing import Annotated

import pydantic

from pyocmf.enums.crypto import SignatureEncodingType, SignatureMethod, SignatureMimeType
from pyocmf.enums.identifiers import (
    ChargePointIdentificationType,
    IdentificationFlag,
    IdentificationType,
    UserAssignmentStatus,
)
from pyocmf.enums.reading import MeterReadingReason, MeterStatus, ReadingType
from pyocmf.enums.units import OCMFUnit, ResistanceUnit
from pyocmf.exceptions import SpecWarning


def warn_spec(message: str) -> None:
    warnings.warn(message, SpecWarning, stacklevel=2)


def _warn_if_unknown(value: object, info: pydantic.ValidationInfo) -> object:
    # A plain str (not a StrEnum member) means no enum member matched
    if type(value) is str:
        field = f" for {info.field_name}" if info.field_name else ""
        warn_spec(f"'{value}' is not a value defined by the OCMF spec{field}")
    return value


# Try the enum first and fall back to the raw string instead of rejecting it
_LENIENT = (pydantic.Field(union_mode="left_to_right"), pydantic.AfterValidator(_warn_if_unknown))

LenientBool = Annotated[bool | str, *_LENIENT]
LenientUserAssignmentStatus = Annotated[UserAssignmentStatus | str, *_LENIENT]
LenientIdentificationFlag = Annotated[IdentificationFlag | str, *_LENIENT]
LenientIdentificationType = Annotated[IdentificationType | str, *_LENIENT]
LenientChargePointIdentificationType = Annotated[ChargePointIdentificationType | str, *_LENIENT]
LenientMeterReadingReason = Annotated[MeterReadingReason | str, *_LENIENT]
LenientMeterStatus = Annotated[MeterStatus | str, *_LENIENT]
LenientReadingType = Annotated[ReadingType | str, *_LENIENT]
LenientUnit = Annotated[OCMFUnit | str, *_LENIENT]
LenientResistanceUnit = Annotated[ResistanceUnit | str, *_LENIENT]
LenientSignatureMethod = Annotated[SignatureMethod | str, *_LENIENT]
LenientSignatureEncoding = Annotated[SignatureEncodingType | str, *_LENIENT]
LenientSignatureMimeType = Annotated[SignatureMimeType | str, *_LENIENT]
