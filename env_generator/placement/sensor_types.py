from dataclasses import dataclass

@dataclass(frozen=True)
class SensorType:

    name: str
    label: str


RADAR = SensorType(
    "radar",
    "Radar"
)

INFRARED = SensorType(
    "infrared",
    "IR"
)

VISUAL = SensorType(
    "visual",
    "Visual"
)

ACOUSTIC = SensorType(
    "acoustic",
    "Acoustic"
)

SENSOR_TYPES = [
    RADAR,
    INFRARED,
    VISUAL,
    ACOUSTIC
]