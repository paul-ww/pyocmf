import pytest
from pyocmf.custom_types.hex_string import HexStr
from contextlib import nullcontext as does_not_raise
import pydantic
from typing import ContextManager


class TestHexString:
    @pytest.mark.parametrize(
        ("input", "expectation"),
        [
            ("1234567890abcdef", does_not_raise()),
            ("xyz", pytest.raises(pydantic.ValidationError)),
            (123, pytest.raises(pydantic.ValidationError)),
        ],
    )
    def test_hex_string(self, input: str, expectation: ContextManager):
        with expectation:
            type_adapter = pydantic.TypeAdapter(HexStr)
            type_adapter.validate_python(input)
