#pragma once
#include "States.h"
#include <unordered_map>
#include <string>
#include <stdexcept>

class DroneDatabase {
private:
    std::unordered_map<std::string, DroneState> database;

public:
    DroneDatabase() {
        // Enclose strings in quotes to compile correctly
        database["IAI Heron"] = { "IAI Heron", "MALE", "ICE Piston",0.0,0.0,57.0,10000.0,1150.0,16.6,8.5,24.80,22.32,45.0,0.50,2.00,1.25,150.0,0.15,80.0,0.25,21.17,0.001};
        database["Heron TP"] = { "Heron TP", "HALE", "Turboprop",0.0,0.0,113.0,13700.0,5670.0,26.0,14.0,60.84,34.68,45.0,0.50,2.00,1.25,400.0,0.30,120.0,0.40,54.60,0.001};
        database["Rustom-2 (TAPAS BH-201)"] = { "Rustom-2 (TAPAS BH-201)", "MALE", "ICE Piston",0.0,0.0,62.0,10600.0,1800.0,20.6,9.5,38.19,25.00,45.0,0.50,2.00,1.25,150.0,0.15,80.0,0.25,29.36,0.05};
        database["Switch UAV"] = { "Switch UAV", "Tactical", "Electric Tactical",0.0,0.0,22.0,6000.0,6.5,2.4,1.5,0.86,9.04,8.82,0.02,0.08,0.05,10.0,0.02,15.0,0.04,1.44,0.001};
        database["MQ-9 Reaper"] = { "MQ-9 Reaper", "MALE", "Turboprop",0.0,0.0,134.0,15240.0,4760.0,20.0,11.0,36.00,41.48,45.0,0.50,2.00,1.25,400.0,0.30,120.0,0.40,33.00,0.001};
        database["Swarm Drones"] = { "Swarm Drones", "Swarm", "Electric Tactical",0.0,0.0,20.0,3000.0,5.0,1.2,1.0,0.22,10.91,8.35,0.02,0.08,0.05,10.0,0.02,15.0,0.04,0.18,0.05};
        database["DRDO Ghatak"] = { "DRDO Ghatak", "Stealth UCAV", "Jet UCAV",0.0,0.0,260.0,12000.0,8000.0,12.0,8.0,21.60,77.04,45.0,0.01,0.05,0.03,1200.0,0.60,250.0,0.70,14.40,0.05};
        database["Searcher"] = { "Searcher", "Tactical", "ICE Piston",0.0,0.0,55.0,6100.0,436.0,8.6,5.8,11.09,25.27,36.32,0.02,0.08,0.05,150.0,0.15,80.0,0.25,19.95,0.001};
        database["Harpy"] = { "Harpy", "Loitering Munition", "ICE Piston",0.0,0.0,116.0,4500.0,135.0,2.1,2.7,0.66,42.47,22.44,0.03,0.15,0.09,150.0,0.15,80.0,0.25,0.85,0.001};
        database["Rooster"] = { "Rooster", "Electric Nano", "Electric Nano",0.0,0.0,10.0,1000.0,1.2,0.4,0.4,0.024,18.27,6.64,0.005,0.02,0.0125,2.0,0.005,5.0,0.01,0.064,0.05};
        database["Black Hornet"] = { "Black Hornet", "Electric Nano", "Electric Nano",0.0,0.0,6.0,100.0,0.033,0.12,0.16,0.00216,15.68,5.27,0.005,0.02,0.0125,2.0,0.005,5.0,0.01,0.00768,0.001};
        database["Nagastra-1"] = { "Nagastra-1", "Loitering Munition", "Electric Tactical",0.0,0.0,25.0,4500.0,9.0,2.0,1.5,0.60,12.81,9.50,0.03,0.15,0.09,10.0,0.02,15.0,0.04,0.45,0.001};
        database["Netra UAV"] = { "Netra UAV", "Tactical", "Electric Nano",0.0,0.0,8.0,3000.0,1.5,0.9,0.9,0.12,14.14,6.84,0.02,0.08,0.05,2.0,0.005,5.0,0.01,0.324,0.001};
    }

    DroneState getDrone(const std::string& name, double speed, double heading) const {
        auto it = database.find(name);
        if(it == database.end()) {
            throw std::runtime_error("Drone " + name + " not found.");
        }
        const DroneState& original = it->second;
        DroneState drone = original; 
        
        drone.speed = speed;
        drone.heading = heading;
        
        return drone;
    }
};
