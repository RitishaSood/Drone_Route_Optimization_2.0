from terrain.terrain_constants import (
    FOREST,
    HILL,
    MOUNTAIN,
    PLAIN,
    VALLEY,
    WATER,
)

TERRAIN_COLORS = {
    WATER: "#2B6CB0",
    PLAIN: "#D9C27C",
    FOREST: "#2F855A",
    HILL: "#B7791F",
    VALLEY: "#436B48",
    MOUNTAIN: "#A0AEC0",
}

SENSOR_COLORS = {
    "radar": "red",
    "infrared": "orange",
    "acoustic": "purple",
    "visual": "blue",
}

SENSOR_MARKERS = {
    "radar": "^",
    "infrared": "s",
    "acoustic": "o",
    "visual": "D",
}
