# SPH-10000-US UL2.21 split-phase CT and battery-current behavior.
from __future__ import annotations

import importlib
import pytest

gm = importlib.import_module("growatt_under_test.growatt_modbus")
profiles = importlib.import_module("growatt_under_test.profiles")

HU = "SPH_8000_10000_HU"

def _pair(cache, high, watts):
    raw = int(round(watts / 0.1))
    cache[high] = (raw >> 16) & 0xFFFF
    cache[high + 1] = raw & 0xFFFF

def _client(profile=HU):
    return gm.GrowattModbus(
        connection_type="tcp",
        host="10.0.0.1",
        port=502,
        register_map=profile,
    )

def test_hu_maps_split_phase_directional_registers():
    regs = profiles.get_profile(HU)["input_registers"]
    expected = {
        1016: "ct_grid_import_l1_low",
        1018: "ct_grid_import_l2_low",
        1022: "power_to_user_low",
        1024: "ct_grid_export_l1_low",
        1026: "ct_grid_export_l2_low",
        1030: "power_to_grid_low",
        1032: "inverter_to_load_l1_low",
        1034: "inverter_to_load_l2_low",
        1038: "power_to_load_low",
    }
    assert {addr: regs[addr]["name"] for addr in expected} == expected

def test_hu_directional_totals_are_netted_for_whole_service_flow():
    client = _client()
    cache = {}
    _pair(cache, 1015, 900.0)
    _pair(cache, 1017, 300.0)
    _pair(cache, 1021, 1200.0)
    _pair(cache, 1023, 400.0)
    _pair(cache, 1025, 100.0)
    _pair(cache, 1029, 500.0)
    _pair(cache, 1031, 700.0)
    _pair(cache, 1033, 600.0)
    client._register_cache = cache

    data = gm.GrowattData()
    data.power_to_user = 1200.0
    data.power_to_grid = 500.0
    client._apply_split_phase_grid_totals(data)

    assert data.ct_grid_import_total == pytest.approx(1200.0)
    assert data.ct_grid_export_total == pytest.approx(500.0)
    assert data.ct_grid_power == pytest.approx(-700.0)
    assert data.power_to_user == pytest.approx(700.0)
    assert data.power_to_grid == pytest.approx(0.0)
    assert data.grid_to_load_power == pytest.approx(700.0)
    assert data.ct_grid_import_l1 == pytest.approx(900.0)
    assert data.ct_grid_import_l2 == pytest.approx(300.0)
    assert data.ct_grid_export_l1 == pytest.approx(400.0)
    assert data.ct_grid_export_l2 == pytest.approx(100.0)
    assert data.inverter_to_load_l1 == pytest.approx(700.0)
    assert data.inverter_to_load_l2 == pytest.approx(600.0)

def test_hu_export_wins_after_netting():
    client = _client()
    data = gm.GrowattData()
    data.power_to_user = 250.0
    data.power_to_grid = 900.0
    client._apply_split_phase_grid_totals(data)
    assert data.ct_grid_power == pytest.approx(650.0)
    assert data.power_to_grid == pytest.approx(650.0)
    assert data.power_to_user == pytest.approx(0.0)
    assert data.grid_to_load_power == pytest.approx(0.0)

def test_split_phase_netting_is_hu_profile_scoped():
    client = _client("SPH_7000_10000")
    data = gm.GrowattData()
    data.power_to_user = 1200.0
    data.power_to_grid = 500.0
    client._apply_split_phase_grid_totals(data)
    assert data.power_to_user == pytest.approx(1200.0)
    assert data.power_to_grid == pytest.approx(500.0)
    assert not hasattr(data, "ct_grid_power")

def test_hu_1088_is_not_live_battery_current():
    hu_regs = profiles.get_profile(HU)["input_registers"]
    other_regs = profiles.get_profile("SPH_3000_6000")["input_registers"]
    assert hu_regs[1088]["name"] == "bms_current_limit_status"
    assert hu_regs[1088]["scale"] == pytest.approx(0.1)
    assert other_regs[1088]["name"] == "battery_current"
    assert other_regs[1088]["scale"] == pytest.approx(0.01)

@pytest.mark.parametrize(
    ("discharge", "charge", "voltage", "expected"),
    [
        (180.0, 0.0, 52.0, 180.0 / 52.0),
        (0.0, 520.0, 52.0, -10.0),
        (0.0, 0.0, 52.0, 0.0),
    ],
)
def test_hu_live_battery_current_is_derived_from_power(
    discharge, charge, voltage, expected
):
    client = _client()
    data = gm.GrowattData()
    data.discharge_power = discharge
    data.charge_power = charge
    data.battery_voltage = voltage
    data.battery_current = 140.0
    client._derive_profile_battery_current(data)
    assert data.battery_current == pytest.approx(expected)

def test_battery_current_derivation_is_profile_scoped():
    client = _client("SPH_7000_10000")
    data = gm.GrowattData()
    data.discharge_power = 180.0
    data.charge_power = 0.0
    data.battery_voltage = 52.0
    data.battery_current = 12.3
    client._derive_profile_battery_current(data)
    assert data.battery_current == pytest.approx(12.3)

def test_hu_battery_current_is_unread_when_inputs_are_unread():
    client = _client()
    data = gm.GrowattData()
    data.discharge_power = 0.0
    data.charge_power = 0.0
    data.battery_voltage = 52.0
    data.unread_fields.add("charge_power")
    client._derive_profile_battery_current(data)
    assert "battery_current" in data.unread_fields
