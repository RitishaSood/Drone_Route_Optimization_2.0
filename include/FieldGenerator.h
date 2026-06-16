#pragma once
#include <vector>
#include <memory>
#include <string>
#include "States.h"
#include "Threats.h"

struct NoFlyZone {
    double x_m, y_m;
    double radius_sq_m;
};

class FieldGenerator {
private:
    int width;
    int height;
    
    // Physical scale linkage
    static constexpr double CELL_SIZE = 100.0; // 1 cell = 100 meters

    std::vector<double> terrain_grid; 
    
    // Isolated Probability Fields
    std::vector<double> radar_field;
    std::vector<double> ir_field;
    std::vector<double> acoustic_field;
    std::vector<double> visual_field;
    std::vector<double> wind_field;
    
    // Constraint Masks
    std::vector<bool> nfz_mask;

    std::vector<std::unique_ptr<Threat>> active_threats;
    std::vector<NoFlyZone> nfzs;

    void calculateChunk(int start_y, int end_y, double drone_z_m, const DroneState& drone, const EnvState& env);

public:
    FieldGenerator(int w = 100, int h = 100);

    void setTerrain(const std::vector<double>& terrain);

    void addRadar(double x_m, double y_m, double z_m, double r0, double max_range, double diff_k, double mask_thresh);
    void addIR(double x_m, double y_m, double z_m, double max_range, double k_ir);
    void addAcoustic(double x_m, double y_m, double z_m, double max_range, double k_ac);
    void addVisual(double x_m, double y_m, double z_m, double max_range, double k_vis);
    void addNoFlyZone(double x_m, double y_m, double radius_m);

    void generateFieldsAtZ(double drone_z_m, const DroneState& drone, const EnvState& env, int num_threads = 4);
    
    void exportFieldsToCSV(const std::string& prefix) const;
};