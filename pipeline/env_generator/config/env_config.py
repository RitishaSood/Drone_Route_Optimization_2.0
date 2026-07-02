from dataclasses import dataclass


@dataclass
class EnvConfig:

    air_density: float = 1.225
    wind_speed: float = 8.0

    ir_gamma: float = 0.05
    ir_c_bg: float = 0.8

    n_bg: float = 4.0

    visual_lux: float = 0.5
    visual_c_bg: float = 0.2