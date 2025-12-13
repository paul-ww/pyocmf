"""Tests for custom unit enums - just basic smoke tests since these are standard enums."""

from pyocmf.types.units import EnergyUnit, ResistanceUnit, TimeUnit


class TestUnitEnums:
    """Basic smoke tests for unit enums."""

    def test_resistance_units(self) -> None:
        """Test that resistance unit enum values work."""
        assert ResistanceUnit.MOHM == "mOhm"
        assert ResistanceUnit.OHM == "Ohm"

    def test_energy_units(self) -> None:
        """Test that energy unit enum values work."""
        assert EnergyUnit.KWH == "kWh"
        assert EnergyUnit.WH == "Wh"

    def test_time_units(self) -> None:
        """Test that time unit enum values work."""
        assert TimeUnit.SEC == "sec"
        assert TimeUnit.MIN == "min"
        assert TimeUnit.H == "h"
