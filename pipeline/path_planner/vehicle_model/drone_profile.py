from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DronePerformanceProfile:
    name: str
    uav_class: str
    propulsion_class: str
    cruise_speed_mps: float
    min_speed_mps: float
    max_speed_mps: float
    max_acceleration_mps2: float
    fuel_capacity: float
    base_fuel_burn_per_km: float
    climb_fuel_factor: float
    turn_fuel_factor: float
    acceleration_fuel_factor: float
    wind_fuel_factor: float
    weather_fuel_factor: float
    health_capacity: float
    base_wear_per_km: float
    climb_wear_factor: float
    turn_wear_factor: float
    acceleration_wear_factor: float
    turbulence_wear_factor: float
    rain_wear_factor: float
    hail_wear_factor: float
    wind_sensitivity: float
    rain_sensitivity: float
    temperature_sensitivity: float
    max_wind_tolerance_mps: float
    max_operating_temperature_c: float
    min_operating_temperature_c: float


# These values are simplified simulation estimates used for algorithm comparison.
DRONE_PERFORMANCE_PROFILES = {
    "IAI Heron": DronePerformanceProfile(
        name="IAI Heron",
        uav_class="MALE",
        propulsion_class="ICE Piston",
        cruise_speed_mps=40.0,
        min_speed_mps=18.0,
        max_speed_mps=80.0,
        max_acceleration_mps2=4.0,
        fuel_capacity=691.2,
        base_fuel_burn_per_km=0.20,
        climb_fuel_factor=0.08,
        turn_fuel_factor=0.05,
        acceleration_fuel_factor=0.10,
        wind_fuel_factor=0.10,
        weather_fuel_factor=0.10,
        health_capacity=100.0,
        base_wear_per_km=0.01,
        climb_wear_factor=0.05,
        turn_wear_factor=0.01,
        acceleration_wear_factor=0.01,
        turbulence_wear_factor=0.5,
        rain_wear_factor=0.2,
        hail_wear_factor=0.8,
        wind_sensitivity=0.10,
        rain_sensitivity=0.20,
        temperature_sensitivity=0.05,
        max_wind_tolerance_mps=20.0,
        max_operating_temperature_c=55.0,
        min_operating_temperature_c=-20.0,
    ),
}

def _clone(base: DronePerformanceProfile, **kwargs) -> DronePerformanceProfile:
    data = base.__dict__.copy()
    data.update(kwargs)
    return DronePerformanceProfile(**data)

DRONE_PERFORMANCE_PROFILES.update({
    "Heron TP": _clone(DRONE_PERFORMANCE_PROFILES["IAI Heron"], name="Heron TP", uav_class="HALE", propulsion_class="Turboprop", cruise_speed_mps=75.0, max_speed_mps=120.0, max_wind_tolerance_mps=24.0, fuel_capacity=3645.0, base_fuel_burn_per_km=0.45),
    "Rustom-2 (TAPAS BH-201)": _clone(DRONE_PERFORMANCE_PROFILES["IAI Heron"], name="Rustom-2 (TAPAS BH-201)", cruise_speed_mps=42.0, fuel_capacity=544.32),
    "Switch UAV": _clone(DRONE_PERFORMANCE_PROFILES["IAI Heron"], name="Switch UAV", uav_class="Tactical", propulsion_class="Electric Tactical", cruise_speed_mps=15.0, max_speed_mps=25.0, fuel_capacity=5.4, base_fuel_burn_per_km=0.05),
    "MQ-9 Reaper": _clone(DRONE_PERFORMANCE_PROFILES["IAI Heron"], name="MQ-9 Reaper", uav_class="MALE", propulsion_class="Turboprop", cruise_speed_mps=90.0, max_speed_mps=140.0, fuel_capacity=3936.6, base_fuel_burn_per_km=0.45),
    "Swarm Drones": _clone(DRONE_PERFORMANCE_PROFILES["IAI Heron"], name="Swarm Drones", uav_class="Swarm", propulsion_class="Electric Tactical", cruise_speed_mps=13.0, max_speed_mps=20.0, fuel_capacity=3.51, base_fuel_burn_per_km=0.05),
    "DRDO Ghatak": _clone(DRONE_PERFORMANCE_PROFILES["IAI Heron"], name="DRDO Ghatak", uav_class="Stealth UCAV", propulsion_class="Jet UCAV", cruise_speed_mps=170.0, max_speed_mps=260.0, fuel_capacity=3304.8, base_fuel_burn_per_km=0.90),
    "Searcher": _clone(DRONE_PERFORMANCE_PROFILES["IAI Heron"], name="Searcher", uav_class="Tactical", cruise_speed_mps=36.0, fuel_capacity=414.72),
    "Harpy": _clone(DRONE_PERFORMANCE_PROFILES["IAI Heron"], name="Harpy", uav_class="Loitering Munition", cruise_speed_mps=75.0, fuel_capacity=324.0),
    "Rooster": _clone(DRONE_PERFORMANCE_PROFILES["IAI Heron"], name="Rooster", uav_class="Electric Nano", propulsion_class="Electric Nano", cruise_speed_mps=7.0, max_speed_mps=12.0, fuel_capacity=0.252),
    "Black Hornet": _clone(DRONE_PERFORMANCE_PROFILES["IAI Heron"], name="Black Hornet", uav_class="Electric Nano", propulsion_class="Electric Nano", cruise_speed_mps=4.0, max_speed_mps=8.0, fuel_capacity=0.1152),
    "Nagastra-1": _clone(DRONE_PERFORMANCE_PROFILES["IAI Heron"], name="Nagastra-1", uav_class="Loitering Munition", propulsion_class="Electric Tactical", cruise_speed_mps=17.0, fuel_capacity=4.59),
    "Netra UAV": _clone(DRONE_PERFORMANCE_PROFILES["IAI Heron"], name="Netra UAV", uav_class="Tactical", propulsion_class="Electric Nano", cruise_speed_mps=5.0, max_speed_mps=10.0, fuel_capacity=0.18),
})

DEFAULT_DRONE_NAME = "IAI Heron"

def get_drone_profile(drone_name: str | None) -> DronePerformanceProfile:
    if not drone_name:
        return DRONE_PERFORMANCE_PROFILES[DEFAULT_DRONE_NAME]
    if drone_name in DRONE_PERFORMANCE_PROFILES:
        return DRONE_PERFORMANCE_PROFILES[drone_name]
    lowered = drone_name.lower()
    for key, value in DRONE_PERFORMANCE_PROFILES.items():
        if key.lower() == lowered:
            return value
    return DRONE_PERFORMANCE_PROFILES[DEFAULT_DRONE_NAME]
