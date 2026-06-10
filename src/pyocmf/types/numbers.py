import decimal
from typing import Annotated

import pydantic

# OCMF spec requires numeric fields (RV, CL, LR) to be JSON Numbers. Pydantic
# serializes Decimal as a JSON string by default, which would violate the spec,
# so model_dump_json serializes through float. OCMF.to_string instead uses
# utils.serialization.model_to_ocmf_json, which emits the Decimal exactly,
# preserving the decimal places of parsed input (e.g. 2935.600).
OCMFNumber = Annotated[
    decimal.Decimal,
    pydantic.PlainSerializer(float, return_type=float, when_used="json"),
]

__all__ = ["OCMFNumber"]
