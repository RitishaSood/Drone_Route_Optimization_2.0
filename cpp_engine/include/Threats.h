#pragma once

#include "States.h"
#include "FastMath.h"
#include "Config.h"
#include <cmath>
#include <algorithm>
#include <vector>

// Helper function for C++17 clamp if not available
template<typename T>
inline T clamp(T value, T min_val, T max_val)
{
    if(value < min_val) return min_val;
    if(value > max_val) return max_val;
    return value;
}

class Threat
{
protected:

    SensorSite sensor;

    static constexpr double XY_SCALE_M = 1000.0;
    static constexpr double Z_SCALE_M  = 100.0;

protected:

    double getDistanceSq(
        int tx,
        int ty,
        int tz) const
    {
        double dx =
            (tx - sensor.x) * XY_SCALE_M;

        double dy =
            (ty - sensor.y) * XY_SCALE_M;

        double dz =
            (tz - sensor.z) * Z_SCALE_M;

        return
            dx * dx +
            dy * dy +
            dz * dz;
    }

    double getTerrainClearance(
        int tx,
        int ty,
        int tz,
        const TerrainData& terrain) const
    {
        int steps =
            std::max(
                15,
                static_cast<int>(
                    std::ceil(
                        std::hypot(
                            tx - sensor.x,
                            ty - sensor.y))) * 2);

        double max_clearance = -1e9;

        for(int i = 1; i < steps; ++i)
        {
            double t =
                static_cast<double>(i) /
                steps;

            double sx =
                sensor.x +
                t * (tx - sensor.x);

            double sy =
                sensor.y +
                t * (ty - sensor.y);

            double sz =
                sensor.z +
                t * (tz - sensor.z);

            int cx =
                clamp(
                    static_cast<int>(sx),
                    0,
                    terrain.width - 1);

            int cy =
                clamp(
                    static_cast<int>(sy),
                    0,
                    terrain.height - 1);

            double terrain_z =
                terrain.heightAt(cx, cy);

            double clearance =
                (terrain_z - sz) *
                Z_SCALE_M;

            max_clearance =
                std::max(
                    max_clearance,
                    clearance);
        }

        return max_clearance;
    }

    double getSoftTerrainFactor(double clearance) const
    {
        if(clearance <= 0.0)
        {
            return 1.0;
        }

        return FastMath::get().exp_neg(
            0.02 * clearance);
    }

public:

    explicit Threat(
        const SensorSite& s)
        :
        sensor(s)
    {
    }

    virtual ~Threat() = default;

    virtual double calculateRisk(
        int target_x,
        int target_y,
        int target_z,
        const DroneState& drone,
        const DynamicSignature& dyn_sig,
        const EnvState& env,
        const TerrainData& terrain) const = 0;
};


// =====================================================
// RADAR
// =====================================================

class RadarThreat : public Threat
{
public:

    explicit RadarThreat(
        const SensorSite& s)
        :
        Threat(s)
    {
    }

    double calculateRisk(
        int tx,
        int ty,
        int tz,
        const DroneState& drone,
        const DynamicSignature& dyn_sig,
        const EnvState& env,
        const TerrainData& terrain) const override
    {
        double dist_sq =
            getDistanceSq(
                tx,
                ty,
                tz);

        if(dist_sq <= 0.0)
            return 1.0;

        if(dist_sq >
           sensor.max_range *
           sensor.max_range)
            return 0.0;

        double dx =
            (tx - sensor.x) *
            XY_SCALE_M;

        double dy =
            (ty - sensor.y) *
            XY_SCALE_M;

        double dz =
            (tz - sensor.z) *
            Z_SCALE_M;

        double d_xy =
            std::sqrt(
                dx * dx +
                dy * dy);

        double d_s =
            std::sqrt(dist_sq);

        double los_angle =
            std::atan2(
                dy,
                dx);

        double theta =
            drone.heading -
            los_angle;

        double sigma_theta =
            drone.sigma_front +
            (
                drone.sigma_side -
                drone.sigma_front
            ) *
            std::abs(
                std::sin(theta));

        double r_eff =
            sensor.R0 *
            std::sqrt(
                std::sqrt(
                    sigma_theta /
                    drone.sigma_avg));

        double r_ratio =
            d_s / r_eff;

        double r4 =
            r_ratio *
            r_ratio *
            r_ratio *
            r_ratio;

        double phi = (d_xy == 0)
        ? Config::PI / 2.0
        : std::atan2(dz, d_xy);

        double p_radar =
            (
                1.0 /
                (1.0 + r4)
            ) *
            (
                std::cos(phi) *
                std::cos(phi)
            );

        double clearance =
            getTerrainClearance(
                tx,
                ty,
                tz,
                terrain);

        double terrain_factor;

        if(clearance <= 0.0)
        {
            terrain_factor = 1.0;
        }
        else
        {
            terrain_factor =
                FastMath::get().exp_neg(
                    sensor.diffraction_k *
                    clearance);
        }

        return clamp(
            terrain_factor *
            p_radar,
            0.0,
            1.0);
    }
};


