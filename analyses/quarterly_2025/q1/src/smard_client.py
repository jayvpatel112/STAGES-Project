from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import time

import numpy as np
import pandas as pd
import requests

TIMEZONE = "Europe/Berlin"
PERIOD_START = pd.Timestamp("2025-01-01 00:00", tz=TIMEZONE)
PERIOD_END = pd.Timestamp("2025-04-01 00:00", tz=TIMEZONE)

BASE_URL = "https://www.smard.de/app/chart_data"

SOURCE_FILTERS: dict[str, int] = {
    "Lignite": 1223,
    "Nuclear": 1224,
    "Wind Offshore": 1225,
    "Hydro": 1226,
    "Other Conventional": 1227,
    "Other Renewable": 1228,
    "Biomass": 4066,
    "Wind Onshore": 4067,
    "Solar": 4068,
    "Hard Coal": 4069,
    "Pumped Storage": 4070,
    "Fossil Gas": 4071,
    "Total Load": 410,
}

RENEWABLES: list[str] = [
    "Wind Onshore",
    "Wind Offshore",
    "Solar",
    "Hydro",
    "Biomass",
    "Other Renewable",
]

CONVENTIONALS: list[str] = [
    "Lignite",
    "Hard Coal",
    "Fossil Gas",
    "Nuclear",
    "Other Conventional",
    "Pumped Storage",
]

GENERATION_SOURCES: list[str] = RENEWABLES + CONVENTIONALS


@dataclass(frozen=True)
class DownloadResult:
    dataframe: pd.DataFrame
    raw_files_downloaded: int
    raw_files_loaded_from_cache: int
    warnings: list[str]


def _safe_name(text: str) -> str:
    return (
        text.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace("__", "_")
    )


def _normalise_epoch_ms(value: int | float | str) -> int:
    """Return epoch milliseconds from a SMARD timestamp-like value."""
    as_int = int(float(value))
    # Seconds since epoch are ~1.7e9; milliseconds are ~1.7e12.
    if as_int < 10_000_000_000:
        return as_int * 1000
    return as_int


def _extract_timestamps(payload: Any) -> list[int]:
    """Extract SMARD index timestamps from several possible JSON shapes."""
    found: list[int] = []

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)
        elif isinstance(obj, (int, float, str)):
            try:
                ts = _normalise_epoch_ms(obj)
            except (ValueError, TypeError):
                return
            # Valid modern epoch milliseconds range, wide enough for SMARD files.
            if 1_000_000_000_000 <= ts <= 2_000_000_000_000:
                found.append(ts)

    walk(payload)
    return sorted(set(found))


def _extract_series(payload: Any) -> list[tuple[int, float | None]]:
    """Extract (timestamp_ms, value) pairs from a SMARD series JSON file."""
    if isinstance(payload, dict):
        series = payload.get("series") or payload.get("data") or payload.get("values")
    else:
        series = payload

    rows: list[tuple[int, float | None]] = []
    if not isinstance(series, list):
        return rows

    for item in series:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        try:
            ts = _normalise_epoch_ms(item[0])
        except (ValueError, TypeError):
            continue
        raw_value = item[1]
        if raw_value is None:
            value = None
        else:
            try:
                value = float(raw_value)
            except (ValueError, TypeError):
                value = None
        rows.append((ts, value))
    return rows


def _fetch_json(url: str, cache_file: Path, *, retries: int = 4, pause: float = 1.5) -> tuple[Any, bool]:
    """Fetch JSON with disk cache. Returns (payload, downloaded_now)."""
    if cache_file.exists():
        with cache_file.open("r", encoding="utf-8") as f:
            return json.load(f), False

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    headers = {"User-Agent": "q1-2025-energy-analysis/1.0"}
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            payload = response.json()
            tmp_file = cache_file.with_suffix(cache_file.suffix + ".tmp")
            with tmp_file.open("w", encoding="utf-8") as f:
                json.dump(payload, f)
            tmp_file.replace(cache_file)
            return payload, True
        except Exception as exc:  # noqa: BLE001 - we want a robust notebook-level error
            last_error = exc
            if attempt < retries:
                time.sleep(pause * attempt)
    raise RuntimeError(f"Could not fetch SMARD URL after {retries} attempts: {url}") from last_error


def _index_url(filter_id: int) -> str:
    return f"{BASE_URL}/{filter_id}/DE/index_hour.json"


def _series_url(filter_id: int, timestamp_ms: int) -> str:
    return f"{BASE_URL}/{filter_id}/DE/{filter_id}_DE_hour_{timestamp_ms}.json"


def _candidate_index_timestamps(index_timestamps: list[int]) -> list[int]:
    """Pick SMARD series files likely to overlap Q1 2025.

    The index timestamps usually correspond to file time anchors. To avoid boundary
    misses, we include a buffer and the closest file before the quarter.
    """
    if not index_timestamps:
        return []
    ts_df = pd.DataFrame({"timestamp_ms": index_timestamps})
    ts_df["time"] = pd.to_datetime(ts_df["timestamp_ms"], unit="ms", utc=True).dt.tz_convert(TIMEZONE)

    buffer_start = PERIOD_START - pd.Timedelta(days=14)
    buffer_end = PERIOD_END + pd.Timedelta(days=14)
    mask = (ts_df["time"] >= buffer_start) & (ts_df["time"] <= buffer_end)
    selected = ts_df.loc[mask, "timestamp_ms"].tolist()

    before = ts_df.loc[ts_df["time"] < PERIOD_START, "timestamp_ms"]
    if not before.empty:
        selected.append(int(before.iloc[-1]))

    after = ts_df.loc[ts_df["time"] >= PERIOD_END, "timestamp_ms"]
    if not after.empty:
        selected.append(int(after.iloc[0]))

    # If no timestamps were selected, use the latest small batch as a fallback for
    # unusual index structures. This is not synthetic data; it only broadens which
    # real API files are checked.
    if not selected:
        selected = index_timestamps[-20:]
    return sorted(set(int(x) for x in selected))


