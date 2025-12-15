"""Encoding type validators for hex and base64 strings."""

import base64
import re
from typing import Annotated

from pydantic import AfterValidator, WithJsonSchema

from pyocmf.exceptions import Base64DecodingError, HexDecodingError


def validate_hex_string(value: str) -> str:
    """Validate that a string contains only hexadecimal characters.

    Args:
        value: String to validate.

    Returns:
        The validated hex string.

    Raises:
        TypeError: If value is not a string.
        HexDecodingError: If string contains non-hex characters.
    """
    if not isinstance(value, str):
        msg = "string required"
        raise TypeError(msg)
    if not re.fullmatch(r"^[0-9a-fA-F]+$", value):
        msg = "invalid hexadecimal string"
        raise HexDecodingError(msg)
    return value


HexStr = Annotated[
    str,
    AfterValidator(validate_hex_string),
    WithJsonSchema({"type": "string", "pattern": "^[0-9a-fA-F]+$"}, mode="validation"),
]


def validate_base64_string(value: str) -> str:
    """Validate that a string is valid base64 encoding.

    Args:
        value: String to validate.

    Returns:
        The validated base64 string.

    Raises:
        TypeError: If value is not a string.
        Base64DecodingError: If string is not valid base64.
    """
    if not isinstance(value, str):
        msg = "string required"
        raise TypeError(msg)
    try:
        base64.b64decode(value, validate=True)
    except Exception as e:
        msg = "invalid base64 string"
        raise Base64DecodingError(msg) from e
    return value


Base64Str = Annotated[
    str,
    AfterValidator(validate_base64_string),
    WithJsonSchema({"type": "string", "format": "base64"}, mode="validation"),
]
