from pyocmf.enums.units import EnergyUnit, ResistanceUnit


class TestUnitEnums:
    def test_resistance_units(self) -> None:
        """Test resistance units as defined in OCMF spec Table 20."""
        assert ResistanceUnit.MOHM == "mOhm"
        assert ResistanceUnit.UOHM == "uOhm"

    def test_energy_units(self) -> None:
        """Test energy units as defined in OCMF spec Table 20."""
        assert EnergyUnit.KWH == "kWh"
        assert EnergyUnit.WH == "Wh"
