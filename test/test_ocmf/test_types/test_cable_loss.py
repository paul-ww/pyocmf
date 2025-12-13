"""Tests for CableLossCompensation model."""

import decimal

import pydantic
import pytest

from pyocmf.types.cable_loss import CableLossCompensation
from pyocmf.types.units import ResistanceUnit


class TestCableLossCompensation:
    """Test the CableLossCompensation pydantic model."""

    def test_valid_cable_loss_with_all_fields(self) -> None:
        """Test creating CableLossCompensation with all fields."""
        data = {
            "LN": "Cable Type A",
            "LI": 123,
            "LR": "1.5",
            "LU": "mOhm",
        }
        cable_loss = CableLossCompensation.model_validate(data)

        assert cable_loss.LN == "Cable Type A"
        assert cable_loss.LI == 123
        assert cable_loss.LR == decimal.Decimal("1.5")
        assert cable_loss.LU == ResistanceUnit.MOHM

    def test_valid_cable_loss_minimal_fields(self) -> None:
        """Test creating CableLossCompensation with only required fields."""
        data = {
            "LR": "2.5",
            "LU": "Ohm",
        }
        cable_loss = CableLossCompensation.model_validate(data)

        assert cable_loss.LN is None
        assert cable_loss.LI is None
        assert cable_loss.LR == decimal.Decimal("2.5")
        assert cable_loss.LU == ResistanceUnit.OHM

    @pytest.mark.parametrize(
        "lr_value",
        ["0.001", "1.5", "100", "0.0", "999.999", 1.5, 5],
    )
    def test_lr_accepts_various_numeric_types(self, lr_value) -> None:
        """Test that LR field accepts string, float, and int values."""
        data = {"LR": lr_value, "LU": "mOhm"}
        cable_loss = CableLossCompensation.model_validate(data)
        assert isinstance(cable_loss.LR, decimal.Decimal)

    def test_ln_max_length_enforced(self) -> None:
        """Test that LN field enforces max length of 20."""
        data = {
            "LN": "A" * 21,  # Too long
            "LR": "1.0",
            "LU": "mOhm",
        }
        with pytest.raises(pydantic.ValidationError) as exc_info:
            CableLossCompensation.model_validate(data)

        errors = exc_info.value.errors()
        assert any(
            "max_length" in str(error) or "string_too_long" in str(error) for error in errors
        )

    def test_missing_required_fields(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(pydantic.ValidationError):
            CableLossCompensation.model_validate({"LU": "mOhm"})

        with pytest.raises(pydantic.ValidationError):
            CableLossCompensation.model_validate({"LR": "1.5"})
