#pragma once

#include <cstdint>

namespace Config {
// =====================================================
// WORLD DIMENSIONS
// =====================================================
constexpr double PI = 3.14159265358979323846;
constexpr int GRID_WIDTH = 100;
constexpr int GRID_HEIGHT = 100;

constexpr int Z_MIN = 0;
constexpr int Z_MAX = 100;

// =====================================================
// UNIT CONVERSIONS
// =====================================================

constexpr double XY_CELL_SIZE_METERS = 1000.0;

constexpr double Z_UNIT_METERS = 100.0;

// =====================================================
// SIMULATION MODE
// =====================================================

enum class SimulationMode { Mode25D, Mode3D };

constexpr SimulationMode CURRENT_MODE = SimulationMode::Mode25D;

constexpr int SIMULATION_Z = 70;

// =====================================================
// COSTS
// =====================================================

constexpr double NFZ_COST = 999999.0;

constexpr double MIN_COST = 0.0;
constexpr double MAX_COST = 1.0;

// =====================================================
// THREADING
// =====================================================

constexpr int DEFAULT_THREADS = 8;

// =====================================================
// RANDOMIZATION
// =====================================================

constexpr unsigned RANDOM_SEED = 42;

// =====================================================
// TERRAIN TYPES
// =====================================================

enum class TerrainType : uint8_t {

  Water = 0,
  Plain = 1,
  Forest = 2,
  Hill = 3,
  Valley = 4,
  Mountain = 5
};

// =====================================================
// DEFAULT SENSOR PARAMETERS
// =====================================================

namespace SensorDefaults {
constexpr double RADAR_R0 = 4000.0;
constexpr double RADAR_DIFFRACTION_K = 0.15;
constexpr double RADAR_MASK_THRESHOLD = 20.0;

constexpr double IR_K = 1000.0;

constexpr double ACOUSTIC_K = 500.0;

constexpr double VISUAL_K = 750.0;
}  // namespace SensorDefaults
}  // namespace Config