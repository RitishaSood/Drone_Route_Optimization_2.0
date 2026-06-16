#pragma once
#include "States.h"
#include <string>
#include <vector>
#include <stdexcept>
#include <cmath>
#include <algorithm>

class DroneDatabase {
private:
    struct RawUAVPreset {
        std::string name;
        std::string uav_class;         
        std::string propulsion;        
        double wingspan;               // m
        double length;                 // m
        double max_speed;              // m/s
        double ceiling;                // m
        double mtow;                   // kg
        std::string maturity;          
    };

    std::vector<RawUAVPreset> database;

public:
    DroneDatabase() {
        database.push_back({"IAI Heron", "MALE", "ICE Piston", 16.6, 8.5, 57.0, 10000.0, 1150.0, "Mature"});
        database.push_back({"Heron TP", "HALE", "Turboprop", 26.0, 14.0, 113.0, 13700.0, 5670.0, "Mature"});
        database.push_back({"Rustom-2 (TAPAS BH-201)", "MALE", "ICE Piston", 20.6, 9.5, 62.0, 10600.0, 1800.0, "Prototype"});
        database.push_back({"Switch UAV", "Tactical", "Electric Tactical", 2.4, 1.5, 22.0, 6000.0, 6.5, "Mature"});
        database.push_back({"MQ-9 Reaper", "MALE", "Turboprop", 20.0, 11.0, 134.0, 15240.0, 4760.0, "Mature"});
        database.push_back({"Swarm Drones", "Swarm", "Electric Tactical", 1.2, 1.0, 20.0, 3000.0, 5.0, "Prototype"});
        database.push_back({"DRDO Ghatak", "Stealth UCAV", "Jet UCAV", 12.0, 8.0, 260.0, 12000.0, 8000.0, "Prototype"});
        database.push_back({"Netra UAV", "Tactical", "Electric Nano", 0.9, 0.9, 8.0, 3000.0, 1.5, "Mature"});
        database.push_back({"Harpy", "Loitering Munition", "ICE Piston", 2.1, 2.7, 116.0, 4500.0, 135.0, "Mature"});
        database.push_back({"Searcher", "Tactical", "ICE Piston", 8.6, 5.8, 55.0, 6100.0, 436.0, "Mature"});
        database.push_back({"Rooster", "Electric Nano", "Electric Nano", 0.4, 0.4, 10.0, 1000.0, 1.2, "Prototype"});
        database.push_back({"Black Hornet", "Electric Nano", "Electric Nano", 0.12, 0.16, 6.0, 100.0, 0.033, "Mature"});
        database.push_back({"Nagastra-1", "Loitering Munition", "Electric Tactical", 2.0, 1.5, 25.0, 4500.0, 9.0, "Mature"});
        database.push_back({"DRDO Netra", "Tactical", "Electric Nano", 0.9, 0.9, 8.0, 3000.0, 1.5, "Mature"});
    }

