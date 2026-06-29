#pragma once

#include "States.h"
#include "Threats.h"
#include "Config.h"

#include <vector>
#include <thread>

class FieldGenerator
{
private:

    TerrainData terrain;
    std::vector<SensorSite> sensors;
    SimulationConfig config;
    std::vector<NFZTriangle> nfzs;
    std::vector<double> final_cost;
    std::vector<bool> nfz_mask;

    void buildNFZMask();

    bool pointInsideTriangle(
        int px,
        int py,
        const NFZTriangle& t) const;

    void calculateChunk(
        int start_y,
        int end_y,
        const DroneState& drone,
        const EnvState& env);

public:
    FieldGenerator(
        const TerrainData& terrain,
        const std::vector<SensorSite>& sensors,
        const std::vector<NFZTriangle>& nfzs);

    void generate(
        const DroneState& drone,
        const EnvState& env,
        int num_threads);

    void exportCostMatrix(
        const std::string& filename) const;

    const std::vector<double>&
    getCostMatrix() const;
};