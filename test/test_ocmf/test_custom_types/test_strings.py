"""Tests for custom string validators that have custom logic (HexStr, Base64Str)."""

from contextlib import nullcontext as does_not_raise
from typing import ContextManager

import pydantic
import pytest

from pyocmf.custom_types.strings import Base64Str, HexStr


class TestHexString:
    """Test our custom HexStr validator with custom exception."""

    @pytest.mark.parametrize(
        ("input", "expectation"),
        [
            ("1234567890abcdef", does_not_raise()),
            ("ABCDEF", does_not_raise()),
            ("abc123", does_not_raise()),
            ("xyz", pytest.raises(pydantic.ValidationError)),
            ("12G4", pytest.raises(pydantic.ValidationError)),  # G is not hex
            ("", pytest.raises(pydantic.ValidationError)),  # Empty string invalid
            (123, pytest.raises(pydantic.ValidationError)),  # Non-string
        ],
    )
    def test_hex_string(self, input: str, expectation: ContextManager) -> None:
        """Test HexStr validation with various inputs."""
        with expectation:
            type_adapter = pydantic.TypeAdapter(HexStr)
            type_adapter.validate_python(input)

    def test_hex_string_custom_exception(self) -> None:
        """Test that HexDecodingError is raised for invalid hex strings."""
        with pytest.raises(pydantic.ValidationError) as exc_info:
            type_adapter = pydantic.TypeAdapter(HexStr)
            type_adapter.validate_python("xyz")

        errors = exc_info.value.errors()
        assert "invalid hexadecimal string" in str(errors[0])


class TestBase64String:
    """Test our custom Base64Str validator with custom exception."""

    @pytest.mark.parametrize(
        ("input", "expectation"),
        [
            ("SGVsbG8gV29ybGQ=", does_not_raise()),  # "Hello World"
            ("YWJjMTIz", does_not_raise()),  # "abc123"
            ("", does_not_raise()),  # Empty string valid for base64
            ("VGVzdA==", does_not_raise()),  # "Test"
            ("NotValidBase64!", pytest.raises(pydantic.ValidationError)),
            ("xyz", pytest.raises(pydantic.ValidationError)),
            (123, pytest.raises(pydantic.ValidationError)),  # Non-string
        ],
    )
    def test_base64_string(self, input: str, expectation: ContextManager) -> None:
        """Test Base64Str validation with various inputs."""
        with expectation:
            type_adapter = pydantic.TypeAdapter(Base64Str)
            type_adapter.validate_python(input)

    def test_base64_string_custom_exception(self) -> None:
        """Test that Base64DecodingError is raised for invalid base64 strings."""
        with pytest.raises(pydantic.ValidationError) as exc_info:
            type_adapter = pydantic.TypeAdapter(Base64Str)
            type_adapter.validate_python("NotValidBase64!")

        errors = exc_info.value.errors()
        assert "invalid base64 string" in str(errors[0])
