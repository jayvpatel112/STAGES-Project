"""
utils.py — STAGES Project
Bauhaus-Universität Weimar · SoSe 2026

All data pipeline functions in one place:
  - SMARD energy data  (load, clean, features, aggregate)
  - DWD weather data   (download, clean, merge)

Import in Marimo:  from utils import *
"""

import os
import io
import glob
import zipfile

import requests
import pandas as pd

# ═══════════════════════════════════════════════════════════════════════════════
# 1.  DWD STATION REGISTRY
#     IDs verified May 2026 against FF/SD_Stundenwerte_Beschreibung_Stationen.txt
# ═══════════════════════════════════════════════════════════════════════════════

DWD_STATIONS = {
    "01975": "Hamburg-Fuhlsbüttel",   # North — main Hamburg station
    "03379": "München",                # South — solar region
    "03987": "Potsdam",                # Central Brandenburg
    "01420": "Frankfurt/Main",         # Central — good baseline
    "05792": "Zugspitze",             # Alpine — high wind
    "02564": "Kiel-Holtenau",         # North — Baltic/offshore proxy
}

DWD_BASE = (
    "https://opendata.dwd.de/climate_environment/CDC/"
    "observations_germany/climate/hourly/"
)


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  DWD DOWNLOAD
# ═══════════════════════════════════════════════════════════════════════════════

def dwd_download_station(station_id: str, label: str, url: str, out_dir: str) -> bool:
    """Download one zip from DWD and extract the produkt_*.txt file."""
    os.makedirs(out_dir, exist_ok=True)
    try:
        r = requests.get(url, timeout=60)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False
    if r.status_code != 200:
        return False
    try:
        zf = zipfile.ZipFile(io.BytesIO(r.content))
    except zipfile.BadZipFile:
        return False
    data_files = [f for f in zf.namelist() if f.startswith("produkt_")]
    if not data_files:
        return False
    for fname in data_files:
        data = zf.read(fname)
        with open(os.path.join(out_dir, os.path.basename(fname)), "wb") as f:
            f.write(data)
    return True


def dwd_download_all(stations: dict = None) -> dict:
    """
    Download wind, sun, and solar data for all stations.

    Returns a status dict:
        { station_id: { "wind": True/False, "sun": True/False, "solar": True/False } }
    """
    if stations is None:
        stations = DWD_STATIONS

    targets = [
        ("wind",  DWD_BASE + "wind/recent/stundenwerte_FF_{id}_akt.zip",  "data/dwd/{id}_wind"),
        ("sun",   DWD_BASE + "sun/recent/stundenwerte_SD_{id}_akt.zip",   "data/dwd/{id}_sun"),
        ("solar", DWD_BASE + "solar/stundenwerte_ST_{id}_row.zip",         "data/dwd/{id}_solar"),
    ]

    status = {}
    for sid in stations:
        status[sid] = {}
        for label, url_tpl, dir_tpl in targets:
            ok = dwd_download_station(
                sid, label,
                url_tpl.format(id=sid),
                dir_tpl.format(id=sid),
            )
            status[sid][label] = ok
    return status


def dwd_download_summary(status: dict) -> str:
    """Return a markdown table showing which downloads succeeded."""
    lines = ["| Station | Wind | Sun | Solar |", "|---------|------|-----|-------|"]
    for sid, results in status.items():
        name = DWD_STATIONS.get(sid, sid)
        def icon(v): return "✅" if v else "❌"
        lines.append(
            f"| {name} (`{sid}`) | {icon(results.get('wind'))} | "
            f"{icon(results.get('sun'))} | {icon(results.get('solar'))} |"
        )
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  DWD CLEAN
# ═══════════════════════════════════════════════════════════════════════════════

def _dwd_parse_timestamp(df: pd.DataFrame) -> pd.Series:
    """Parse MESS_DATUM column (YYYYMMDDHH) → tz-aware Europe/Berlin time."""
    return (
        pd.to_datetime(df["MESS_DATUM"].astype(str), format="%Y%m%d%H", utc=True)
        .dt.tz_convert("Europe/Berlin")
    )


