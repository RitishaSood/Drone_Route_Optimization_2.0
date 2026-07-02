"""
terrain_constants.py
====================

Authoritative terrain definitions.
Must match C++ Part exactly:
enum class TerrainType : uint8_t
{
    Water    = 0,
    Plain    = 1,
    Forest   = 2,
    Hill     = 3,
    Valley   = 4,
    Mountain = 5
};
"""

GRID_SIZE_X = 100
GRID_SIZE_Y = 100
GRID_SIZE_Z = 100

CELL_SIZE_KM = 1.0
Z_STEP_METERS = 100.0

WATER = 0
PLAIN = 1
FOREST = 2
HILL = 3
VALLEY = 4
MOUNTAIN = 5

TERRAIN_NAMES = {
    WATER: "Water",
    PLAIN: "Plain",
    FOREST: "Forest",
    HILL: "Hill",
    VALLEY: "Valley",
    MOUNTAIN: "Mountain"
}