def _download_source(source_name: str, filter_id: int, raw_dir: Path) -> tuple[pd.DataFrame, int, int, list[str]]:
    downloaded = 0
    cached = 0
    warnings: list[str] = []

    source_dir = raw_dir / "smard" / f"{filter_id}_{_safe_name(source_name)}"
    index_payload, was_downloaded = _fetch_json(_index_url(filter_id), source_dir / "index_hour.json")
    downloaded += int(was_downloaded)
    cached += int(not was_downloaded)

    index_ts = _extract_timestamps(index_payload)
    if not index_ts:
        raise RuntimeError(f"SMARD index for {source_name} ({filter_id}) did not contain timestamps.")

    candidates = _candidate_index_timestamps(index_ts)
    all_rows: list[tuple[int, float | None]] = []
    for ts in candidates:
        payload, was_downloaded = _fetch_json(
            _series_url(filter_id, ts),
            source_dir / f"{filter_id}_DE_hour_{ts}.json",
        )
        downloaded += int(was_downloaded)
        cached += int(not was_downloaded)
        all_rows.extend(_extract_series(payload))

    if not all_rows:
        return pd.DataFrame(columns=["Start date", source_name]), downloaded, cached, [
            f"No SMARD series rows returned for {source_name}."
        ]

    df = pd.DataFrame(all_rows, columns=["timestamp_ms", source_name])
    df["Start date"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True).dt.tz_convert(TIMEZONE)
    df = df.drop(columns=["timestamp_ms"])
    df = df[(df["Start date"] >= PERIOD_START) & (df["Start date"] < PERIOD_END)]
    df = df.drop_duplicates(subset="Start date", keep="last").sort_values("Start date")

    if df.empty:
        warnings.append(f"No Q1 2025 rows found for {source_name}; check SMARD index coverage.")
    return df, downloaded, cached, warnings


def download_q1_2025(raw_dir: str | Path) -> DownloadResult:
    """Download hourly SMARD generation and load data for Q1 2025 Germany.

    Values are kept in MWh per hour, matching the SMARD chart-data API.
    """
    raw_path = Path(raw_dir)
    expected_index = pd.date_range(PERIOD_START, PERIOD_END, freq="h", inclusive="left")
    result = pd.DataFrame({"Start date": expected_index})

    total_downloaded = 0
    total_cached = 0
    warnings: list[str] = []

    for source_name, filter_id in SOURCE_FILTERS.items():
        source_df, downloaded, cached, source_warnings = _download_source(source_name, filter_id, raw_path)
        total_downloaded += downloaded
        total_cached += cached
        warnings.extend(source_warnings)
        result = result.merge(source_df, on="Start date", how="left")

    # Germany had no nuclear generation in Q1 2025. If SMARD exposes nuclear as an
    # empty series rather than hourly zeros, make the accounting explicit here.
    if "Nuclear" in result and result["Nuclear"].isna().all():
        result["Nuclear"] = 0.0
        warnings.append(
            "SMARD returned no Q1 rows for Nuclear; set to 0.0 MWh/h because German nuclear generation was absent in 2025."
        )

    numeric_cols = [c for c in SOURCE_FILTERS if c in result.columns]
    result[numeric_cols] = result[numeric_cols].apply(pd.to_numeric, errors="coerce")

    result["Total Renewable"] = result[RENEWABLES].sum(axis=1, min_count=1)
    result["Total Conventional"] = result[CONVENTIONALS].sum(axis=1, min_count=1)
    result["Total Generation"] = result[GENERATION_SOURCES].sum(axis=1, min_count=1)
    result["Total Wind"] = result[["Wind Onshore", "Wind Offshore"]].sum(axis=1, min_count=1)
    result["Residual Load"] = result["Total Load"] - result["Total Renewable"]
    result["Renewable Shortfall"] = result["Residual Load"].clip(lower=0)
    result["Renewable Surplus Against Load"] = (-result["Residual Load"]).clip(lower=0)
    result["Renewable Share of Load"] = result["Total Renewable"] / result["Total Load"]
    result["Renewable Share of Generation"] = result["Total Renewable"] / result["Total Generation"]
    result["Net Trade Proxy"] = result["Total Generation"] - result["Total Load"]
    result["Net Import Proxy"] = (-result["Net Trade Proxy"]).clip(lower=0)
    result["Exportable Surplus Proxy"] = result["Net Trade Proxy"].clip(lower=0)
    result["Renewables Meet Load"] = result["Total Renewable"] >= result["Total Load"]
    result["Date"] = result["Start date"].dt.date
    result["Month Number"] = result["Start date"].dt.month
    result["Month"] = result["Start date"].dt.month_name()
    result["Hour"] = result["Start date"].dt.hour
    result["Weekday"] = result["Start date"].dt.day_name()

    missing_counts = result[numeric_cols].isna().sum()
    serious_missing = missing_counts[missing_counts > 0]
    if not serious_missing.empty:
        warnings.append("Missing hourly values detected: " + serious_missing.to_dict().__repr__())

    return DownloadResult(
        dataframe=result,
        raw_files_downloaded=total_downloaded,
        raw_files_loaded_from_cache=total_cached,
        warnings=warnings,
    )
