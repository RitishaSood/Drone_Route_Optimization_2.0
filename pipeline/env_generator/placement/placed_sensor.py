from dataclasses import dataclass


@dataclass
class PlacedSensor:

    sensor_id: int

    sensor_type: str
    label: str

    x: int
    y: int
    z: int

    terrain_class: int

    suitability_score: float = 0.0

    def to_csv_row(self):

        return [
            self.sensor_id,
            self.sensor_type,
            self.label,
            self.x,
            self.y,
            self.z,
            self.terrain_class
        ]