def dwd_load_wind(station_id: str) -> "pd.DataFrame | None":
    """
    Load hourly wind speed (m/s) for one station.
    DWD column F = mean wind speed. Values < 0 (coded -999) replaced with NaN.
    """
    files = glob.glob(f"data/dwd/{station_id}_wind/produkt_*.txt")
    if not files:
        return None
    df = pd.read_csv(files[0], sep=";", encoding="latin-1")
    df.columns = df.columns.str.strip()
    df["Date"] = _dwd_parse_timestamp(df)
    col = next((c for c in df.columns if c.strip() == "F"), None)
    if col is None:
        return None
    df["wind_speed"] = pd.to_numeric(df[col], errors="coerce")
    df.loc[df["wind_speed"] < 0, "wind_speed"] = None
    df["station_id"] = station_id
    return df[["Date", "station_id", "wind_speed"]].copy()


def dwd_load_sun(station_id: str) -> "pd.DataFrame | None":
    """
    Load hourly sunshine duration (minutes/hour) for one station.
    DWD column SD_SO: 0–60 min. Values < 0 replaced with NaN.
    """
    files = glob.glob(f"data/dwd/{station_id}_sun/produkt_*.txt")
    if not files:
        return None
    df = pd.read_csv(files[0], sep=";", encoding="latin-1")
    df.columns = df.columns.str.strip()
    df["Date"] = _dwd_parse_timestamp(df)
    col = next((c for c in df.columns if c.strip() == "SD_SO"), None)
    if col is None:
        return None
    df["sunshine_min"] = pd.to_numeric(df[col], errors="coerce")
    df.loc[df["sunshine_min"] < 0, "sunshine_min"] = None
    df["station_id"] = station_id
    return df[["Date", "station_id", "sunshine_min"]].copy()


def _dwd_parse_solar_timestamp(df: pd.DataFrame) -> pd.Series:
    """
    Parse solar file timestamps → naive datetime (no timezone).

    Solar files use MESS_DATUM_WOZ with format 'YYYYMMDDhh:mm'
    (e.g. '2005010101:00') — local solar time, NOT the standard YYYYMMDDHH
    used by wind/sun files.

    Two problems with solar timestamps:
    1. Format is '%Y%m%d%H:%M' not '%Y%m%d%H' → ValueError if wrong format used
    2. The file spans 20 years so DST ambiguity (clocks going back) raises errors
       if you try to tz_localize. We return naive timestamps instead —
       the merge with SMARD (also stripped to naive) still aligns correctly.
    """
    ts_col = "MESS_DATUM_WOZ" if "MESS_DATUM_WOZ" in df.columns else "MESS_DATUM"
    return pd.to_datetime(
        df[ts_col].astype(str).str.strip(),
        format="%Y%m%d%H:%M"
    )


def dwd_load_solar(station_id: str) -> "pd.DataFrame | None":
    """
    Load hourly global radiation (J/cm²) from the solar/ folder.
    DWD column FG_LBERG = global incoming radiation. Values < 0 → NaN.
    Note: solar/ has no recent/ subfolder — one file covers full history.
    Note: uses _dwd_parse_solar_timestamp(), NOT _dwd_parse_timestamp(),
          because solar files use format '%Y%m%d%H:%M' not '%Y%m%d%H'.
    """
    files = glob.glob(f"data/dwd/{station_id}_solar/produkt_*.txt")
    if not files:
        return None
    df = pd.read_csv(files[0], sep=";", encoding="latin-1")
    df.columns = df.columns.str.strip()
    df["Date"] = _dwd_parse_solar_timestamp(df)
    col = next((c for c in df.columns if c.strip() == "FG_LBERG"), None)
    if col is None:
        return None
    df["global_radiation"] = pd.to_numeric(df[col], errors="coerce")
    df.loc[df["global_radiation"] < 0, "global_radiation"] = None
    df["station_id"] = station_id
    return df[["Date", "station_id", "global_radiation"]].copy()


