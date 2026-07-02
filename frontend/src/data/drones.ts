export interface DroneRecord {
  name: string;
  uav_class: string;
  propulsion_class: string;
  max_speed: number;
  ceiling: number;
  mtow: number;
  wingspan: number;
  length: number;
  wing_area: number;
  stall_speed: number;
  max_wind_tolerance: number;
  sigma_front: number;
  sigma_side: number;
  sigma_avg: number;
  i_base: number;
  c_drag: number;
  s_idle: number;
  c_aero: number;
  a_vis: number;
  failure_probability: number;
}

export const DRONES: DroneRecord[] = [
  { name: "IAI Heron", uav_class: "MALE", propulsion_class: "ICE Piston", max_speed: 57.0, ceiling: 10000.0, mtow: 1150.0, wingspan: 16.6, length: 8.5, wing_area: 24.80, stall_speed: 22.32, max_wind_tolerance: 45.0, sigma_front: 0.50, sigma_side: 2.00, sigma_avg: 1.25, i_base: 150.0, c_drag: 0.15, s_idle: 80.0, c_aero: 0.25, a_vis: 21.17, failure_probability: 0.001 },
  { name: "Heron TP", uav_class: "HALE", propulsion_class: "Turboprop", max_speed: 113.0, ceiling: 13700.0, mtow: 5670.0, wingspan: 26.0, length: 14.0, wing_area: 60.84, stall_speed: 34.68, max_wind_tolerance: 45.0, sigma_front: 0.50, sigma_side: 2.00, sigma_avg: 1.25, i_base: 400.0, c_drag: 0.30, s_idle: 120.0, c_aero: 0.40, a_vis: 54.60, failure_probability: 0.001 },
  { name: "Rustom-2 (TAPAS BH-201)", uav_class: "MALE", propulsion_class: "ICE Piston", max_speed: 62.0, ceiling: 10600.0, mtow: 1800.0, wingspan: 20.6, length: 9.5, wing_area: 38.19, stall_speed: 25.00, max_wind_tolerance: 45.0, sigma_front: 0.50, sigma_side: 2.00, sigma_avg: 1.25, i_base: 150.0, c_drag: 0.15, s_idle: 80.0, c_aero: 0.25, a_vis: 29.36, failure_probability: 0.05 },
  { name: "Switch UAV", uav_class: "Tactical", propulsion_class: "Electric Tactical", max_speed: 22.0, ceiling: 6000.0, mtow: 6.5, wingspan: 2.4, length: 1.5, wing_area: 0.86, stall_speed: 9.04, max_wind_tolerance: 8.82, sigma_front: 0.02, sigma_side: 0.08, sigma_avg: 0.05, i_base: 10.0, c_drag: 0.02, s_idle: 15.0, c_aero: 0.04, a_vis: 1.44, failure_probability: 0.001 },
  { name: "MQ-9 Reaper", uav_class: "MALE", propulsion_class: "Turboprop", max_speed: 134.0, ceiling: 15240.0, mtow: 4760.0, wingspan: 20.0, length: 11.0, wing_area: 36.00, stall_speed: 41.48, max_wind_tolerance: 45.0, sigma_front: 0.50, sigma_side: 2.00, sigma_avg: 1.25, i_base: 400.0, c_drag: 0.30, s_idle: 120.0, c_aero: 0.40, a_vis: 33.00, failure_probability: 0.001 },
  { name: "Swarm Drones", uav_class: "Swarm", propulsion_class: "Electric Tactical", max_speed: 20.0, ceiling: 3000.0, mtow: 5.0, wingspan: 1.2, length: 1.0, wing_area: 0.22, stall_speed: 10.91, max_wind_tolerance: 8.35, sigma_front: 0.02, sigma_side: 0.08, sigma_avg: 0.05, i_base: 10.0, c_drag: 0.02, s_idle: 15.0, c_aero: 0.04, a_vis: 0.18, failure_probability: 0.05 },
  { name: "DRDO Ghatak", uav_class: "Stealth UCAV", propulsion_class: "Jet UCAV", max_speed: 260.0, ceiling: 12000.0, mtow: 8000.0, wingspan: 12.0, length: 8.0, wing_area: 21.60, stall_speed: 77.04, max_wind_tolerance: 45.0, sigma_front: 0.01, sigma_side: 0.05, sigma_avg: 0.03, i_base: 1200.0, c_drag: 0.60, s_idle: 250.0, c_aero: 0.70, a_vis: 14.40, failure_probability: 0.05 },
  { name: "Searcher", uav_class: "Tactical", propulsion_class: "ICE Piston", max_speed: 55.0, ceiling: 6100.0, mtow: 436.0, wingspan: 8.6, length: 5.8, wing_area: 11.09, stall_speed: 25.27, max_wind_tolerance: 36.32, sigma_front: 0.02, sigma_side: 0.08, sigma_avg: 0.05, i_base: 150.0, c_drag: 0.15, s_idle: 80.0, c_aero: 0.25, a_vis: 19.95, failure_probability: 0.001 },
  { name: "Harpy", uav_class: "Loitering Munition", propulsion_class: "ICE Piston", max_speed: 116.0, ceiling: 4500.0, mtow: 135.0, wingspan: 2.1, length: 2.7, wing_area: 0.66, stall_speed: 42.47, max_wind_tolerance: 22.44, sigma_front: 0.03, sigma_side: 0.15, sigma_avg: 0.09, i_base: 150.0, c_drag: 0.15, s_idle: 80.0, c_aero: 0.25, a_vis: 0.85, failure_probability: 0.001 },
  { name: "Rooster", uav_class: "Electric Nano", propulsion_class: "Electric Nano", max_speed: 10.0, ceiling: 1000.0, mtow: 1.2, wingspan: 0.4, length: 0.4, wing_area: 0.024, stall_speed: 18.27, max_wind_tolerance: 6.64, sigma_front: 0.005, sigma_side: 0.02, sigma_avg: 0.0125, i_base: 2.0, c_drag: 0.005, s_idle: 5.0, c_aero: 0.01, a_vis: 0.064, failure_probability: 0.05 },
  { name: "Black Hornet", uav_class: "Electric Nano", propulsion_class: "Electric Nano", max_speed: 6.0, ceiling: 100.0, mtow: 0.033, wingspan: 0.12, length: 0.16, wing_area: 0.00216, stall_speed: 15.68, max_wind_tolerance: 5.27, sigma_front: 0.005, sigma_side: 0.02, sigma_avg: 0.0125, i_base: 2.0, c_drag: 0.005, s_idle: 5.0, c_aero: 0.01, a_vis: 0.00768, failure_probability: 0.001 },
  { name: "Nagastra-1", uav_class: "Loitering Munition", propulsion_class: "Electric Tactical", max_speed: 25.0, ceiling: 4500.0, mtow: 9.0, wingspan: 2.0, length: 1.5, wing_area: 0.60, stall_speed: 12.81, max_wind_tolerance: 9.50, sigma_front: 0.03, sigma_side: 0.15, sigma_avg: 0.09, i_base: 10.0, c_drag: 0.02, s_idle: 15.0, c_aero: 0.04, a_vis: 0.45, failure_probability: 0.001 },
  { name: "Netra UAV", uav_class: "Tactical", propulsion_class: "Electric Nano", max_speed: 8.0, ceiling: 3000.0, mtow: 1.5, wingspan: 0.9, length: 0.9, wing_area: 0.12, stall_speed: 14.14, max_wind_tolerance: 6.84, sigma_front: 0.02, sigma_side: 0.08, sigma_avg: 0.05, i_base: 2.0, c_drag: 0.005, s_idle: 5.0, c_aero: 0.01, a_vis: 0.324, failure_probability: 0.001 },
];

export const DRONE_NAMES = DRONES.map((d) => d.name);
export const DRONE_BY_NAME: Record<string, DroneRecord> = Object.fromEntries(
  DRONES.map((d) => [d.name, d]),
);
