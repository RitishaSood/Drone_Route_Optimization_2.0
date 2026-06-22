"""
sensor_types.py
===============
Defines the data structures for sensor types and placed sensor records.

Two responsibilities:
  1. SENSOR_REGISTRY  — static catalogue of all supported sensor types,
                        including their display properties and which
                        suitability weight dict to use from config.
  2. PlacedSensor     — dataclass representing a single sensor that has
                        been positioned on the grid by PlacementEngine.
                        This is the core output object passed to
                        Visualizer and Exporter.

No placement logic lives here.  No layer computation lives here.
This module is pure data definition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from config import SensorPlacementConfig, DEFAULT_CONFIG


# ---------------------------------------------------------------------------
# SensorType — static descriptor for one category of sensor
# ---------------------------------------------------------------------------

@dataclass
class SensorType:
    """
    Describes a category of sensor: its name, display properties, and
    which weight dict to pull from SuitabilityWeights.

    Attributes
    ----------
    name          : str
        Canonical identifier used as dict key throughout the system
        (must match keys in PlacementConfig.separation / markers / colors
        and SuitabilityWeights fields).
    label         : str
        Human-readable label for plot legends and JSON output.
    weight_key    : str
        Attribute name on SuitabilityWeights that holds this sensor's
        layer weights.  e.g. 'radar' → cfg.weights.radar
    invert_elevation : bool
        If True, LayerBuilder uses (1 − elevation_layer) when computing
        this sensor's suitability.  True only for acoustic sensors
        (lower terrain → less wind noise → better SNR).
    description   : str
        One-line description for documentation / reporting.
    """
    name:             str
    label:            str
    weight_key:       str
    invert_elevation: bool = False
    description:      str  = ""


# ---------------------------------------------------------------------------
# Sensor registry — single catalogue of all sensor types
# ---------------------------------------------------------------------------

# Ordered list used by PlacementEngine and Visualizer to iterate types
# consistently.  Add new sensor types here; no other file needs changing.
SENSOR_TYPES: List[SensorType] = [
    SensorType(
        name='radar',
        label='Radar',
        weight_key='radar',
        invert_elevation=False,
        description=(
            'Ground surveillance radar. Benefits from high elevation for '
            'maximum horizon coverage and minimal ground clutter.'
        ),
    ),
    SensorType(
        name='visual',
        label='Visual / EO',
        weight_key='visual',
        invert_elevation=False,
        description=(
            'Electro-optical camera. Prioritises wide unobstructed sightlines '
            'and proximity to strategically important terrain features.'
        ),
    ),
    SensorType(
        name='infrared',
        label='Infrared / IR',
        weight_key='infrared',
        invert_elevation=False,
        description=(
            'Thermal infrared sensor. Most effective at high-ground outposts '
            'where thermal contrast between targets and background is highest.'
        ),
    ),
    SensorType(
        name='acoustic',
        label='Acoustic',
        weight_key='acoustic',
        invert_elevation=True,   # lower terrain → less wind noise
        description=(
            'Acoustic detection array. Prefers lower-elevation terrain to '
            'reduce wind noise, and strategic zones for maximum event coverage.'
        ),
    ),
]

# Fast lookup by name — used by PlacementEngine and Exporter
SENSOR_REGISTRY: Dict[str, SensorType] = {s.name: s for s in SENSOR_TYPES}


# ---------------------------------------------------------------------------
# PlacedSensor — output record for a single positioned sensor
# ---------------------------------------------------------------------------

@dataclass
class PlacedSensor:
    """
    Represents a sensor after placement.
    """

    sensor_id: int
    sensor_type: str
    row: int
    col: int
    elevation_m: float
    terrain_class: str
    suitability: float

    _cell_size_m: float = field(default=100.0, repr=False, compare=False)

    def __post_init__(self):
        """
        Validate sensor type and compute metric coordinates.
        """
        if self.sensor_type not in SENSOR_REGISTRY:
            raise ValueError(
                f"Invalid sensor type '{self.sensor_type}'. "
                f"Available sensor types: {list(SENSOR_REGISTRY.keys())}"
            )

        self.x_m = self.col * self._cell_size_m
        self.y_m = self.row * self._cell_size_m

    @property
    def type_info(self) -> SensorType:
        """
        Returns SensorType metadata safely.
        """
        sensor_info = SENSOR_REGISTRY.get(self.sensor_type)

        if sensor_info is None:
            raise ValueError(
                f"Sensor type '{self.sensor_type}' not found in registry."
            )

        return sensor_info

    def to_dict(self) -> dict:
        return {
            "id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "label": self.type_info.label,
            "row": self.row,
            "col": self.col,
            "x_m": round(self.x_m, 1),
            "y_m": round(self.y_m, 1),
            "elevation_m": round(self.elevation_m, 2),
            "terrain_class": self.terrain_class,
            "suitability": round(self.suitability, 4),
        }

    def __repr__(self) -> str:
        return (
            f"PlacedSensor(id={self.sensor_id}, "
            f"type={self.sensor_type!r}, "
            f"row={self.row}, col={self.col}, "
            f"elev={self.elevation_m:.0f}m, "
            f"terrain={self.terrain_class!r}, "
            f"score={self.suitability:.3f})"
        )


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_registry(cfg: SensorPlacementConfig = DEFAULT_CONFIG) -> None:
    """
    Cross-check SENSOR_REGISTRY against config at startup.

    Verifies:
      - Every sensor name in SENSOR_REGISTRY has a matching key in
        cfg.weights, cfg.placement.separation, cfg.placement.markers,
        cfg.placement.colors.
      - weight_key attribute on each SensorType points to a real
        attribute on SuitabilityWeights.

    Raises ValueError on the first inconsistency found.
    Called once from main.py after cfg.validate().
    """
    weight_fields = vars(cfg.weights).keys()

    for st in SENSOR_TYPES:
        name = st.name

        if st.weight_key not in weight_fields:
            raise ValueError(
                f"SensorType '{name}': weight_key='{st.weight_key}' not found "
                f"in SuitabilityWeights. Available: {list(weight_fields)}"
            )
        if name not in cfg.placement.separation:
            raise ValueError(
                f"SensorType '{name}' missing from cfg.placement.separation"
            )
        if name not in cfg.placement.markers:
            raise ValueError(
                f"SensorType '{name}' missing from cfg.placement.markers"
            )
        if name not in cfg.placement.colors:
            raise ValueError(
                f"SensorType '{name}' missing from cfg.placement.colors"
            )


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from config import DEFAULT_CONFIG

    # Registry completeness
    assert len(SENSOR_TYPES) == 4
    assert set(SENSOR_REGISTRY.keys()) == {'radar', 'visual', 'infrared', 'acoustic'}
    print(f"PASS  SENSOR_REGISTRY has {len(SENSOR_TYPES)} types")

    # Inversion flag correct
    assert SENSOR_REGISTRY['acoustic'].invert_elevation is True
    assert SENSOR_REGISTRY['radar'].invert_elevation is False
    print("PASS  acoustic invert_elevation=True, radar=False")

    # validate_registry against default config
    validate_registry(DEFAULT_CONFIG)
    print("PASS  validate_registry() — all sensor types consistent with config")

    # PlacedSensor construction and metric conversion
    ps = PlacedSensor(
        sensor_id=1,
        sensor_type='radar',
        row=45,
        col=67,
        elevation_m=823.4,
        terrain_class='Mountain',
        suitability=0.91,
        _cell_size_m=100.0,
    )
    assert ps.x_m == 6700.0, f"Expected x_m=6700.0, got {ps.x_m}"
    assert ps.y_m == 4500.0, f"Expected y_m=4500.0, got {ps.y_m}"
    print(f"PASS  PlacedSensor metric conversion: x_m={ps.x_m}, y_m={ps.y_m}")

    # to_dict schema
    d = ps.to_dict()
    required_keys = {'id', 'sensor_type', 'label', 'row', 'col',
                     'x_m', 'y_m', 'elevation_m', 'terrain_class', 'suitability'}
    assert required_keys.issubset(d.keys()), f"Missing keys: {required_keys - d.keys()}"
    assert d['label'] == 'Radar'
    print(f"PASS  to_dict() schema correct, label='{d['label']}'")

    # repr
    print(f"\nSample repr:\n  {ps!r}")

    print("\nAll sensor_types.py checks passed.")

    # Print registry summary
    print("\nSensor Registry:")
    print(f"  {'Name':<12} {'Label':<16} {'WeightKey':<12} {'InvertElev'}")
    print("  " + "-" * 52)
    for st in SENSOR_TYPES:
        print(f"  {st.name:<12} {st.label:<16} {st.weight_key:<12} {st.invert_elevation}")