    DroneState ingestAndSynthesize(const std::string& name, double current_speed, double heading) {
        for (const auto& raw : database) {
            if (raw.name == name) {
                DroneState synthesized;
                synthesized.name = raw.name;
                synthesized.uav_class = raw.uav_class;
                synthesized.propulsion_class = raw.propulsion;
                synthesized.speed = current_speed;
                synthesized.heading = heading;
                synthesized.max_speed = raw.max_speed;
                synthesized.ceiling = raw.ceiling;
                synthesized.mtow = raw.mtow;
                synthesized.wingspan = raw.wingspan;
                synthesized.length = raw.length;

                // 1. RADAR SURROGATE COEFFICIENTS
                if (raw.uav_class == "Electric Nano") {
                    synthesized.sigma_front = 0.005; synthesized.sigma_side = 0.02;
                } else if (raw.uav_class == "Tactical") {
                    synthesized.sigma_front = 0.02;  synthesized.sigma_side = 0.08;
                } else if (raw.uav_class == "MALE" || raw.uav_class == "HALE") {
                    synthesized.sigma_front = 0.5;   synthesized.sigma_side = 2.0;
                } else if (raw.uav_class == "Stealth UCAV") {
                    synthesized.sigma_front = 0.01;  synthesized.sigma_side = 0.05;
                } else if (raw.uav_class == "Loitering Munition") {
                    synthesized.sigma_front = 0.03;  synthesized.sigma_side = 0.15;
                } else if (raw.uav_class == "Swarm") {
                    synthesized.sigma_front = 0.02;  synthesized.sigma_side = 0.08; 
                } else {
                    synthesized.sigma_front = 0.1;   synthesized.sigma_side = 0.4;
                }
                synthesized.sigma_avg = (synthesized.sigma_front + synthesized.sigma_side) / 2.0;

                // 2. THERMAL (IR) SURROGATE COEFFICIENTS
                if (raw.propulsion == "Electric Nano") {
                    synthesized.i_base = 2.0;    synthesized.c_drag = 0.005;
                } else if (raw.propulsion == "Electric Tactical") {
                    synthesized.i_base = 10.0;   synthesized.c_drag = 0.02;
                } else if (raw.propulsion == "ICE Piston") {
                    synthesized.i_base = 150.0;  synthesized.c_drag = 0.15;
                } else if (raw.propulsion == "Turboprop") {
                    synthesized.i_base = 400.0;  synthesized.c_drag = 0.3;
                } else if (raw.propulsion == "Jet UCAV") {
                    synthesized.i_base = 1200.0; synthesized.c_drag = 0.6;
                } else {
                    synthesized.i_base = 50.0;   synthesized.c_drag = 0.1;
                }

                // 3. ACOUSTIC SURROGATE COEFFICIENTS
                if (raw.propulsion == "Electric Nano") {
                    synthesized.s_idle = 5.0;    synthesized.c_aero = 0.01;
                } else if (raw.propulsion == "Electric Tactical") {
                    synthesized.s_idle = 15.0;   synthesized.c_aero = 0.04;
                } else if (raw.propulsion == "ICE Piston") {
                    synthesized.s_idle = 80.0;   synthesized.c_aero = 0.25;
                } else if (raw.propulsion == "Turboprop") {
                    synthesized.s_idle = 120.0;  synthesized.c_aero = 0.4;
                } else if (raw.propulsion == "Jet UCAV") {
                    synthesized.s_idle = 250.0;  synthesized.c_aero = 0.7;
                } else {
                    synthesized.s_idle = 30.0;   synthesized.c_aero = 0.1;
                }

                // 4. GEOMETRIC VISUAL CROSS-SECTION
                double fill_factor = (raw.uav_class == "Electric Nano" || raw.uav_class == "Tactical") ? 0.4 : 0.15;
                synthesized.a_vis = raw.wingspan * raw.length * fill_factor;

                // 5. AERODYNAMIC & DENSITY MODEL SURROGATES
                double ar_multiplier = (raw.uav_class == "MALE" || raw.uav_class == "HALE") ? 0.09 : 0.15;
                synthesized.wing_area = ar_multiplier * (raw.wingspan * raw.wingspan);
                
                double g = 9.81;
                double cl_max = 1.2;
                synthesized.stall_speed = std::sqrt((2.0 * raw.mtow * g) / (1.225 * synthesized.wing_area * cl_max));
                synthesized.max_wind_tolerance = std::min(45.0, 5.0 + std::sqrt(raw.mtow) * 1.5);

                // 6. RELIABILITY / MTBF RISK COEFFICIENTS
                if (raw.maturity == "Mature") {
                    synthesized.failure_probability = 0.001;
                } else if (raw.maturity == "Prototype") {
                    synthesized.failure_probability = 0.05; 
                } else if (raw.maturity == "Swarm") {
                    synthesized.failure_probability = 0.15;  
                } else {
                    synthesized.failure_probability = 0.02;
                }

                return synthesized;
            }
        }
        throw std::runtime_error("UAV identifier '" + name + "' not found in presets database.");
    }
};