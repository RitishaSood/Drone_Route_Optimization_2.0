from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DroneFuelProfile:
    name: str
    uav_class: str
    propulsion_class: str
    cruise_speed: float
    endurance_hours: float
    max_range_km: float
    fuel_capacity: float
    fuel_burn_per_km: float
    threat_fuel_factor: float
    turn_fuel_penalty: float
    climb_fuel_factor: float


DRONE_FUEL_PROFILES = {
    "IAI Heron": DroneFuelProfile(
        name="IAI Heron",
        uav_class="MALE UAV",
        propulsion_class="piston",
        cruise_speed=140.0,
        endurance_hours=45.0,
        max_range_km=1000.0,
        fuel_capacity=1000.0,
        fuel_burn_per_km=1.0,
        threat_fuel_factor=0.01,
        turn_fuel_penalty=0.5,
        climb_fuel_factor=0.0,
    ),
    "Heron TP": DroneFuelProfile(
        name="Heron TP",
        uav_class="MALE UAV",
        propulsion_class="turboprop",
        cruise_speed=220.0,
        endurance_hours=30.0,
        max_range_km=1500.0,
        fuel_capacity=1200.0,
        fuel_burn_per_km=1.2,
        threat_fuel_factor=0.012,
        turn_fuel_penalty=0.55,
        climb_fuel_factor=0.0,
    ),
}


def get_drone_fuel_profile(drone_name: str | None) -> DroneFuelProfile:
    if drone_name in DRONE_FUEL_PROFILES:
        return DRONE_FUEL_PROFILES[drone_name]
    return DRONE_FUEL_PROFILES["IAI Heron"]