def dwd_build_national(stations: dict = None) -> pd.DataFrame:
    """
    Load wind + sun + solar for all stations, average per hour across stations.

    Returns hourly DataFrame:
        Date | wind_speed (m/s) | sunshine_min (min/hr) | global_radiation (J/cm²)
    """
    if stations is None:
        stations = DWD_STATIONS

    wind_frames, sun_frames, solar_frames = [], [], []
    for sid in stations:
        w = dwd_load_wind(sid)
        s = dwd_load_sun(sid)
        r = dwd_load_solar(sid)
        if w is not None: wind_frames.append(w)
        if s is not None: sun_frames.append(s)
        if r is not None: solar_frames.append(r)

    def _avg(frames, col):
        if not frames:
            return pd.DataFrame(columns=["Date", col])
        combined = pd.concat(frames)
        # Strip timezone so solar (naive) and wind/sun (tz-aware) merge without error
        if combined["Date"].dt.tz is not None:
            combined["Date"] = combined["Date"].dt.tz_localize(None)
        return combined.groupby("Date")[col].mean().reset_index()

    weather = _avg(wind_frames, "wind_speed")
    weather = weather.merge(_avg(sun_frames,   "sunshine_min"),    on="Date", how="outer")
    weather = weather.merge(_avg(solar_frames, "global_radiation"), on="Date", how="outer")
    return weather.sort_values("Date").reset_index(drop=True)


def dwd_save(df: pd.DataFrame, path: str = "data/dwd/weather_national.csv") -> str:
    """
    Save the national weather DataFrame to CSV.

    Only keeps rows where at least one weather value is non-null.
    This prevents the solar file's 20-year history from inflating the row count
    and making wind/sun appear 100% missing (they only cover the last 500 days).
    Also strips timezone info to avoid mixed-tz issues.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = df.copy()
    if hasattr(out["Date"], "dt") and out["Date"].dt.tz is not None:
        out["Date"] = out["Date"].dt.tz_localize(None)
    weather_cols = [c for c in ["wind_speed", "sunshine_min", "global_radiation"] if c in out.columns]
    out = out.dropna(subset=weather_cols, how="all")
    out = out.sort_values("Date").reset_index(drop=True)
    out.to_csv(path, index=False)
    return path


def dwd_load(path: str = "data/dwd/weather_national.csv") -> pd.DataFrame:
    """Load the saved national weather CSV as timezone-naive datetime."""
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def dwd_quality_report(df: pd.DataFrame) -> str:
    """
    Return a markdown quality-report table.

    Wind + sun cover only the last ~500 days (recent/ folder).
    Solar covers 2005 to present. Showing available rows per column
    makes this difference clear instead of showing misleading 100% missing.
    """
    lines = [
        "| Column | Available rows | Missing rows | Missing % | Mean |",
        "|--------|---------------|-------------|-----------|------|",
    ]
    for col in ["wind_speed", "sunshine_min", "global_radiation"]:
        if col not in df.columns:
            continue
        total    = len(df)
        valid    = int(df[col].notna().sum())
        missing  = total - valid
        pct      = missing / total * 100
        mean     = df[col].mean()
        mean_str = f"{mean:.2f}" if not pd.isna(mean) else "—"
        lines.append(f"| `{col}` | {valid:,} | {missing:,} | {pct:.1f}% | {mean_str} |")
    lines.append(f"\n> Date range: **{df['Date'].min()}** → **{df['Date'].max()}** · Rows: **{len(df):,}**")
    lines.append("> Wind + sun cover the last ~500 days only. Solar covers 2005–present. This is expected.")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  SMARD  —  LOAD & CLEAN
# ═══════════════════════════════════════════════════════════════════════════════

def smard_load_raw(file_name: str, folder: str = "data") -> pd.DataFrame:
    """Load a raw SMARD CSV export (semicolon-separated, UTF-8 BOM)."""
    return pd.read_csv(
        os.path.join(folder, file_name),
        sep=";", encoding="utf-8-sig", low_memory=False,
    )


def _parse_mwh(series: pd.Series) -> pd.Series:
    """Convert SMARD MWh strings ('1,234.5' or '-') to float."""
    return pd.to_numeric(
        series.astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("-", "0", regex=False),
        errors="coerce",
    ).fillna(0)


def smard_clean_generation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the Actual_generation SMARD export.
    Renames all source columns, parses MWh strings,
    and returns a tidy DataFrame with a 'Date' column.
    """
    col_map = {
        "Biomass [MWh] Calculated resolutions":               "Biomass",
        "Hydropower [MWh] Calculated resolutions":            "Hydro",
        "Wind offshore [MWh] Calculated resolutions":         "Wind_Offshore",
        "Wind onshore [MWh] Calculated resolutions":          "Wind_Onshore",
        "Photovoltaics [MWh] Calculated resolutions":         "Solar",
        "Other renewable [MWh] Calculated resolutions":       "Other_Renewable",
        "Nuclear [MWh] Calculated resolutions":               "Nuclear",
        "Lignite [MWh] Calculated resolutions":               "Lignite",
        "Hard coal [MWh] Calculated resolutions":             "Hard_Coal",
        "Fossil gas [MWh] Calculated resolutions":            "Gas",
        "Hydro pumped storage [MWh] Calculated resolutions":  "Pumped_Storage",
        "Other conventional [MWh] Calculated resolutions":    "Other_Conventional",
    }
    out = df.rename(columns=col_map).copy()
    out["Date"] = pd.to_datetime(out["Start date"], format="%b %d, %Y %I:%M %p")
    for col in col_map.values():
        if col in out.columns:
            out[col] = _parse_mwh(out[col])
    return out[["Date"] + list(col_map.values())]


