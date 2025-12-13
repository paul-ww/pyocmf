"""Tests for custom string validators that have custom logic (HexStr, Base64Str)."""

from contextlib import AbstractContextManager
from contextlib import nullcontext as does_not_raise
from typing import Any

import pydantic
import pytest

from pyocmf.types.identifiers import Base64Str, HexStr


class TestHexString:
    """Test our custom HexStr validator with custom exception."""

    @pytest.mark.parametrize(
        ("input", "expectation"),
        [
            ("1234567890abcdef", does_not_raise()),
            ("ABCDEF", does_not_raise()),
            ("abc123", does_not_raise()),
            ("xyz", pytest.raises(pydantic.ValidationError)),
            ("12G4", pytest.raises(pydantic.ValidationError)),
            ("", pytest.raises(pydantic.ValidationError)),
            (123, pytest.raises(pydantic.ValidationError)),
        ],
    )
    def test_hex_string(self, input: str, expectation: AbstractContextManager[Any]) -> None:
        """Test HexStr validation with various inputs."""
        with expectation:
            type_adapter = pydantic.TypeAdapter(HexStr)
            type_adapter.validate_python(input)

    def test_hex_string_custom_exception(self) -> None:
        """Test that HexDecodingError is raised for invalid hex strings."""
        type_adapter = pydantic.TypeAdapter(HexStr)
        with pytest.raises(pydantic.ValidationError) as exc_info:
            type_adapter.validate_python("xyz")

        errors = exc_info.value.errors()
        assert "invalid hexadecimal string" in str(errors[0])


class TestBase64String:
    """Test our custom Base64Str validator with custom exception."""

    @pytest.mark.parametrize(
        ("input", "expectation"),
        [
            ("SGVsbG8gV29ybGQ=", does_not_raise()),
            ("YWJjMTIz", does_not_raise()),
            ("", does_not_raise()),
            ("VGVzdA==", does_not_raise()),
            ("NotValidBase64!", pytest.raises(pydantic.ValidationError)),
            ("xyz", pytest.raises(pydantic.ValidationError)),
            (123, pytest.raises(pydantic.ValidationError)),
        ],
    )
    def test_base64_string(self, input: str, expectation: AbstractContextManager[Any]) -> None:
        """Test Base64Str validation with various inputs."""
        with expectation:
            type_adapter = pydantic.TypeAdapter(Base64Str)
            type_adapter.validate_python(input)

    def test_base64_string_custom_exception(self) -> None:
        """Test that Base64DecodingError is raised for invalid base64 strings."""
        type_adapter = pydantic.TypeAdapter(Base64Str)
        with pytest.raises(pydantic.ValidationError) as exc_info:
            type_adapter.validate_python("NotValidBase64!")

        errors = exc_info.value.errors()
        assert "invalid base64 string" in str(errors[0])
