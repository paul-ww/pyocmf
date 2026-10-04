import decimal

import pytest

from pyocmf.enums.units import ResistanceUnit
from pyocmf.exceptions import SpecWarning
from pyocmf.models import CableLossCompensation


class TestCableLossCompensation:
    def test_valid_cable_loss_with_all_fields(self) -> None:
        data = {
            "LN": "Cable Type A",
            "LI": 123,
            "LR": "1.5",
            "LU": "mOhm",
        }
        cable_loss = CableLossCompensation.model_validate(data)

        assert cable_loss.LN == "Cable Type A"
        assert cable_loss.LI == 123
        assert decimal.Decimal("1.5") == cable_loss.LR
        assert cable_loss.LU == ResistanceUnit.MOHM

    def test_valid_cable_loss_minimal_fields(self) -> None:
        data = {
            "LR": "2.5",
            "LU": "uOhm",
        }
        cable_loss = CableLossCompensation.model_validate(data)

        assert cable_loss.LN is None
        assert cable_loss.LI is None
        assert decimal.Decimal("2.5") == cable_loss.LR
        assert cable_loss.LU == ResistanceUnit.UOHM

    @pytest.mark.parametrize(
        "lr_value",
        ["0.001", "1.5", "100", "0.0", "999.999", 1.5, 5],
    )
    def test_lr_accepts_various_numeric_types(self, lr_value: str | float | int) -> None:
        data = {"LR": lr_value, "LU": "mOhm"}
        cable_loss = CableLossCompensation.model_validate(data)
        assert isinstance(cable_loss.LR, decimal.Decimal)

    def test_ln_max_length_warns(self) -> None:
        with pytest.warns(SpecWarning, match="exceeds 20 characters"):
            cable_loss = CableLossCompensation.model_validate({
                "LN": "A" * 21,
                "LR": "1.0",
                "LU": "mOhm",
            })
        assert cable_loss.LN == "A" * 21

    @pytest.mark.parametrize(("data", "missing"), [({"LU": "mOhm"}, "LR"), ({"LR": "1.5"}, "LU")])
    def test_missing_required_fields_warn(self, data: dict, missing: str) -> None:
        with pytest.warns(SpecWarning, match=rf"\({missing}\) is mandatory"):
            CableLossCompensation.model_validate(data)
