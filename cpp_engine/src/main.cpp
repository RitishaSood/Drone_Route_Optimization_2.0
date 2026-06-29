#include <filesystem>
#include <iostream>
#include <thread>

#include "../include/CSVLoader.h"
#include "../include/Config.h"
#include "../include/DroneDatabase.h"
#include "../include/FieldGenerator.h"

int main() {
  try {
    std::cout << "=====================================\n"
              << " UAV Probability Field Generator\n"
              << "=====================================\n\n";

    std::cout << "[1/5] Loading terrain...\n";
    TerrainData terrain = CSVLoader::loadTerrain("data/terrain_height.csv", "data/terrain_type.csv");

    std::cout << "[2/5] Loading sensors...\n";
    std::vector<SensorSite> sensors = CSVLoader::loadSensors("data/sensor.csv");

    std::cout << "[3/5] Loading NFZs...\n";
    std::vector<NFZTriangle> nfzs = CSVLoader::loadNFZ("data/nfz.csv");

    std::cout << "[4/5] Loading environment...\n";
    EnvState env = CSVLoader::loadEnvironment("data/env.csv");

    // =====================================================
    // LOAD DRONE
    // =====================================================
    std::cout << "[5/5] Loading drone profile...\n";
    DroneDatabase db;
    DroneState drone = db.getDrone("MQ-9 Reaper", 130.0, 0.0);

    // =====================================================
    // PRINT SUMMARY
    // =====================================================

    std::cout << "\n";
    std::cout << "Grid Size     : " << terrain.width << " x " << terrain.height
              << "\n";
    std::cout << "Sensors       : " << sensors.size() << "\n";
    std::cout << "NFZs          : " << nfzs.size() << "\n";
    std::cout << "Drone         : " << drone.name << "\n";
    std::cout << "Simulation Z  : " << Config::SIMULATION_Z << "\n";

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

    FieldGenerator generator(terrain, sensors, nfzs);
    std::cout << "Generating probability field...\n";
    generator.generate(drone, env, num_threads);

    // =====================================================
    // EXPORT
    // =====================================================

    std::cout << "Writing outputs/final_cost.csv...\n";
    std::filesystem::create_directories("outputs");
    generator.exportCostMatrix("outputs/final_cost.csv");
    std::cout << "\nOutput written to:\n"
              << std::filesystem::absolute("outputs/final_cost.csv") << "\n";
    return 0;
  } catch (const std::exception& e) {
    std::cerr << "\nFatal Error: " << e.what() << "\n";
    return -1;
  }
}