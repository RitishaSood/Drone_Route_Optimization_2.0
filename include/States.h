#pragma once
#include <string>

// Explicitly type the sensors for Field Separation
enum class ThreatType {
    Radar,
    IR,
    Acoustic,
    Visual
};

// Precomputed dynamic signatures to save CPU cycles
struct DynamicSignature {
    double v_ratio;
    double v_sq;
    double v_cubed;
    double i_dynamic;
    double s_dynamic;
};

// Represents the UAV's physical state
struct DroneState {
    std::string name;
    std::string uav_class;
    std::string propulsion_class;

    // Kinematics
    double speed;              
    double heading;            
    double max_speed;          
    double ceiling;            
    double mtow;               

    // Aerodynamics
    double wingspan;           
    double length;             
    double wing_area;          
    double stall_speed;        
    double max_wind_tolerance; 

    // Signatures
    double sigma_front;        
    double sigma_side;         
    double sigma_avg;          
    double i_base;             
    double c_drag;             
    double s_idle;             
    double c_aero;             
    double a_vis;              

    // Reliability
    double failure_probability;
};

struct EnvState {
    double air_density;         
    double wind_speed;          
    
    double ir_gamma;            
    double ir_c_bg;             
    
    double n_bg;                
    
    double visual_lux;          
    double visual_c_bg;         
};