from __future__ import annotations

from pyocmf.registries import (
    OBISCategory,
    OBISInfo,
    get_obis_info,
    is_accumulation_register,
    is_billing_relevant,
    is_transaction_register,
    normalize_obis_code,
    validate_obis_for_billing,
)


class TestOBISNormalization:
    def test_normalize_removes_asterisk(self) -> None:
        assert normalize_obis_code("01-00:B2.08.00*FF") == "01-00:B2.08.00"
        assert normalize_obis_code("01-00:B2.08.00*00") == "01-00:B2.08.00"

    def test_normalize_preserves_without_asterisk(self) -> None:
        assert normalize_obis_code("01-00:B2.08.00") == "01-00:B2.08.00"
        assert normalize_obis_code("1-b:1.8.0") == "1-b:1.8.0"


class TestOBISInfo:
    def test_from_code_known_obis(self) -> None:
        info = OBISInfo.from_code("01-00:B2.08.00*FF")
        assert info is not None
        assert info.code == "01-00:B2.08.00"
        assert info.billing_relevant is True
        assert info.category == OBISCategory.IMPORT

    def test_from_code_unknown_obis(self) -> None:
        info = OBISInfo.from_code("99-99:99.99.99*FF")
        assert info is None

    def test_is_accumulation_register_method(self) -> None:
        # B2 is accumulation register
        info = OBISInfo.from_code("01-00:B2.08.00*FF")
        assert info is not None
        assert info.is_accumulation_register() is True

        # Time register is not accumulation
        info = OBISInfo.from_code("01-00:00.08.06*FF")
        assert info is not None
        assert info.is_accumulation_register() is False

    def test_is_transaction_register_method(self) -> None:
        # B2, B3, C2, C3 are transaction registers
        info = OBISInfo.from_code("01-00:B2.08.00")
        assert info is not None
        assert info.is_transaction_register() is True
        info = OBISInfo.from_code("01-00:B3.08.00")
        assert info is not None
        assert info.is_transaction_register() is True
        info = OBISInfo.from_code("01-00:C2.08.00")
        assert info is not None
        assert info.is_transaction_register() is True
        info = OBISInfo.from_code("01-00:C3.08.00")
        assert info is not None
        assert info.is_transaction_register() is True

        # B0, B1, C0, C1 are total registers (not transaction)
        info = OBISInfo.from_code("01-00:B0.08.00")
        assert info is not None
        assert info.is_transaction_register() is False
        info = OBISInfo.from_code("01-00:B1.08.00")
        assert info is not None
        assert info.is_transaction_register() is False


class TestBillingRelevance:
    def test_known_billing_relevant_codes(self) -> None:
        assert is_billing_relevant("01-00:B0.08.00*FF") is True
        assert is_billing_relevant("01-00:B2.08.00*FF") is True
        assert is_billing_relevant("01-00:C3.08.00*FF") is True
        assert is_billing_relevant("01-00:01.08.00*FF") is True
        assert is_billing_relevant("1-b:1.8.0") is True

    def test_non_billing_codes(self) -> None:
        assert is_billing_relevant("01-00:00.08.06*FF") is False  # Time
        assert is_billing_relevant("01-00:16.07.00*FF") is False  # Power

    def test_pattern_matching_for_unknown_codes(self) -> None:
        # Unknown B/C registers should still be recognized
        assert is_billing_relevant("01-00:B1.08.00*99") is True
        assert is_billing_relevant("01-00:C0.08.00*AA") is True


class TestAccumulationRegister:
    def test_accumulation_registers_b0_b3(self) -> None:
        assert is_accumulation_register("01-00:B0.08.00*FF") is True
        assert is_accumulation_register("01-00:B1.08.00*FF") is True
        assert is_accumulation_register("01-00:B2.08.00*FF") is True
        assert is_accumulation_register("01-00:B3.08.00*FF") is True

    def test_accumulation_registers_c0_c3(self) -> None:
        assert is_accumulation_register("01-00:C0.08.00*FF") is True
        assert is_accumulation_register("01-00:C1.08.00*FF") is True
        assert is_accumulation_register("01-00:C2.08.00*FF") is True
        assert is_accumulation_register("01-00:C3.08.00*FF") is True

    def test_non_accumulation_registers(self) -> None:
        assert is_accumulation_register("01-00:01.08.00*FF") is False
        assert is_accumulation_register("01-00:00.08.06*FF") is False
        assert is_accumulation_register("1-b:1.8.0") is False


class TestTransactionRegister:
    def test_transaction_registers(self) -> None:
        assert is_transaction_register("01-00:B2.08.00*FF") is True
        assert is_transaction_register("01-00:B3.08.00*FF") is True
        assert is_transaction_register("01-00:C2.08.00*FF") is True
        assert is_transaction_register("01-00:C3.08.00*FF") is True

    def test_total_registers(self) -> None:
        assert is_transaction_register("01-00:B0.08.00*FF") is False
        assert is_transaction_register("01-00:B1.08.00*FF") is False
        assert is_transaction_register("01-00:C0.08.00*FF") is False
        assert is_transaction_register("01-00:C1.08.00*FF") is False


class TestValidateObisForBilling:
    def test_valid_billing_obis(self) -> None:
        is_valid, error = validate_obis_for_billing("01-00:B2.08.00*FF")
        assert is_valid is True
        assert error is None

    def test_none_obis_fails(self) -> None:
        is_valid, error = validate_obis_for_billing(None)
        assert is_valid is False
        assert error is not None
        assert "required" in error

    def test_non_billing_obis_fails(self) -> None:
        is_valid, error = validate_obis_for_billing("01-00:00.08.06*FF")
        assert is_valid is False
        assert error is not None
        assert "not billing-relevant" in error


class TestGetObisInfo:
    def test_get_known_obis_info(self) -> None:
        info = get_obis_info("01-00:B2.08.00*FF")
        assert info is not None
        assert "Transaction Import Mains" in info.description
        assert info.billing_relevant is True
        assert info.category == OBISCategory.IMPORT

    def test_get_unknown_obis_info(self) -> None:
        info = get_obis_info("99-99:99.99.99*FF")
        assert info is None

    def test_get_legacy_obis_info(self) -> None:
        info = get_obis_info("1-b:1.8.0")
        assert info is not None
        assert "legacy" in info.description.lower()
        assert info.billing_relevant is True
