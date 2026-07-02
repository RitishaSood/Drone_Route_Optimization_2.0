#pragma once

#include <cstdlib>
#include <cstdint>
#include <filesystem>
#include <string>

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

constexpr int SIMULATION_Z = 40;

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
// RUNTIME PATHS
// =====================================================

struct RuntimePaths {
  bool run_dir_enabled;
  std::filesystem::path run_dir;
  std::filesystem::path data_root_dir;
  std::filesystem::path csv_dir;
  std::filesystem::path data_dir;
  std::filesystem::path outputs_dir;
  std::filesystem::path plots_dir;
  std::filesystem::path config_dir;
};

inline RuntimePaths getRuntimePaths() {
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4996)
#endif
  const char* run_dir_env = std::getenv("RUN_DIR");
#ifdef _MSC_VER
#pragma warning(pop)
#endif
  const bool has_run_dir =
      run_dir_env != nullptr && std::string(run_dir_env).size() > 0;

  if (has_run_dir) {
    const std::filesystem::path run_dir(run_dir_env);

    return RuntimePaths{
        true,
        run_dir,
        run_dir / "data",
        run_dir / "data" / "csv",
        run_dir / "data",
        run_dir / "data" / "outputs",
        run_dir / "data" / "plots",
        run_dir / "config",
    };
  }

  return RuntimePaths{
      false,
      std::filesystem::path(),
      std::filesystem::path("data"),
      std::filesystem::path("data/csv"),
      std::filesystem::path("data"),
      std::filesystem::path("data/outputs"),
      std::filesystem::path("data/plots"),
      std::filesystem::path(),
  };
}

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
