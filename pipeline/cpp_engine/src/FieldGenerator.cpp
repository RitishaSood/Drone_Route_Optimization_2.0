#include <cmath>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <thread>
#include "../include/FieldGenerator.h"

FieldGenerator::FieldGenerator(const TerrainData& terrain, const std::vector<SensorSite>& sensors, const std::vector<NFZTriangle>& nfzs, int simulation_z)
    : terrain(terrain),
      sensors(sensors),
      config{simulation_z,
             true,
             true,
             true,
             true,
             true,
             false,
             1.0,
             1.0,
             1.0,
             1.0},
      nfzs(nfzs) {
  final_cost.resize(terrain.width * terrain.height, 0.0);
  nfz_mask.resize(terrain.width * terrain.height, false);
  buildNFZMask();
}

bool FieldGenerator::pointInsideTriangle(int px, int py, const NFZTriangle& t) const {
  double denom = (t.y2 - t.y3) * (t.x1 - t.x3) + (t.x3 - t.x2) * (t.y1 - t.y3);
  if (std::abs(denom) < 1e-9) return false;
  double a =
      ((t.y2 - t.y3) * (px - t.x3) + (t.x3 - t.x2) * (py - t.y3)) / denom;
  double b =
      ((t.y3 - t.y1) * (px - t.x3) + (t.x1 - t.x3) * (py - t.y3)) / denom;
  double c = 1.0 - a - b;
  return a >= 0.0 && b >= 0.0 && c >= 0.0;
}

void FieldGenerator::buildNFZMask() {
  for (int y = 0; y < terrain.height; ++y) {
    for (int x = 0; x < terrain.width; ++x) {
      int idx = y * terrain.width + x;
      bool inside = false;
      for (const auto& nfz : nfzs) {
        if (pointInsideTriangle(x, y, nfz)) {
          inside = true;
          break;
        }
      }
      nfz_mask[idx] = inside;
    }
  }
}

void FieldGenerator::calculateChunk(int start_y, int end_y, const DroneState& drone, const EnvState& env) {
  DynamicSignature dyn_sig;
  double v_ratio = drone.speed / drone.max_speed;
  dyn_sig.v_ratio = v_ratio;
  dyn_sig.v_sq = v_ratio * v_ratio;
  dyn_sig.v_cubed = dyn_sig.v_sq * v_ratio;
  dyn_sig.i_dynamic = drone.i_base * (1.0 + drone.c_drag * dyn_sig.v_cubed);
  dyn_sig.s_dynamic = drone.s_idle * (1.0 + drone.c_aero * dyn_sig.v_sq);

  for (int y = start_y; y < end_y; ++y) {
    for (int x = 0; x < terrain.width; ++x) {
      int idx = y * terrain.width + x;

      if (nfz_mask[idx]) {
        final_cost[idx] = Config::NFZ_COST;

        continue;
      }

      double combined_escape = 1.0;

      for (const auto& sensor : sensors) {
        double risk = 0.0;

        switch (sensor.type) {
          case SensorType::Radar: {
            RadarThreat radar(sensor);

            risk = radar.calculateRisk(x, y, config.simulation_z, drone,
                                       dyn_sig, env, terrain);

            break;
          }

          case SensorType::Infrared: {
            IRThreat ir(sensor);

            risk = ir.calculateRisk(x, y, config.simulation_z, drone, dyn_sig,
                                    env, terrain);

            break;
          }

          case SensorType::Acoustic: {
            AcousticThreat ac(sensor);

            risk = ac.calculateRisk(x, y, config.simulation_z, drone, dyn_sig,
                                    env, terrain);

            break;
          }

          case SensorType::Visual: {
            VisualThreat vis(sensor);

            risk = vis.calculateRisk(x, y, config.simulation_z, drone, dyn_sig,
                                     env, terrain);

            break;
          }

          default:
            break;
        }

        combined_escape *= (1.0 - risk);
      }

      final_cost[idx] = 1.0 - combined_escape;
    }
  }
}

void FieldGenerator::generate(const DroneState& drone, const EnvState& env,
                              int num_threads) {
  std::vector<std::thread> workers;

  int rows_per_thread = terrain.height / num_threads;

  int current_y = 0;

  for (int i = 0; i < num_threads; ++i) {
    int end_y =
        (i == num_threads - 1) ? terrain.height : current_y + rows_per_thread;

    workers.emplace_back(&FieldGenerator::calculateChunk, this, current_y,
                         end_y, std::cref(drone), std::cref(env));

    current_y = end_y;
  }

  for (auto& t : workers) {
    t.join();
  }
}

void FieldGenerator::exportCostMatrix(const std::string& filename) const {
  std::ofstream file(filename);

  if (!file.is_open()) {
    throw std::runtime_error("Unable to write cost matrix.");
  }

  for (int row = 0; row < terrain.height; ++row) {
    int y = terrain.height - 1 - row;
    for (int x = 0; x < terrain.width; ++x) {
      int idx = y * terrain.width + x;

      file << std::fixed << std::setprecision(6) << final_cost[idx];

      if (x != terrain.width - 1) {
        file << ",";
      }
    }

    file << "\n";
  }
}

const std::vector<double>& FieldGenerator::getCostMatrix() const {
  return final_cost;
}
