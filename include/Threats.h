#pragma once
#include "States.h"
#include "FastMath.h"
#include <cmath>
#include <algorithm>
#include <vector>

// --- BASE THREAT CLASS ---
class Threat {
protected:
    double x, y, z;          // STRICTLY IN METERS
    double max_range_sq;     // STRICTLY IN METERS
    ThreatType type;

    // Ray Marching for accurate Line-of-Sight Masking
    double getTerrainClearance(double target_x_m, double target_y_m, double target_z_m, 
                               const std::vector<double>& terrain, int grid_w, int grid_h, double cell_size) const {
        int steps = 15;
        double max_clearance = -99999.0;
        
        for (int i = 1; i < steps; ++i) {
            double t = (double)i / steps;
            double sample_x_m = x + t * (target_x_m - x);
            double sample_y_m = y + t * (target_y_m - y);
            double sample_z_m = z + t * (target_z_m - z);

            int cx = std::clamp((int)(sample_x_m / cell_size), 0, grid_w - 1);
            int cy = std::clamp((int)(sample_y_m / cell_size), 0, grid_h - 1);

            double h_terrain = terrain[cy * grid_w + cx];
            double clearance = h_terrain - sample_z_m;
            
            if (clearance > max_clearance) {
                max_clearance = clearance;
            }
        }
        return max_clearance;
    }

public:
    Threat(ThreatType t, double x, double y, double z, double max_range) 
        : type(t), x(x), y(y), z(z), max_range_sq(max_range * max_range) {}
    virtual ~Threat() = default;

    ThreatType getType() const { return type; }

    virtual double calculateRisk(double target_x_m, double target_y_m, double target_z_m, 
                                 const DroneState& drone, const DynamicSignature& dyn_sig, const EnvState& env, 
                                 const std::vector<double>& terrain, int grid_w, int grid_h, double cell_size) = 0;
    
    double getDistanceSq(double tx, double ty, double tz) const {
        double dx = tx - x; double dy = ty - y; double dz = tz - z;
        return (dx * dx) + (dy * dy) + (dz * dz);
    }
};

// --- RADAR THREAT ---
class RadarThreat : public Threat {
    double R0; 
    double diffraction_k;       
    double deep_mask_threshold; 

public:
    RadarThreat(double x, double y, double z, double r0, double max_range, double diff_k, double mask_thresh) 
        : Threat(ThreatType::Radar, x, y, z, max_range), R0(r0), diffraction_k(diff_k), deep_mask_threshold(mask_thresh) {}

    double calculateRisk(double target_x_m, double target_y_m, double target_z_m, 
                         const DroneState& drone, const DynamicSignature& dyn_sig, const EnvState& env, 
                         const std::vector<double>& terrain, int grid_w, int grid_h, double cell_size) override {
        
        double dist_sq = getDistanceSq(target_x_m, target_y_m, target_z_m);
        if (dist_sq > max_range_sq) return 0.0; 
        if (dist_sq == 0) return 1.0;
        
        double dx = target_x_m - x; double dy = target_y_m - y; double dz = target_z_m - z; 
        double d_xy_sq = (dx * dx) + (dy * dy);
        double d_xy = std::sqrt(d_xy_sq);
        double d_s = std::sqrt(dist_sq); 

        double radar_los_angle = std::atan2(dy, dx);
        double theta = drone.heading - radar_los_angle;
        double sigma_theta = drone.sigma_front + (drone.sigma_side - drone.sigma_front) * std::abs(std::sin(theta));
        double r_eff = R0 * std::sqrt(std::sqrt(sigma_theta / drone.sigma_avg));

        double r_ratio = d_s / r_eff;
        double r_quart = r_ratio * r_ratio * r_ratio * r_ratio; 
        
        double phi = (d_xy == 0) ? M_PI/2.0 : std::atan2(dz, d_xy); 
        double cos_phi = std::cos(phi);
        double p_radar = (1.0 / (1.0 + r_quart)) * (cos_phi * cos_phi);

        double clearance = getTerrainClearance(target_x_m, target_y_m, target_z_m, terrain, grid_w, grid_h, cell_size);
        double V_terrain = (clearance <= 0.0) ? 1.0 : (clearance > deep_mask_threshold) ? 0.0 : FastMath::get().exp_neg(diffraction_k * clearance);

        return std::clamp(V_terrain * p_radar, 0.0, 1.0);
    }
};

