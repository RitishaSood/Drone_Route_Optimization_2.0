from __future__ import annotations

import json

from pipeline.path_planner.vehicle_model import EnvironmentState, summarize_path_performance, summary_to_dict


def main() -> int:
    env = EnvironmentState(
        environment_enabled=True,
        wind_enabled=True,
        wind_speed_mps=10.0,
        gust_speed_mps=5.0,
        rain_enabled=True,
        rain_intensity=0.5,
        fog_enabled=True,
        fog_intensity=0.25,
        snow_enabled=True,
        snow_intensity=0.1,
        hail_enabled=True,
        hail_intensity=0.05,
        turbulence_enabled=True,
        turbulence_intensity=0.2,
        temperature_enabled=True,
        temperature_c=45.0,
        thunderstorm_enabled=True,
        thunderstorm=True,
        ew_jamming_enabled=True,
        ew_jammers=[{"x": 1, "y": 0, "z": 50, "strength": 1.0, "max_range": 20.0}],
        time_aware=True,
        time_of_day_enabled=True,
        mission_start_hour=22,
        mission_duration_hours=6.0,
        time_sample_interval_minutes=30,
        mission_deadline_minutes=0.001,
        time_step_seconds=30.0,
    )

    summary = summarize_path_performance(
        [(0, 0, 50), (1, 0, 50), (2, 0, 50)],
        drone_name="IAI Heron",
        env=env,
    )

    payload = summary_to_dict(summary)
    print(json.dumps(payload, indent=2))

    assert payload["total_environment_penalty"] > 0
    assert payload["average_environment_penalty"] > 0
    assert payload["environment_enabled"] is True
    assert payload["time_of_day_enabled"] is True
    assert payload["visual_time_multiplier_average"] < 1.0
    assert payload["ir_time_multiplier_average"] > 1.0
    assert payload["total_ew_jamming_exposure"] >= 0
    assert payload["average_ew_jamming_exposure"] >= 0
    assert payload["max_ew_jamming_exposure"] >= 0
    assert payload["communication_loss_risk"] >= 0
    assert payload["gps_navigation_penalty"] >= 0
    assert payload["time_aware"] is True
    assert payload["mission_deadline_minutes"] > 0
    assert payload["time_feasible"] is False
    assert payload["mission_feasible"] is False
    assert payload["metric_note"].startswith("Fuel, time, and wear values")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
