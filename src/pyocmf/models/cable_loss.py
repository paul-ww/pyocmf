from __future__ import annotations

import pydantic

from pyocmf.types.lenient import LenientResistanceUnit, warn_spec
from pyocmf.types.numbers import OCMFNumber

_MAX_NAMING_LENGTH = 20


class CableLossCompensation(pydantic.BaseModel):
    LN: str | None = pydantic.Field(default=None, description="Loss Compensation Naming (0..20)")
    LI: int | None = pydantic.Field(default=None, description="Loss Compensation Identification")
    LR: OCMFNumber | None = pydantic.Field(
        default=None, description="Loss Compensation Cable Resistance - REQUIRED"
    )
    LU: LenientResistanceUnit | None = pydantic.Field(
        default=None, description="Loss Compensation Unit - REQUIRED"
    )

    @pydantic.model_validator(mode="after")
    def warn_on_spec_deviations(self) -> CableLossCompensation:
        if self.LN is not None and len(self.LN) > _MAX_NAMING_LENGTH:
            warn_spec(f"Loss compensation naming (LN) exceeds {_MAX_NAMING_LENGTH} characters")
        if self.LR is None:
            warn_spec("Loss compensation cable resistance (LR) is mandatory")
        if self.LU is None:
            warn_spec("Loss compensation resistance unit (LU) is mandatory")
        return self