// --- IR THREAT ---
class IRThreat : public Threat {
    double K_ir; 
public:
    IRThreat(double x, double y, double z, double max_range, double k_ir) 
        : Threat(ThreatType::IR, x, y, z, max_range), K_ir(k_ir) {}

    double calculateRisk(double target_x_m, double target_y_m, double target_z_m, 
                         const DroneState& drone, const DynamicSignature& dyn_sig, const EnvState& env, 
                         const std::vector<double>& terrain, int grid_w, int grid_h, double cell_size) override {
        double dist_sq = getDistanceSq(target_x_m, target_y_m, target_z_m);
        if (dist_sq == 0) return 1.0; 
        if (dist_sq > max_range_sq) return 0.0;
        
        double clearance = getTerrainClearance(target_x_m, target_y_m, target_z_m, terrain, grid_w, grid_h, cell_size);
        if (clearance > 0.0) return 0.0; // Hard mask for IR
        
        double d_s = std::sqrt(dist_sq);
        double extinction = FastMath::get().exp_neg(env.ir_gamma * d_s);
        double E_received = (dyn_sig.i_dynamic * extinction) / dist_sq;

        double p_ir = 1.0 - FastMath::get().exp_neg(K_ir * env.ir_c_bg * E_received);
        return std::clamp(p_ir, 0.0, 1.0);
    }
};

// --- ACOUSTIC THREAT ---
class AcousticThreat : public Threat {
    double K_ac;
public:
    AcousticThreat(double x, double y, double z, double max_range, double k_ac) 
        : Threat(ThreatType::Acoustic, x, y, z, max_range), K_ac(k_ac) {}

    double calculateRisk(double target_x_m, double target_y_m, double target_z_m, 
                         const DroneState& drone, const DynamicSignature& dyn_sig, const EnvState& env, 
                         const std::vector<double>& terrain, int grid_w, int grid_h, double cell_size) override {
        double dist_sq = getDistanceSq(target_x_m, target_y_m, target_z_m);
        if (dist_sq == 0) return 1.0;
        if (dist_sq > max_range_sq) return 0.0;

        double SNR = dyn_sig.s_dynamic / (dist_sq * env.n_bg);
        double p_ac = 1.0 - FastMath::get().exp_neg(K_ac * SNR);
        return std::clamp(p_ac, 0.0, 1.0);
    }
};

// --- VISUAL THREAT ---
class VisualThreat : public Threat {
    double K_vis; 
public:
    VisualThreat(double x, double y, double z, double max_range, double k_vis) 
        : Threat(ThreatType::Visual, x, y, z, max_range), K_vis(k_vis) {}

    double calculateRisk(double target_x_m, double target_y_m, double target_z_m, 
                         const DroneState& drone, const DynamicSignature& dyn_sig, const EnvState& env, 
                         const std::vector<double>& terrain, int grid_w, int grid_h, double cell_size) override {
        double dist_sq = getDistanceSq(target_x_m, target_y_m, target_z_m);
        if (dist_sq == 0) return 1.0;
        if (dist_sq > max_range_sq) return 0.0;

        double clearance = getTerrainClearance(target_x_m, target_y_m, target_z_m, terrain, grid_w, grid_h, cell_size);
        if (clearance > 0.0) return 0.0; // Hard mask for Visual

        double optic_factor = (drone.a_vis * env.visual_lux * env.visual_c_bg) / dist_sq;
        double p_vis = 1.0 - FastMath::get().exp_neg(K_vis * optic_factor);
        return std::clamp(p_vis, 0.0, 1.0);
    }
};