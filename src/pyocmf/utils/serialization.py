from __future__ import annotations

import decimal
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pydantic


def model_to_ocmf_json(model: pydantic.BaseModel) -> str:
    """Serialize a model to compact OCMF JSON with exact decimal representation.

    The OCMF spec requires numeric fields (RV, CL, LR) to be JSON Numbers and
    warns that their representation must not be transformed (e.g. 2935.600 must
    not become 2935.6). Standard JSON encoders cannot emit Decimal as a raw
    number token, so this assembles the JSON string directly from the dumped
    model.
    """
    return _encode(model.model_dump(mode="python", exclude_none=True))


def _encode(value: Any) -> str:
    if isinstance(value, decimal.Decimal):
        if not value.is_finite():
            msg = f"Cannot represent non-finite Decimal '{value}' as a JSON number"
            raise ValueError(msg)
        return str(value)
    if isinstance(value, dict):
        return "{" + ",".join(f"{json.dumps(str(k))}:{_encode(v)}" for k, v in value.items()) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_encode(v) for v in value) + "]"
    return json.dumps(value)
