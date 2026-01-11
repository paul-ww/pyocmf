from pyocmf.enums.units import EnergyUnit, ResistanceUnit, TimeUnit


class TestUnitEnums:
    def test_resistance_units(self) -> None:
        assert ResistanceUnit.MOHM == "mOhm"
        assert ResistanceUnit.OHM == "Ohm"

    def test_energy_units(self) -> None:
        assert EnergyUnit.KWH == "kWh"
        assert EnergyUnit.WH == "Wh"

    def test_time_units(self) -> None:
        assert TimeUnit.SEC == "sec"
        assert TimeUnit.MIN == "min"
        assert TimeUnit.H == "h"
