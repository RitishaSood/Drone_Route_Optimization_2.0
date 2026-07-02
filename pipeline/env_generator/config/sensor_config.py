from dataclasses import dataclass

@dataclass
class SensorConfig:

    radar_count: int = 8
    infrared_count: int = 8
    acoustic_count: int = 8
    visual_count: int = 8