from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class EnvironmentState:
    environment_enabled: bool = False
    wind_enabled: bool = False
    wind_speed_mps: float = 0.0
    wind_direction_deg: float = 0.0
    gust_speed_mps: float = 0.0
    rain_enabled: bool = False
    rain_intensity: float = 0.0
    fog_enabled: bool = False
    fog_intensity: float = 0.0
    snow_enabled: bool = False
    snow_intensity: float = 0.0
    hail_enabled: bool = False
    hail_intensity: float = 0.0
    turbulence_enabled: bool = False
    turbulence_intensity: float = 0.0
    temperature_enabled: bool = False
    temperature_c: float = 25.0
    thunderstorm_enabled: bool = False
    thunderstorm: bool = False
    ew_jamming_enabled: bool = False
    ew_jammers: list[dict] | None = None
    time_aware: bool = True
    mission_deadline_minutes: float = 120.0
    time_step_seconds: float = 60.0
    time_of_day_enabled: bool = False
    mission_start_hour: int = 6
    mission_duration_hours: float = 6.0
    time_sample_interval_minutes: int = 30


def clamp_environment(env: EnvironmentState) -> EnvironmentState:
    for field in ("rain_intensity", "fog_intensity", "snow_intensity", "hail_intensity", "turbulence_intensity"):
        setattr(env, field, max(0.0, min(1.0, float(getattr(env, field)))))
    env.wind_speed_mps = max(0.0, min(40.0, float(env.wind_speed_mps)))
    env.gust_speed_mps = max(0.0, min(60.0, float(env.gust_speed_mps)))
    env.wind_direction_deg = max(0.0, min(359.0, float(env.wind_direction_deg)))
    env.temperature_c = float(env.temperature_c)
    return env


def _get_any(data: dict | None, *keys: str, default=None):
    if not data:
        return default
    for key in keys:
        if key in data:
            return data[key]
    return default


def environment_from_dict(data: dict | None) -> EnvironmentState:
    raw_jammers = _get_any(data, "ewJammingSensors", "ew_jammers", "EW_JAMMERS_JSON", default=[])
    if isinstance(raw_jammers, str):
        try:
            raw_jammers = json.loads(raw_jammers)
        except json.JSONDecodeError:
            raw_jammers = []
    env = EnvironmentState(
        environment_enabled=bool(_get_any(data, "environmentEnabled", "environment_enabled", "ENVIRONMENT_ENABLED", default=False)),
        wind_enabled=bool(_get_any(data, "windEnabled", "wind_enabled", "WIND_ENABLED", default=False)),
        wind_speed_mps=float(_get_any(data, "windSpeed", "wind_speed", "wind_speed_mps", "WIND_SPEED", "WIND_SPEED_MPS", default=0.0) or 0.0),
        wind_direction_deg=float(_get_any(data, "windDirection", "wind_direction_deg", "WIND_DIRECTION", default=0.0) or 0.0),
        gust_speed_mps=float(_get_any(data, "gustSpeed", "gust_speed", "gust_speed_mps", "GUST_SPEED", default=0.0) or 0.0),
        rain_enabled=bool(_get_any(data, "rainEnabled", "rain_enabled", "RAIN_ENABLED", default=False)),
        rain_intensity=float(_get_any(data, "rainIntensity", "rain_intensity", "RAIN_INTENSITY", default=0.0) or 0.0),
        fog_enabled=bool(_get_any(data, "fogEnabled", "fog_enabled", "FOG_ENABLED", default=False)),
        fog_intensity=float(_get_any(data, "fogIntensity", "fog_intensity", "FOG_INTENSITY", default=0.0) or 0.0),
        snow_enabled=bool(_get_any(data, "snowEnabled", "snow_enabled", "SNOW_ENABLED", default=False)),
        snow_intensity=float(_get_any(data, "snowIntensity", "snow_intensity", "SNOW_INTENSITY", default=0.0) or 0.0),
        hail_enabled=bool(_get_any(data, "hailEnabled", "hail_enabled", "HAIL_ENABLED", default=False)),
        hail_intensity=float(_get_any(data, "hailIntensity", "hail_intensity", "HAIL_INTENSITY", default=0.0) or 0.0),
        turbulence_enabled=bool(_get_any(data, "turbulenceEnabled", "turbulence_enabled", "TURBULENCE_ENABLED", default=False)),
        turbulence_intensity=float(_get_any(data, "turbulenceIntensity", "turbulence_intensity", "TURBULENCE_INTENSITY", default=0.0) or 0.0),
        temperature_enabled=bool(_get_any(data, "temperatureEnabled", "temperature_enabled", "TEMPERATURE_ENABLED", default=False)),
        temperature_c=float(_get_any(data, "temperatureC", "temperature_c", "TEMPERATURE_C", default=25.0) or 25.0),
        thunderstorm_enabled=bool(_get_any(data, "thunderstormEnabled", "thunderstorm_enabled", "THUNDERSTORM_ENABLED", default=False)),
        thunderstorm=bool(_get_any(data, "thunderstorm", "THUNDERSTORM", default=False)),
        ew_jamming_enabled=bool(_get_any(data, "ewJammingEnabled", "ew_jamming_enabled", "EW_JAMMING_ENABLED", default=False)),
        ew_jammers=list(raw_jammers or []),
        time_aware=bool(_get_any(data, "timeAware", "time_aware", "TIME_AWARE", default=True)),
        mission_deadline_minutes=float(_get_any(data, "missionDeadlineMinutes", "mission_deadline_minutes", "MISSION_DEADLINE_MINUTES", default=120.0) or 120.0),
        time_step_seconds=float(_get_any(data, "timeStepSeconds", "time_step_seconds", "TIME_STEP_SECONDS", default=60.0) or 60.0),
        time_of_day_enabled=bool(_get_any(data, "timeOfDayEnabled", "time_of_day_enabled", "TIME_OF_DAY_ENABLED", default=False)),
        mission_start_hour=int(_get_any(data, "missionStartHour", "mission_start_hour", "MISSION_START_HOUR", default=6) or 6),
        mission_duration_hours=float(_get_any(data, "missionDurationHours", "mission_duration_hours", "MISSION_DURATION_HOURS", default=6.0) or 6.0),
        time_sample_interval_minutes=int(_get_any(data, "timeSampleIntervalMinutes", "time_sample_interval_minutes", "TIME_SAMPLE_INTERVAL_MINUTES", default=30) or 30),
    )
    if not env.environment_enabled:
        env.wind_enabled = env.rain_enabled = env.fog_enabled = env.snow_enabled = env.hail_enabled = env.turbulence_enabled = env.temperature_enabled = env.thunderstorm_enabled = False
    return clamp_environment(env)
