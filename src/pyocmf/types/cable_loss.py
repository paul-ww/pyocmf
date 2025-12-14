"""Cable loss compensation types for OCMF.

This module defines models for representing cable loss compensation
data in charging sessions.
"""

import decimal

import pydantic

from pyocmf.types.units import ResistanceUnit


class CableLossCompensation(pydantic.BaseModel):
    """Cable loss compensation data.

    Represents information about cable resistance and compensation
    applied during a charging session.
    """

    LN: str | None = pydantic.Field(
        default=None, max_length=20, description="Loss Compensation Naming"
    )
    LI: int | None = pydantic.Field(default=None, description="Loss Compensation Identification")
    LR: decimal.Decimal = pydantic.Field(description="Loss Compensation Cable Resistance")
    LU: ResistanceUnit = pydantic.Field(description="Loss Compensation Unit")
