#include "../include/FieldGenerator.h"
#include <iostream>
#include <iomanip>
#include <fstream>
#include <thread>
#include <stdexcept>

FieldGenerator::FieldGenerator(int w, int h) : width(w), height(h) {
    int total_cells = width * height;
    terrain_grid.resize(total_cells, 0.0); 
    radar_field.resize(total_cells, 0.0);
    ir_field.resize(total_cells, 0.0);
    acoustic_field.resize(total_cells, 0.0);
    visual_field.resize(total_cells, 0.0);
    wind_field.resize(total_cells, 0.0);
    nfz_mask.resize(total_cells, false);
}

void FieldGenerator::setTerrain(const std::vector<double>& terrain) {
    if (terrain.size() != width * height) throw std::runtime_error("Terrain size mismatch");
    terrain_grid = terrain;
}

void FieldGenerator::addRadar(double x, double y, double z, double r0, double max_range, double diff_k, double mask_thresh) {
    active_threats.push_back(std::make_unique<RadarThreat>(x, y, z, r0, max_range, diff_k, mask_thresh));
}
void FieldGenerator::addIR(double x, double y, double z, double max_range, double k_ir) {
    active_threats.push_back(std::make_unique<IRThreat>(x, y, z, max_range, k_ir));
}
void FieldGenerator::addAcoustic(double x, double y, double z, double max_range, double k_ac) {
    active_threats.push_back(std::make_unique<AcousticThreat>(x, y, z, max_range, k_ac));
}
void FieldGenerator::addVisual(double x, double y, double z, double max_range, double k_vis) {
    active_threats.push_back(std::make_unique<VisualThreat>(x, y, z, max_range, k_vis));
}
void FieldGenerator::addNoFlyZone(double x, double y, double radius) {
    nfzs.push_back({x, y, radius * radius});
}

void FieldGenerator::calculateChunk(int start_y, int end_y, double drone_z_m, const DroneState& drone, const EnvState& env) {
    double v_ratio = (drone.max_speed > 0.0) ? std::clamp(drone.speed / drone.max_speed, 0.0, 1.0) : 0.0;
    
    DynamicSignature dyn_sig;
    dyn_sig.v_ratio = v_ratio;
    dyn_sig.v_sq = v_ratio * v_ratio;
    dyn_sig.v_cubed = dyn_sig.v_sq * v_ratio;
    
    dyn_sig.i_dynamic = drone.i_base * (1.0 + drone.c_drag * dyn_sig.v_cubed);
    dyn_sig.s_dynamic = drone.s_idle * (1.0 + drone.c_aero * dyn_sig.v_sq);

    double wind_ratio = std::clamp(env.wind_speed / drone.max_wind_tolerance, 0.0, 1.0);
    double global_wind_risk = wind_ratio * wind_ratio; 

    for (int y = start_y; y < end_y; ++y) {
        for (int x = 0; x < width; ++x) {
            int idx = y * width + x;
            
            double target_x_m = x * CELL_SIZE;
            double target_y_m = y * CELL_SIZE;

            // 1. Evaluate Hard Constraints (NFZ Masking)
            bool inside_nfz = false;
            for (const auto& zone : nfzs) {
                double dx = target_x_m - zone.x_m;
                double dy = target_y_m - zone.y_m;
                if ((dx * dx) + (dy * dy) <= zone.radius_sq_m) {
                    inside_nfz = true;
                    break;
                }
            }
            nfz_mask[idx] = inside_nfz;

            // 2. Evaluate Base Wind Field
            wind_field[idx] = global_wind_risk;

            // 3. Independent Field Propagators
            double esc_radar = 1.0;
            double esc_ir = 1.0;
            double esc_acoustic = 1.0;
            double esc_visual = 1.0;

            for (const auto& threat : active_threats) {
                double risk = threat->calculateRisk(target_x_m, target_y_m, drone_z_m, drone, dyn_sig, env, terrain_grid, width, height, CELL_SIZE);
                
                switch (threat->getType()) {
                    case ThreatType::Radar:    esc_radar *= (1.0 - risk); break;
                    case ThreatType::IR:       esc_ir *= (1.0 - risk); break;
                    case ThreatType::Acoustic: esc_acoustic *= (1.0 - risk); break;
                    case ThreatType::Visual:   esc_visual *= (1.0 - risk); break;
                }
            }

            radar_field[idx]    = 1.0 - esc_radar;
            ir_field[idx]       = 1.0 - esc_ir;
            acoustic_field[idx] = 1.0 - esc_acoustic;
            visual_field[idx]   = 1.0 - esc_visual;
        }
    }
}

void FieldGenerator::generateFieldsAtZ(double drone_z_m, const DroneState& drone, const EnvState& env, int num_threads) {
    std::vector<std::thread> threads;
    int rows_per_thread = height / num_threads;
    int current_y = 0;

    for (int i = 0; i < num_threads; ++i) {
        int end_y = (i == num_threads - 1) ? height : current_y + rows_per_thread;
        threads.emplace_back(&FieldGenerator::calculateChunk, this, current_y, end_y, drone_z_m, std::ref(drone), std::ref(env));
        current_y = end_y;
    }
    for (auto& t : threads) {
        if (t.joinable()) t.join();
    }
}

void FieldGenerator::exportFieldsToCSV(const std::string& prefix) const {
    auto writeField = [&](const std::vector<double>& field, const std::string& name) {
        std::ofstream file(prefix + "_" + name + ".csv");
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                file << std::fixed << std::setprecision(5) << field[y * width + x];
                if (x < width - 1) file << ",";
            }
            file << "\n";
        }
        file.close();
    };

    writeField(radar_field, "radar");
    writeField(ir_field, "ir");
    writeField(acoustic_field, "acoustic");
    writeField(visual_field, "visual");
    writeField(wind_field, "wind");

    std::ofstream mask_file(prefix + "_nfz_mask.csv");
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            mask_file << (nfz_mask[y * width + x] ? "1" : "0");
            if (x < width - 1) mask_file << ",";
        }
        mask_file << "\n";
    }
    mask_file.close();

    std::cout << "[Ejection] Separated Field CSVs successfully generated with prefix: " << prefix << "\n";
}