def smard_clean_consumption(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the Actual_consumption SMARD export.

    Key columns:
      Grid_Load     — total electricity drawn from the grid (MWh/h)
      Residual_Load — portion that renewables cannot cover alone;
                      near zero = renewables meeting almost all demand
    """
    col_map = {
        "grid load [MWh] Calculated resolutions":                             "Grid_Load",
        "Grid load incl. hydro pumped storage [MWh] Calculated resolutions":  "Grid_Load_incl_Pumped",
        "Hydro pumped storage [MWh] Calculated resolutions":                  "Pumped_Demand",
        "Residual load [MWh] Calculated resolutions":                         "Residual_Load",
    }
    out = df.rename(columns=col_map).copy()
    out["Date"] = pd.to_datetime(out["Start date"], format="%b %d, %Y %I:%M %p")
    for col in col_map.values():
        if col in out.columns:
            out[col] = _parse_mwh(out[col])
    return out[["Date"] + [c for c in col_map.values() if c in out.columns]]


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  SMARD  —  FEATURE ENGINEERING & AGGREGATION
# ═══════════════════════════════════════════════════════════════════════════════

def smard_add_features(gen: pd.DataFrame) -> pd.DataFrame:
    """
    Add aggregate columns to the cleaned generation DataFrame.

    New columns:
      Total_Wind          = Wind_Onshore + Wind_Offshore
      Total_Renewable     = Solar + Wind + Biomass + Hydro + Other_Renewable
      Total_Fossil        = Lignite + Hard_Coal + Gas + Other_Conventional
      Total_Generation    = Total_Renewable + Total_Fossil + Pumped_Storage
      Renewable_Share_Pct = Total_Renewable / Total_Generation × 100
    """
    df = gen.copy()
    df["Total_Wind"]      = df["Wind_Onshore"] + df["Wind_Offshore"]
    df["Total_Renewable"] = df[["Solar","Total_Wind","Biomass","Hydro","Other_Renewable"]].sum(axis=1)
    df["Total_Fossil"]    = df[["Lignite","Hard_Coal","Gas","Other_Conventional"]].sum(axis=1)
    df["Total_Generation"]  = df["Total_Renewable"] + df["Total_Fossil"] + df["Pumped_Storage"]
    df["Renewable_Share_Pct"] = (df["Total_Renewable"] / df["Total_Generation"] * 100).fillna(0)
    return df


def smard_merge(gen: pd.DataFrame, con: pd.DataFrame) -> pd.DataFrame:
    """
    Merge generation and consumption DataFrames on Date.

    Adds:
      Coverage_Pct — how much of demand is met by domestic generation.
                     > 100% means Germany exports surplus electricity.
    """
    df = gen.merge(con, on="Date", how="inner")
    df["Coverage_Pct"] = df["Total_Generation"] / df["Grid_Load"] * 100
    df["Hour"]  = df["Date"].dt.hour
    df["Month"] = df["Date"].dt.strftime("%B")
    df["day"]   = df["Date"].dt.date
    return df


def smard_aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate hourly merged DataFrame to daily totals.
    Share and coverage are recalculated from daily sums (not averages of hourly %).
    """
    daily = df.groupby("day").sum(numeric_only=True).reset_index()
    daily["Date"]                = pd.to_datetime(daily["day"])
    daily["Renewable_Share_Pct"] = daily["Total_Renewable"] / daily["Total_Generation"] * 100
    daily["Coverage_Pct"]        = daily["Total_Generation"] / daily["Grid_Load"] * 100
    daily["Month"]               = daily["Date"].dt.strftime("%B")
    return daily


def smard_save(df: pd.DataFrame, file_name: str = "cleaned_smard.csv") -> str:
    """Save cleaned SMARD DataFrame to data/cleaned/ and return path."""
    path = os.path.join("data", "cleaned", file_name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return path


def smard_load(file_name: str = "cleaned_smard.csv") -> pd.DataFrame:
    """Load a saved cleaned SMARD CSV."""
    df = pd.read_csv(os.path.join("data", "cleaned", file_name), low_memory=False)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  SMARD + DWD  —  MERGE
# ═══════════════════════════════════════════════════════════════════════════════

def merge_energy_weather(smard: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """
    Merge hourly SMARD energy data with hourly DWD weather data on Date.

    Key details:
    - Strips tz info from weather before merging (both become naive, align correctly)
    - Filters weather to SMARD date range before merge — prevents the
      solar file's 2005-2026 history from diluting correlations with NaN rows
      outside the SMARD window (Apr-Jun 2025).
    """
    w = weather.copy()
    if hasattr(w["Date"], "dt") and w["Date"].dt.tz is not None:
        w["Date"] = w["Date"].dt.tz_localize(None)
    # Filter weather to SMARD date range so correlation matrix has no NaN columns
    w = w[(w["Date"] >= smard["Date"].min()) & (w["Date"] <= smard["Date"].max())]
    return smard.merge(w, on="Date", how="left")


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  SUMMARY & INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

def compute_summary(df: pd.DataFrame) -> dict:
    """Compute high-level KPIs from a merged hourly DataFrame."""
    total_gen  = df["Total_Generation"].sum() / 1e6
    total_ren  = df["Total_Renewable"].sum() / 1e6
    total_load = df["Grid_Load"].sum() / 1e6
    daily      = smard_aggregate_daily(df)

    return {
        "total_generation_twh":  round(total_gen, 2),
        "total_load_twh":        round(total_load, 2),
        "renewable_share_pct":   round(total_ren / total_gen * 100, 1),
        "solar_twh":             round(df["Solar"].sum() / 1e6, 2),
        "wind_twh":              round(df["Total_Wind"].sum() / 1e6, 2),
        "avg_coverage_pct":      round(daily["Coverage_Pct"].mean(), 1),
        "dunkelflaute_days":     int(len(daily[daily["Renewable_Share_Pct"] < 30])),
        "low_renewable_days":    int(len(daily[daily["Renewable_Share_Pct"] < 50])),
        "best_day":              daily.loc[daily["Renewable_Share_Pct"].idxmax()],
        "worst_day":             daily.loc[daily["Renewable_Share_Pct"].idxmin()],
    }


def summary_to_markdown(s: dict) -> str:
    """Format a summary dict as a Marimo-ready markdown string."""
    best  = s["best_day"]
    worst = s["worst_day"]
    return f"""
| Metric | Value | What it means |
|--------|-------|---------------|
| ⚡ Total generation | **{s['total_generation_twh']} TWh** | Electricity produced in the period |
| 🏠 Total demand | **{s['total_load_twh']} TWh** | Electricity consumed |
| 🌱 Renewable share | **{s['renewable_share_pct']}%** | Of every 3 units, ~2 came from renewables |
| 🔌 Avg. coverage | **{s['avg_coverage_pct']}%** | Germany generates ≈ what it consumes |
| ☀️ Solar output | **{s['solar_twh']} TWh** | From photovoltaic panels |
| 🌬️ Wind output | **{s['wind_twh']} TWh** | Onshore + offshore combined |
| 📅 Best renewable day | **{best['Date'].strftime('%b %d')} ({best['Renewable_Share_Pct']:.1f}%)** | Nearly fully green |
| 📅 Lowest renewable day | **{worst['Date'].strftime('%b %d')} ({worst['Renewable_Share_Pct']:.1f}%)** | Fossils had to step in |
| ⚠️ Low-renewable days (<50%) | **{s['low_renewable_days']} days** | When fossil backup was significant |
| 🌑 Dunkelflaute days (<30%) | **{s['dunkelflaute_days']} days** | True "dark doldrums" periods |
"""