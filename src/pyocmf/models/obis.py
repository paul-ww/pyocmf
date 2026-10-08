from __future__ import annotations

from typing import Annotated

import pydantic
from pydantic import BeforeValidator

from pyocmf.registries.obis import (
    OBISInfo,
    get_obis_info,
    is_accumulation_register,
    is_billing_relevant,
    is_law_relevant,
    is_loss_compensated,
    is_transaction_register,
)


class OBIS(pydantic.BaseModel):
    """OBIS code of a reading register (RI), with an optional suffix after ``*``."""

    model_config = pydantic.ConfigDict(frozen=True)

    code: str
    suffix: str | None = None

    @classmethod
    def from_string(cls, obis_str: str) -> OBIS:
        """Split an OBIS string into the code and the suffix after ``*``."""
        if not isinstance(obis_str, str):
            return obis_str

        parts = obis_str.split("*", 1)
        return cls(
            code=parts[0],
            suffix=parts[1] if len(parts) > 1 else None,
        )

    @pydantic.model_serializer
    def serialize_to_string(self) -> str:
        # OCMF spec Table 7: RI is a JSON String, not an object
        return str(self)

    @property
    def info(self) -> OBISInfo | None:
        """Registry entry of a known code, else None."""
        return get_obis_info(self.code)

    @property
    def is_billing_relevant(self) -> bool:
        """See ``pyocmf.registries.obis.is_billing_relevant``."""
        return is_billing_relevant(self.code)

    @property
    def is_law_relevant(self) -> bool:
        """See ``pyocmf.registries.obis.is_law_relevant``."""
        return is_law_relevant(str(self))

    @property
    def is_loss_compensated(self) -> bool:
        """Whether the register holds loss-compensated energy (98, B1, B3, C1, C3)."""
        return is_loss_compensated(self.code)

    @property
    def is_accumulation_register(self) -> bool:
        """See ``pyocmf.registries.obis.is_accumulation_register``."""
        return is_accumulation_register(self.code)

    @property
    def is_transaction_register(self) -> bool:
        """See ``pyocmf.registries.obis.is_transaction_register``."""
        return is_transaction_register(self.code)

    def __str__(self) -> str:
        return f"{self.code}*{self.suffix}" if self.suffix else self.code

    def __repr__(self) -> str:
        if self.suffix:
            return f"OBIS('{self.code}*{self.suffix}')"
        return f"OBIS('{self.code}')"


OBISCode = Annotated[
    OBIS,
    BeforeValidator(lambda v: OBIS.from_string(v) if isinstance(v, str) else v),
]
