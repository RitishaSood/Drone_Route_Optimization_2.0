#include <cctype>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>

#include "../include/CSVLoader.h"
#include "../include/Config.h"

TerrainData CSVLoader::loadTerrain(const std::string& height_file, const std::string& type_file) {
  TerrainData terrain;
  terrain.width = 100;
  terrain.height = 100;
  terrain.elevation.reserve(10000);
  terrain.terrain_type.reserve(10000);

  // HEIGHT
  {
    std::ifstream file(height_file);

    if (!file.is_open()) {
      throw std::runtime_error("Unable to open terrain height csv.");
    }

    std::string line;

    while (std::getline(file, line)) {
      std::stringstream ss(line);

      std::string value;

      while (std::getline(ss, value, ',')) {
        terrain.elevation.push_back(std::stod(value));
      }
    }
  }

  // TYPE
  {
    std::ifstream file(type_file);

    if (!file.is_open()) {
      throw std::runtime_error("Unable to open terrain type csv.");
    }

    std::string line;

    while (std::getline(file, line)) {
      std::stringstream ss(line);
      std::string value;
      while (std::getline(ss, value, ',')) {
        terrain.terrain_type.push_back(static_cast<uint8_t>(std::stoi(value)));
      }
    }
  }

  return terrain;
}

std::vector<SensorSite> CSVLoader::loadSensors(const std::string& filename) {
  std::vector<SensorSite> sensors;

  std::ifstream file(filename);

  if (!file.is_open()) {
    throw std::runtime_error("Unable to open sensor csv.");
  }

  std::string line;

  // Skip header
  std::getline(file, line);

  while (std::getline(file, line)) {
    if (line.empty()) {
      continue;
    }

    std::stringstream ss(line);
    std::vector<std::string> fields;
    std::string value;

    while (std::getline(ss, value, ',')) {
      fields.push_back(value);
    }

    if (fields.size() != 7) {
      throw std::runtime_error("Malformed sensor row: " + line);
    }

    SensorSite sensor;

    // Basic Info
    sensor.id = std::stoi(fields[0]);

    std::string sensor_type = fields[1];

    for (char& c : sensor_type) {
      c = static_cast<char>(std::tolower(c));
    }

    if (sensor_type == "radar") {
      sensor.type = SensorType::Radar;
    } else if (sensor_type == "infrared") {
      sensor.type = SensorType::Infrared;
    } else if (sensor_type == "acoustic") {
      sensor.type = SensorType::Acoustic;
    } else if (sensor_type == "visual") {
      sensor.type = SensorType::Visual;
    } else {
      throw std::runtime_error("Unknown sensor type: " + fields[1]);
    }

    sensor.label = fields[2];

    sensor.x = std::stod(fields[3]);
    sensor.y = std::stod(fields[4]);
    sensor.z = std::stod(fields[5]);

    // Terrain Type
    sensor.terrain_type = static_cast<uint8_t>(std::stoi(fields[6]));

    if (sensor.terrain_type > 5) {
      throw std::runtime_error("Invalid terrain type id in sensor.csv");
    }

    // Default Sensor Parameters
    switch (sensor.type) {
      case SensorType::Radar:
        sensor.max_range = 10000.0;
        sensor.R0 = Config::SensorDefaults::RADAR_R0;
        sensor.diffraction_k = Config::SensorDefaults::RADAR_DIFFRACTION_K;
        sensor.deep_mask_threshold = Config::SensorDefaults::RADAR_MASK_THRESHOLD;
        break;

      case SensorType::Infrared:
        sensor.max_range = 5000.0;
        sensor.K_ir = Config::SensorDefaults::IR_K;
        break;

      case SensorType::Acoustic:
        sensor.max_range = 3000.0;
        sensor.K_ac = Config::SensorDefaults::ACOUSTIC_K;
        break;

      case SensorType::Visual:
        sensor.max_range = 7500.0;
        sensor.K_vis = Config::SensorDefaults::VISUAL_K;
        break;

      default:
        break;
    }

    sensors.push_back(sensor);
  }

  return sensors;
}

EnvState CSVLoader::loadEnvironment(const std::string& filename) {
  EnvState env{};

  std::ifstream file(filename);

  if (!file.is_open()) {
    throw std::runtime_error("Unable to open env csv.");
  }

  std::string line;

  while (std::getline(file, line)) {
    std::stringstream ss(line);

    std::string key;
    std::string value;

    std::getline(ss, key, ',');
    std::getline(ss, value, ',');

    if (key == "air_density")
      env.air_density = std::stod(value);

    else if (key == "wind_speed")
      env.wind_speed = std::stod(value);

    else if (key == "ir_gamma")
      env.ir_gamma = std::stod(value);

    else if (key == "ir_c_bg")
      env.ir_c_bg = std::stod(value);

    else if (key == "n_bg")
      env.n_bg = std::stod(value);

    else if (key == "visual_lux")
      env.visual_lux = std::stod(value);

    else if (key == "visual_c_bg")
      env.visual_c_bg = std::stod(value);
  }

  return env;
}

std::vector<NFZTriangle> CSVLoader::loadNFZ(const std::string& filename) {
  std::vector<NFZTriangle> nfzs;

  std::ifstream file(filename);

  if (!file.is_open()) {
    throw std::runtime_error("Failed to open nfz.csv");
  }

  std::string line;

  // Skip header
  std::getline(file, line);

  while (std::getline(file, line)) {
    if (line.empty()) {
      continue;
    }

    std::stringstream ss(line);

    std::vector<std::string> fields;
    std::string token;

    while (std::getline(ss, token, ',')) {
      fields.push_back(token);
    }

    if (fields.size() != 11) {
      throw std::runtime_error("Malformed NFZ row: " + line);
    }

    NFZTriangle nfz;

    // CSV:
    // Cid,type,x1,y1,z1,x2,y2,z2,x3,y3,z3

    nfz.id = std::stoi(fields[0]);

    // fields[1] = "NFZ"

    nfz.x1 = std::stoi(fields[2]);
    nfz.y1 = std::stoi(fields[3]);

    nfz.x2 = std::stoi(fields[5]);
    nfz.y2 = std::stoi(fields[6]);

    nfz.x3 = std::stoi(fields[8]);
    nfz.y3 = std::stoi(fields[9]);

    // Bounds check
    if (nfz.x1 < 0 || nfz.x1 >= Config::GRID_WIDTH || nfz.y1 < 0 ||
        nfz.y1 >= Config::GRID_HEIGHT || nfz.x2 < 0 ||
        nfz.x2 >= Config::GRID_WIDTH || nfz.y2 < 0 ||
        nfz.y2 >= Config::GRID_HEIGHT || nfz.x3 < 0 ||
        nfz.x3 >= Config::GRID_WIDTH || nfz.y3 < 0 ||
        nfz.y3 >= Config::GRID_HEIGHT) {
      throw std::runtime_error("NFZ coordinate outside map bounds.");
    }

    nfzs.push_back(nfz);
  }

  return nfzs;
}