from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import time

import pandas as pd
import requests

from smard_client import PERIOD_END, PERIOD_START, TIMEZONE

BRIGHT_SKY_URL = "https://api.brightsky.dev/weather"


@dataclass(frozen=True)
class WeatherLocation:
    name: str
    role: str
    latitude: float
    longitude: float


WEATHER_LOCATIONS: list[WeatherLocation] = [
    WeatherLocation("Hamburg", "north / coastal wind indicator", 53.5511, 9.9937),
    WeatherLocation("Berlin", "eastern lowland indicator", 52.5200, 13.4050),
    WeatherLocation("Frankfurt", "central-west demand and weather indicator", 50.1109, 8.6821),
    WeatherLocation("Munich", "southern Germany indicator", 48.1351, 11.5820),
    WeatherLocation("Cologne", "western Germany indicator", 50.9375, 6.9603),
    WeatherLocation("Leipzig", "central-eastern Germany indicator", 51.3397, 12.3731),
]


def _safe_name(text: str) -> str:
    return text.lower().replace(" ", "_").replace("/", "_")


def _fetch_json(url: str, params: dict[str, Any], cache_file: Path, *, retries: int = 4) -> tuple[Any, bool]:
    if cache_file.exists():
        with cache_file.open("r", encoding="utf-8") as f:
            return json.load(f), False
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    headers = {"User-Agent": "q1-2025-energy-weather-analysis/1.0"}
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=60)
            response.raise_for_status()
            payload = response.json()
            tmp = cache_file.with_suffix(cache_file.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(payload, f)
            tmp.replace(cache_file)
            return payload, True
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < retries:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"Could not fetch Bright Sky weather data for params={params}") from last_error


def _payload_to_frame(payload: Any, location: WeatherLocation) -> pd.DataFrame:
    rows = payload.get("weather", []) if isinstance(payload, dict) else []
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "timestamp" not in df:
        return pd.DataFrame()
    df["Start date"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(TIMEZONE)
    df["Location"] = location.name
    df["Location role"] = location.role
    rename = {
        "wind_speed": "Wind Speed [km/h]",
        "wind_direction": "Wind Direction [deg]",
        "sunshine": "Sunshine [min]",
        "temperature": "Temperature [C]",
        "cloud_cover": "Cloud Cover [%]",
        "pressure_msl": "Pressure [hPa]",
        "relative_humidity": "Relative Humidity [%]",
        "precipitation": "Precipitation [mm]",
    }
    available = [c for c in rename if c in df]
    keep = ["Start date", "Location", "Location role"] + available
    df = df[keep].rename(columns=rename)
    df = df[(df["Start date"] >= PERIOD_START) & (df["Start date"] < PERIOD_END)]
    return df.sort_values(["Location", "Start date"]).reset_index(drop=True)


def download_weather(raw_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    raw_path = Path(raw_dir) / "weather_bright_sky"
    all_frames: list[pd.DataFrame] = []
    messages: list[str] = []
    for loc in WEATHER_LOCATIONS:
        params = {
            "lat": loc.latitude,
            "lon": loc.longitude,
            "date": PERIOD_START.date().isoformat(),
            "last_date": (PERIOD_END - pd.Timedelta(days=1)).date().isoformat(),
            "tz": TIMEZONE,
        }
        cache_file = raw_path / f"{_safe_name(loc.name)}_q1_2025.json"
        payload, was_downloaded = _fetch_json(BRIGHT_SKY_URL, params, cache_file)
        messages.append(f"{'Downloaded' if was_downloaded else 'Loaded cached'} weather data for {loc.name}.")
        frame = _payload_to_frame(payload, loc)
        if frame.empty:
            messages.append(f"No weather records returned for {loc.name}.")
        else:
            all_frames.append(frame)

    if not all_frames:
        return pd.DataFrame(), pd.DataFrame(), messages

    locations_df = pd.concat(all_frames, ignore_index=True)
    numeric_cols = locations_df.select_dtypes(include="number").columns.tolist()
    aggregated = locations_df.groupby("Start date", as_index=False)[numeric_cols].mean()
    aggregated = aggregated.rename(
        columns={
            "Wind Speed [km/h]": "Weather Wind Speed [km/h]",
            "Wind Direction [deg]": "Weather Wind Direction [deg]",
            "Sunshine [min]": "Weather Sunshine [min]",
            "Temperature [C]": "Weather Temperature [C]",
            "Cloud Cover [%]": "Weather Cloud Cover [%]",
            "Pressure [hPa]": "Weather Pressure [hPa]",
            "Relative Humidity [%]": "Weather Relative Humidity [%]",
            "Precipitation [mm]": "Weather Precipitation [mm]",
        }
    )
    return aggregated, locations_df, messages


def load_or_download_weather(processed_file: str | Path, locations_file: str | Path, raw_dir: str | Path):
    processed_path = Path(processed_file)
    locations_path = Path(locations_file)
    if processed_path.exists() and locations_path.exists():
        agg = pd.read_csv(processed_path, parse_dates=["Start date"])
        loc = pd.read_csv(locations_path, parse_dates=["Start date"])
        return agg, loc, [f"Loaded processed weather data from {processed_path}."]
    agg, loc, messages = download_weather(raw_dir)
    if not agg.empty:
        processed_path.parent.mkdir(parents=True, exist_ok=True)
        agg.to_csv(processed_path, index=False)
        loc.to_csv(locations_path, index=False)
        messages.append(f"Saved processed weather files to {processed_path.parent}.")
    return agg, loc, messages
