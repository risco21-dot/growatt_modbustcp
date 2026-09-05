"""Growatt Inverter Profile Collection.

This package contains individual profile files for each inverter series.
Each profile defines register maps with proper integer keys and paired registers.

Profile Structure:
- min.py: MIN series (3-10kW single-phase)
- mid.py: MID series (15-25kW three-phase)
- mod.py: MOD series (6-15kW three-phase hybrid)
- tl_xh.py: TL-XH series (3-10kW hybrid)
- sph.py: SPH series (storage/battery)
- sph_tl3.py: SPH-TL3 series (three-phase hybrid with battery)
- spa.py: SPA series (AC-coupled battery storage, no PV inputs)
- spf.py: SPF series (off-grid with battery)
- spe.py: SPE series (off-grid, larger capacity, SPF protocol)
- wit.py: WIT series (4-15kW three-phase hybrid with advanced storage)
- tl3s.py: TL3-S series (3-15kW three-phase grid-tied, legacy protocol)
"""

from typing import Dict, List, Optional

# Import register maps from individual profile files
from .mic import MIC_REGISTER_MAPS
from .min import MIN_REGISTER_MAPS
from .mid import MID_REGISTER_MAPS
from .sph import SPH_REGISTER_MAPS
from .sph_tl3 import SPH_TL3_REGISTER_MAPS
from .spa import SPA_REGISTER_MAPS
from .spf import SPF_REGISTER_MAPS
from .spe import SPE_REGISTER_MAPS
from .mod import MOD_REGISTER_MAPS
from .tl_xh import TL_XH_REGISTER_MAPS
from .wit import WIT_REGISTER_MAPS
from .tl3s import TL3S_REGISTER_MAPS


# Combine all register maps into single dict
REGISTER_MAPS = {
    **MIC_REGISTER_MAPS,
    **MIN_REGISTER_MAPS,
    **MID_REGISTER_MAPS,
    **SPH_REGISTER_MAPS,
    **SPH_TL3_REGISTER_MAPS,
    **SPA_REGISTER_MAPS,
    **SPF_REGISTER_MAPS,
    **SPE_REGISTER_MAPS,
    **MOD_REGISTER_MAPS,
    **TL_XH_REGISTER_MAPS,
    **WIT_REGISTER_MAPS,
    **TL3S_REGISTER_MAPS,
}

# TEMPORARY FIELD-DATA OVERRIDE — SPH-10000-US / UL2.21 only.
#
# This diagnostic branch intentionally restores register 1088 to the historical
# `battery_current` entity at 0.1 A/count so Home Assistant Recorder can collect
# several full charge/discharge cycles against SOC. On this HU firmware the value
# does NOT represent instantaneous pack current; historical captures show 140 A at
# 78% SOC and 40 A at 99% SOC while battery power is near zero. The purpose here is
# continuity with the old recorder entity so the exact SOC transition points can be
# measured. Do not merge this override upstream.
_hu_diag = REGISTER_MAPS.get("SPH_8000_10000_HU")
if _hu_diag is not None:
    _hu_diag["derive_battery_current_from_power"] = False
    _hu_diag.setdefault("input_registers", {})[1088] = {
        "name": "battery_current",
        "scale": 0.1,
        "unit": "A",
        "desc": "TEMP HU diagnostic: raw 1088 at historical 0.1 A/count; not instantaneous battery current",
    }


def get_profile(profile_key: str) -> Optional[Dict]:
    """Get a profile by its key.
    
    Args:
        profile_key: Profile identifier (e.g., 'MIN_7000_10000TL_X')
    
    Returns:
        Profile dictionary with 'input_registers' and 'holding_registers' keys
        or None if not found
    """
    return REGISTER_MAPS.get(profile_key)


def get_available_profiles() -> Dict[str, str]:
    """Get all available profiles as key: name pairs.
    
    Returns:
        Dictionary mapping profile keys to display names
    """
    return {
        key: profile.get("name", key)
        for key, profile in REGISTER_MAPS.items()
    }


def get_profile_keys() -> List[str]:
    """Get list of all profile keys.
    
    Returns:
        List of profile key strings
    """
    return list(REGISTER_MAPS.keys())


def list_profiles():
    """Print all available profiles with descriptions."""
    print("Available Growatt Inverter Profiles")
    print("=" * 60)
    for key, profile in REGISTER_MAPS.items():
        print(f"\n{key}:")
        print(f"  Name: {profile.get('name', 'N/A')}")
        print(f"  Description: {profile.get('description', 'N/A')}")
        if 'notes' in profile:
            print(f"  Notes: {profile['notes']}")
        # Count registers
        input_regs = len(profile.get('input_registers', {}))
        holding_regs = len(profile.get('holding_registers', {}))
        print(f"  Registers: {input_regs} input, {holding_regs} holding")


__all__ = [
    "REGISTER_MAPS",
    "get_profile",
    "get_available_profiles",
    "get_profile_keys",
    "list_profiles",
]