import base64
import re
from typing import Annotated

from pydantic import AfterValidator, WithJsonSchema

from pyocmf.exceptions import Base64DecodingError, EncodingTypeError, HexDecodingError


def validate_hex_string(value: str) -> str:
    if not isinstance(value, str):
        msg = "string required"
        raise EncodingTypeError(msg, value=value, expected_type="str")
    if not re.fullmatch(r"^[0-9a-fA-F]+$", value):
        msg = "invalid hexadecimal string"
        raise HexDecodingError(msg, value=value)
    return value


HexStr = Annotated[
    str,
    AfterValidator(validate_hex_string),
    WithJsonSchema({"type": "string", "pattern": "^[0-9a-fA-F]+$"}, mode="validation"),
]


def validate_base64_string(value: str) -> str:
    if not isinstance(value, str):
        msg = "string required"
        raise EncodingTypeError(msg, value=value, expected_type="str")
    try:
        base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as e:
        msg = "invalid base64 string"
        raise Base64DecodingError(msg, value=value) from e
    return value


Base64Str = Annotated[
    str,
    AfterValidator(validate_base64_string),
    WithJsonSchema({"type": "string", "format": "base64"}, mode="validation"),
]
