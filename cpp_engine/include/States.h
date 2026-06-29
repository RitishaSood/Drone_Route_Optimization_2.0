#pragma once

#include <string>
#include <vector>
#include <cstdint>

// =====================================================
// THREAT TYPES
// =====================================================

enum class ThreatType
{
    Radar,
    IR,
    Acoustic,
    Visual,
    NFZ
};

// =====================================================
// SENSOR TYPES
// =====================================================

enum class SensorType
{
    Radar,
    Infrared,
    Acoustic,
    Visual,
    NFZ
};

// =====================================================
// TERRAIN TYPES
// =====================================================

enum class TerrainType : uint8_t
{
    Water    = 0,
    Plain    = 1,
    Forest   = 2,
    Hill     = 3,
    Valley   = 4,
    Mountain = 5
};

// =====================================================
// FAST INDEX HELPERS
// =====================================================

inline int idx2D(
    int x,
    int y,
    int width)
{
    return y * width + x;
}

inline int idx3D(
    int x,
    int y,
    int z,
    int width,
    int height)
{
    return z * width * height +
           y * width +
           x;
}

// =====================================================
// DYNAMIC SIGNATURE
// =====================================================

struct DynamicSignature
{
    double v_ratio;
    double v_sq;
    double v_cubed;

    double i_dynamic;
    double s_dynamic;
};

// =====================================================
// DRONE
// =====================================================

struct DroneState
{
    std::string name;
    std::string uav_class;
    std::string propulsion_class;

    double speed;
    double heading;

    double max_speed;
    double ceiling;
    double mtow;

    double wingspan;
    double length;

    double wing_area;
    double stall_speed;
    double max_wind_tolerance;

    double sigma_front;
    double sigma_side;
    double sigma_avg;

    double i_base;
    double c_drag;

    double s_idle;
    double c_aero;

    double a_vis;

    double failure_probability;
};

// =====================================================
// ENVIRONMENT
// =====================================================

struct EnvState
{
    double air_density;
    double wind_speed;

    double ir_gamma;
    double ir_c_bg;

    double n_bg;

    double visual_lux;
    double visual_c_bg;
};

// =====================================================
// TERRAIN DATA
// =====================================================

struct TerrainData
{
    int width;
    int height;

    std::vector<double> elevation;
    std::vector<uint8_t> terrain_type;

    inline int rowForWorldY(int y) const
    {
        return height - 1 - y;
    }

    inline double heightAt(int x,int y) const
    {
        return elevation[rowForWorldY(y) * width + x];
    }

    inline uint8_t typeAt(int x,int y) const
    {
        return terrain_type[rowForWorldY(y) * width + x];
    }
};

// =====================================================
// SENSOR SITE
// =====================================================

struct SensorSite
{
    int id;

    SensorType type;

    std::string label;

    int x;
    int y;
    int z;

    uint8_t terrain_type;

    double max_range;

    // Radar only
    double R0;
    double diffraction_k;
    double deep_mask_threshold;

    // IR only
    double K_ir;

    // Acoustic only
    double K_ac;

    // Visual only
    double K_vis;
};

// =====================================================
// NFZ TRIANGLE
// =====================================================

struct NFZTriangle
{
    int id;

    int x1;
    int y1;

    int x2;
    int y2;

    int x3;
    int y3;
};

struct SensorParameters
{
    double max_range;

    double k1;
    double k2;
    double k3;
    double k4;
};

struct SimulationConfig
{
    int simulation_z;

    bool use_radar;
    bool use_ir;
    bool use_acoustic;
    bool use_visual;

    bool enable_nfz;

    bool custom_weights;

    double radar_weight;
    double ir_weight;
    double acoustic_weight;
    double visual_weight;
};

