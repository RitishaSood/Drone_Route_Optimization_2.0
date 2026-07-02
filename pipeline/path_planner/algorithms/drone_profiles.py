from dataclasses import dataclass


@dataclass(frozen=True)
class DroneFuelProfile:
    name: str
    uav_class: str
    propulsion_class: str

    cruise_speed: float          # m/s, model estimate
    endurance_hours: float       # model estimate
    max_range_km: float          # model estimate

    fuel_capacity: float         # model units
    fuel_burn_per_km: float      # model units / km
    threat_fuel_factor: float    # model units / cost unit
    turn_fuel_penalty: float     # model units / turn
    climb_fuel_factor: float     # model units / z change, future 3D use


DRONE_FUEL_PROFILES = {
    "IAI Heron": DroneFuelProfile(
        name="IAI Heron",
        uav_class="MALE",
        propulsion_class="ICE Piston",
        cruise_speed=40.0,
        endurance_hours=24.0,
        max_range_km=3456.0,
        fuel_capacity=691.2,
        fuel_burn_per_km=0.20,
        threat_fuel_factor=0.005,
        turn_fuel_penalty=0.05,
        climb_fuel_factor=0.08,
    ),

    "Heron TP": DroneFuelProfile(
        name="Heron TP",
        uav_class="HALE",
        propulsion_class="Turboprop",
        cruise_speed=75.0,
        endurance_hours=30.0,
        max_range_km=8100.0,
        fuel_capacity=3645.0,
        fuel_burn_per_km=0.45,
        threat_fuel_factor=0.008,
        turn_fuel_penalty=0.08,
        climb_fuel_factor=0.12,
    ),

    "Rustom-2 (TAPAS BH-201)": DroneFuelProfile(
        name="Rustom-2 (TAPAS BH-201)",
        uav_class="MALE",
        propulsion_class="ICE Piston",
        cruise_speed=42.0,
        endurance_hours=18.0,
        max_range_km=2721.6,
        fuel_capacity=544.32,
        fuel_burn_per_km=0.20,
        threat_fuel_factor=0.005,
        turn_fuel_penalty=0.05,
        climb_fuel_factor=0.08,
    ),

    "Switch UAV": DroneFuelProfile(
        name="Switch UAV",
        uav_class="Tactical",
        propulsion_class="Electric Tactical",
        cruise_speed=15.0,
        endurance_hours=2.0,
        max_range_km=108.0,
        fuel_capacity=5.4,
        fuel_burn_per_km=0.05,
        threat_fuel_factor=0.002,
        turn_fuel_penalty=0.02,
        climb_fuel_factor=0.04,
    ),

    "MQ-9 Reaper": DroneFuelProfile(
        name="MQ-9 Reaper",
        uav_class="MALE",
        propulsion_class="Turboprop",
        cruise_speed=90.0,
        endurance_hours=27.0,
        max_range_km=8748.0,
        fuel_capacity=3936.6,
        fuel_burn_per_km=0.45,
        threat_fuel_factor=0.008,
        turn_fuel_penalty=0.08,
        climb_fuel_factor=0.12,
    ),

    "Swarm Drones": DroneFuelProfile(
        name="Swarm Drones",
        uav_class="Swarm",
        propulsion_class="Electric Tactical",
        cruise_speed=13.0,
        endurance_hours=1.5,
        max_range_km=70.2,
        fuel_capacity=3.51,
        fuel_burn_per_km=0.05,
        threat_fuel_factor=0.002,
        turn_fuel_penalty=0.02,
        climb_fuel_factor=0.04,
    ),

    "DRDO Ghatak": DroneFuelProfile(
        name="DRDO Ghatak",
        uav_class="Stealth UCAV",
        propulsion_class="Jet UCAV",
        cruise_speed=170.0,
        endurance_hours=6.0,
        max_range_km=3672.0,
        fuel_capacity=3304.8,
        fuel_burn_per_km=0.90,
        threat_fuel_factor=0.012,
        turn_fuel_penalty=0.15,
        climb_fuel_factor=0.20,
    ),

    "Searcher": DroneFuelProfile(
        name="Searcher",
        uav_class="Tactical",
        propulsion_class="ICE Piston",
        cruise_speed=36.0,
        endurance_hours=16.0,
        max_range_km=2073.6,
        fuel_capacity=414.72,
        fuel_burn_per_km=0.20,
        threat_fuel_factor=0.005,
        turn_fuel_penalty=0.05,
        climb_fuel_factor=0.08,
    ),

    "Harpy": DroneFuelProfile(
        name="Harpy",
        uav_class="Loitering Munition",
        propulsion_class="ICE Piston",
        cruise_speed=75.0,
        endurance_hours=6.0,
        max_range_km=1620.0,
        fuel_capacity=324.0,
        fuel_burn_per_km=0.20,
        threat_fuel_factor=0.005,
        turn_fuel_penalty=0.05,
        climb_fuel_factor=0.08,
    ),

    "Rooster": DroneFuelProfile(
        name="Rooster",
        uav_class="Electric Nano",
        propulsion_class="Electric Nano",
        cruise_speed=7.0,
        endurance_hours=0.5,
        max_range_km=12.6,
        fuel_capacity=0.252,
        fuel_burn_per_km=0.02,
        threat_fuel_factor=0.001,
        turn_fuel_penalty=0.01,
        climb_fuel_factor=0.02,
    ),

    "Black Hornet": DroneFuelProfile(
        name="Black Hornet",
        uav_class="Electric Nano",
        propulsion_class="Electric Nano",
        cruise_speed=4.0,
        endurance_hours=0.4,
        max_range_km=5.76,
        fuel_capacity=0.1152,
        fuel_burn_per_km=0.02,
        threat_fuel_factor=0.001,
        turn_fuel_penalty=0.01,
        climb_fuel_factor=0.02,
    ),

    "Nagastra-1": DroneFuelProfile(
        name="Nagastra-1",
        uav_class="Loitering Munition",
        propulsion_class="Electric Tactical",
        cruise_speed=17.0,
        endurance_hours=1.5,
        max_range_km=91.8,
        fuel_capacity=4.59,
        fuel_burn_per_km=0.05,
        threat_fuel_factor=0.002,
        turn_fuel_penalty=0.02,
        climb_fuel_factor=0.04,
    ),

    "Netra UAV": DroneFuelProfile(
        name="Netra UAV",
        uav_class="Tactical",
        propulsion_class="Electric Nano",
        cruise_speed=5.0,
        endurance_hours=0.5,
        max_range_km=9.0,
        fuel_capacity=0.18,
        fuel_burn_per_km=0.02,
        threat_fuel_factor=0.001,
        turn_fuel_penalty=0.01,
        climb_fuel_factor=0.02,
    ),
}


DEFAULT_DRONE_NAME = "IAI Heron"


def get_drone_fuel_profile(drone_name: str | None) -> DroneFuelProfile:
    if not drone_name:
        return DRONE_FUEL_PROFILES[DEFAULT_DRONE_NAME]

    return DRONE_FUEL_PROFILES.get(
        drone_name,
        DRONE_FUEL_PROFILES[DEFAULT_DRONE_NAME],
    )