#include <iostream>
#include <thread>
#include <string>
#include <vector>
#include "../include/States.h"
#include "../include/FieldGenerator.h"
#include "../include/DroneDatabase.h"

int main() {
    std::cout << "=== UAV Independent Probability Field Generator ===\n\n";

    // 1. DATA INGESTION
    DroneDatabase db;
    std::string active_drone_name = "MQ-9 Reaper";
    
    double static_cruise_speed = 130.0; 
    double static_heading = 0.0;       
    double static_flight_altitude = 500.0; // 500 meters altitude
    
    std::cout << "[Ingestion] Fetching profile for: " << active_drone_name << "\n";
    DroneState active_drone = db.ingestAndSynthesize(active_drone_name, static_cruise_speed, static_heading);

    EnvState active_env;
    active_env.air_density = 1.225; 
    active_env.wind_speed = 8.0;    
    active_env.ir_gamma = 0.05;      
    active_env.ir_c_bg = 0.8;        
    active_env.n_bg = 4.0;           
    active_env.visual_lux = 0.5;     
    active_env.visual_c_bg = 0.2;    

    // 100x100 grid. At CELL_SIZE=100m, this is a 10km x 10km map.
    int grid_width = 100;
    int grid_height = 100;
    FieldGenerator field_gen(grid_width, grid_height);

    // Mock Terrain Injection (Flat at 0m, with a 300m mountain in the center)
    std::vector<double> mock_terrain(grid_width * grid_height, 0.0);
    for(int y = 40; y < 60; ++y) {
        for(int x = 40; x < 60; ++x) {
            mock_terrain[y * grid_width + x] = 300.0;
        }
    }
    field_gen.setTerrain(mock_terrain);

    // Coordinates are now explicitly in METERS. 
    field_gen.addRadar(5000.0, 5000.0, 0.0, 4000.0, 16000.0, 0.15, 20.0);   
    field_gen.addIR(5000.0, 5000.0, 0.0, 10000.0, 1000.0);     
    
    // NFZ at 3km, 3km with an 800m radius
    field_gen.addNoFlyZone(3000.0, 3000.0, 800.0); 

    // 2. COMPUTATION
    unsigned int hardware_concurrency = std::thread::hardware_concurrency();
    int active_workers = (hardware_concurrency > 0) ? hardware_concurrency : 4;

    std::cout << "\n[Compute] Generating Independent Fields (" << grid_width << "x" << grid_height << ")...\n";
    std::cout << "          -> Utilizing " << active_workers << " parallel threads.\n";
    
    field_gen.generateFieldsAtZ(static_flight_altitude, active_drone, active_env, active_workers);

    // 3. DATA EJECTION PIPELINE
    std::cout << "\n[Ejection] Formatting fields to CSVs...\n";
    
    std::string prefix = "fields_" + active_drone.uav_class;
    field_gen.exportFieldsToCSV(prefix);

    std::cout << "Pipeline completed successfully.\n";

    return 0;
}