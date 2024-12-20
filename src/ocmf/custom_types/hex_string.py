from typing import Annotated, TypeAlias
from pydantic import AfterValidator, WithJsonSchema
import re


def validate_hex_string(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("string required")
    if not re.fullmatch(r"^[0-9a-fA-F]+$", value):
        raise ValueError("invalid hexadecimal string")
    return value


HexStr = Annotated[
    str,
    AfterValidator(validate_hex_string),
    WithJsonSchema({"type": "string", "pattern": "^[0-9a-fA-F]+$"}, mode="validation"),
]