// =====================================================
// IR
// =====================================================

class IRThreat : public Threat
{
public:

    explicit IRThreat(
        const SensorSite& s)
        :
        Threat(s)
    {
    }

    double calculateRisk(
        int tx,
        int ty,
        int tz,
        const DroneState& drone,
        const DynamicSignature& dyn_sig,
        const EnvState& env,
        const TerrainData& terrain) const override
    {
        double dist_sq =
            getDistanceSq(
                tx,
                ty,
                tz);

        if(dist_sq <= 0.0)
            return 1.0;

        if(dist_sq >
           sensor.max_range *
           sensor.max_range)
            return 0.0;

        double clearance =
            getTerrainClearance(
                tx,
                ty,
                tz,
                terrain);

        double terrain_factor =
            getSoftTerrainFactor(clearance);

        double d =
            std::sqrt(dist_sq);

        double d_km =
            d / 1000.0;

        double extinction =
            FastMath::get().exp_neg(
                env.ir_gamma *
                d_km);

        double E_received =
            (
                dyn_sig.i_dynamic *
                extinction
            ) /
            dist_sq;

        double p_ir =
            1.0 -
            FastMath::get().exp_neg(
                sensor.K_ir *
                env.ir_c_bg *
                E_received);

        return clamp(
            terrain_factor *
            p_ir,
            0.0,
            1.0);
    }
};


// =====================================================
// ACOUSTIC
// =====================================================

class AcousticThreat : public Threat
{
public:

    explicit AcousticThreat(
        const SensorSite& s)
        :
        Threat(s)
    {
    }

    double calculateRisk(
        int tx,
        int ty,
        int tz,
        const DroneState& drone,
        const DynamicSignature& dyn_sig,
        const EnvState& env,
        const TerrainData& terrain) const override
    {
        double dist_sq =
            getDistanceSq(
                tx,
                ty,
                tz);

        if(dist_sq <= 0.0)
            return 1.0;

        if(dist_sq >
           sensor.max_range *
           sensor.max_range)
            return 0.0;

        double snr =
            dyn_sig.s_dynamic /
            (
                dist_sq *
                env.n_bg
            );

        double p_ac =
            1.0 -
            FastMath::get().exp_neg(
                sensor.K_ac *
                snr);

        return clamp(
            p_ac,
            0.0,
            1.0);
    }
};


// =====================================================
// VISUAL
// =====================================================

class VisualThreat : public Threat
{
public:

    explicit VisualThreat(
        const SensorSite& s)
        :
        Threat(s)
    {
    }

    double calculateRisk(
        int tx,
        int ty,
        int tz,
        const DroneState& drone,
        const DynamicSignature& dyn_sig,
        const EnvState& env,
        const TerrainData& terrain) const override
    {
        double dist_sq =
            getDistanceSq(
                tx,
                ty,
                tz);

        if(dist_sq <= 0.0)
            return 1.0;

        if(dist_sq >
           sensor.max_range *
           sensor.max_range)
            return 0.0;

        double clearance =
            getTerrainClearance(
                tx,
                ty,
                tz,
                terrain);

        double terrain_factor =
            getSoftTerrainFactor(clearance);

        double optic_factor =
            (
                drone.a_vis *
                env.visual_lux *
                env.visual_c_bg
            ) /
            dist_sq;

        double p_vis =
            1.0 -
            FastMath::get().exp_neg(
                sensor.K_vis *
                optic_factor);

        return clamp(
            terrain_factor *
            p_vis,
            0.0,
            1.0);
    }
};