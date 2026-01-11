from __future__ import annotations

from typing import Annotated

import pydantic
from pydantic import BeforeValidator

from pyocmf.registries.obis import (
    get_obis_info,
    is_accumulation_register,
    is_billing_relevant,
    is_transaction_register,
)


class OBIS(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    code: str
    suffix: str | None = None

    @classmethod
    def from_string(cls, obis_str: str) -> OBIS:
        if not isinstance(obis_str, str):
            return obis_str

        parts = obis_str.split("*", 1)
        return cls(
            code=parts[0],
            suffix=parts[1] if len(parts) > 1 else None,
        )

    @property
    def info(self):
        return get_obis_info(self.code)

    @property
    def is_billing_relevant(self) -> bool:
        return is_billing_relevant(self.code)

    @property
    def is_accumulation_register(self) -> bool:
        return is_accumulation_register(self.code)

    @property
    def is_transaction_register(self) -> bool:
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
