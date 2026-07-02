#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <thread>

#include "../include/CSVLoader.h"
#include "../include/Config.h"
#include "../include/DroneDatabase.h"
#include "../include/FieldGenerator.h"

namespace {
std::string trim(const std::string& value) {
  const auto start = value.find_first_not_of(" \t\r\n");
  if (start == std::string::npos) {
    return "";
  }

  const auto end = value.find_last_not_of(" \t\r\n");
  return value.substr(start, end - start + 1);
}

std::map<std::string, std::string> loadScenarioConfig(
    const std::filesystem::path& filename) {
  std::map<std::string, std::string> values;
  std::ifstream file(filename);

  if (!file.is_open()) {
    return values;
  }

  std::string line;
  while (std::getline(file, line)) {
    line = trim(line);

    if (line.empty() || line[0] == '#') {
      continue;
    }

    const auto equals = line.find('=');
    if (equals == std::string::npos) {
      continue;
    }

    const std::string key = trim(line.substr(0, equals));
    const std::string value = trim(line.substr(equals + 1));

    if (!key.empty()) {
      values[key] = value;
    }
  }

  return values;
}

int getIntConfig(const std::map<std::string, std::string>& values,
                 const std::string& key, int default_value) {
  const auto it = values.find(key);
  if (it == values.end() || it->second.empty()) {
    return default_value;
  }

  try {
    return std::stoi(it->second);
  } catch (...) {
    return default_value;
  }
}

std::string getStringConfig(const std::map<std::string, std::string>& values,
                            const std::string& key,
                            const std::string& default_value) {
  const auto it = values.find(key);
  if (it == values.end() || it->second.empty()) {
    return default_value;
  }

  return it->second;
}
}  // namespace

int main() {
  try {
    std::cout << "=====================================\n"
              << " UAV Probability Field Generator\n"
              << "=====================================\n\n";

    const Config::RuntimePaths paths = Config::getRuntimePaths();
    const std::filesystem::path final_cost_file =
        paths.outputs_dir / "final_cost.csv";
    const std::filesystem::path scenario_file =
        paths.run_dir_enabled ? paths.config_dir / "scenario.env"
                              : std::filesystem::path();

    std::cout << "RUN_DIR mode   : "
              << (paths.run_dir_enabled ? "enabled" : "disabled") << "\n";
    if (paths.run_dir_enabled) {
      std::cout << "Run directory  : " << paths.run_dir.string() << "\n";
    }
    std::cout << "CSV directory  : " << paths.csv_dir.string() << "\n";
    std::cout << "Output directory: " << paths.outputs_dir.string() << "\n";
    std::cout << "Final output   : " << final_cost_file.string() << "\n\n";

    const auto scenario = loadScenarioConfig(scenario_file);
    const int simulation_z =
        getIntConfig(scenario, "FLIGHT_Z", Config::SIMULATION_Z);
    const std::string drone_name =
        getStringConfig(scenario, "DRONE_NAME", "MQ-9 Reaper");

    std::cout << "[1/5] Loading terrain...\n";
    TerrainData terrain = CSVLoader::loadTerrain(
        (paths.csv_dir / "terrain_height.csv").string(),
        (paths.csv_dir / "terrain_type.csv").string());

    std::cout << "[2/5] Loading sensors...\n";
    std::vector<SensorSite> sensors =
        CSVLoader::loadSensors((paths.csv_dir / "sensor.csv").string());

    std::cout << "[3/5] Loading NFZs...\n";
    std::vector<NFZTriangle> nfzs =
        CSVLoader::loadNFZ((paths.csv_dir / "nfz.csv").string());

    std::cout << "[4/5] Loading environment...\n";
    EnvState env =
        CSVLoader::loadEnvironment((paths.csv_dir / "env.csv").string());

    // =====================================================
    // LOAD DRONE
    // =====================================================
    std::cout << "[5/5] Loading drone profile...\n";
    DroneDatabase db;
    DroneState drone = db.getDrone(drone_name, 130.0, 0.0);

    // =====================================================
    // PRINT SUMMARY
    // =====================================================

    std::cout << "\n";
    std::cout << "Grid Size     : " << terrain.width << " x " << terrain.height
              << "\n";
    std::cout << "Sensors       : " << sensors.size() << "\n";
    std::cout << "NFZs          : " << nfzs.size() << "\n";
    std::cout << "Drone         : " << drone.name << "\n";
    std::cout << "Simulation Z  : " << simulation_z << "\n";

    // =====================================================
    // THREAD CONFIG
    // =====================================================

    int num_threads = static_cast<int>(std::thread::hardware_concurrency());
    if (num_threads <= 0) {
      num_threads = Config::DEFAULT_THREADS;
    }
    std::cout << "Threads       : " << num_threads << "\n\n";

    // =====================================================
    // GENERATOR
    // =====================================================

    FieldGenerator generator(terrain, sensors, nfzs, simulation_z);
    std::cout << "Generating probability field...\n";
    generator.generate(drone, env, num_threads);

    // =====================================================
    // EXPORT
    // =====================================================

    std::cout << "Writing " << final_cost_file.string() << "...\n";
    std::filesystem::create_directories(paths.outputs_dir);
    generator.exportCostMatrix(final_cost_file.string());
    std::cout << "\nOutput written to:\n"
              << std::filesystem::absolute(final_cost_file) << "\n";
    return 0;
  } catch (const std::exception& e) {
    std::cerr << "\nFatal Error: " << e.what() << "\n";
    return -1;
  }
}
