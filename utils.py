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
        w = "✅" if results.get("wind")  else "❌"
        s = "✅" if results.get("sun")   else "❌"
        r = "✅" if results.get("solar") else "❌"
        lines.append(f"| {name} (`{sid}`) | {w} | {s} | {r} |")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  DWD CLEAN & BUILD
# ═══════════════════════════════════════════════════════════════════════════════

def _dwd_parse_wind(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="latin-1")
    df.columns = df.columns.str.strip()
    df = df[["MESS_DATUM", "F"]].copy()
    df.columns = ["ts", "wind_speed"]
    df["ts"] = pd.to_datetime(df["ts"].astype(str), format="%Y%m%d%H", errors="coerce")
    df["wind_speed"] = pd.to_numeric(df["wind_speed"], errors="coerce").replace(-999, float("nan"))
    return df.dropna(subset=["ts"]).set_index("ts")


def _dwd_parse_sun(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="latin-1")
    df.columns = df.columns.str.strip()
    df = df[["MESS_DATUM", "SD_SO"]].copy()
    df.columns = ["ts", "sunshine_min"]
    df["ts"] = pd.to_datetime(df["ts"].astype(str), format="%Y%m%d%H", errors="coerce")
    df["sunshine_min"] = pd.to_numeric(df["sunshine_min"], errors="coerce").replace(-999, float("nan"))
    return df.dropna(subset=["ts"]).set_index("ts")


def _dwd_parse_solar(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="latin-1")
    df.columns = df.columns.str.strip()
    df = df[["MESS_DATUM_WOZ", "FG_LBERG"]].copy()
    df.columns = ["ts", "global_radiation"]
    df["ts"] = pd.to_datetime(
        df["ts"].astype(str).str.strip(),
        format="%Y%m%d%H:%M",
        errors="coerce",
    )
    df["global_radiation"] = pd.to_numeric(df["global_radiation"], errors="coerce").replace(-999, float("nan"))
    return df.dropna(subset=["ts"]).set_index("ts")


def _dwd_load_station(station_id: str) -> pd.DataFrame:
    """Load and join wind + sun + solar for one station. Returns hourly indexed df."""
    def _find(suffix):
        matches = glob.glob(f"data/dwd/{station_id}_{suffix}/produkt_*.txt")
        return matches[0] if matches else None

    frames = []
    if p := _find("wind"):
        frames.append(_dwd_parse_wind(p))
    if p := _find("sun"):
        frames.append(_dwd_parse_sun(p))
    if p := _find("solar"):
        frames.append(_dwd_parse_solar(p))

    if not frames:
        return pd.DataFrame()

    out = frames[0]
    for f in frames[1:]:
        out = out.join(f, how="outer")
    return out


def dwd_build_national(stations: dict = None) -> pd.DataFrame:
    """
    Build a national hourly weather DataFrame by averaging across all stations.
    Returns a DataFrame with columns: Date, wind_speed, sunshine_min, global_radiation.
    """
    if stations is None:
        stations = DWD_STATIONS

    all_frames = []
    for sid in stations:
        df = _dwd_load_station(sid)
        if not df.empty:
            all_frames.append(df)

    if not all_frames:
        raise RuntimeError("No DWD station data found — run dwd_download_all() first.")

    combined = pd.concat(all_frames)
    national = combined.groupby(combined.index).mean(numeric_only=True)
    national.index = pd.to_datetime(national.index, utc=True).tz_convert("Europe/Berlin")
    national.index.name = "Date"          # name the index so reset_index produces "Date"
    national = national.reset_index()
    return national.sort_values("Date").reset_index(drop=True)


def dwd_save(df: pd.DataFrame, path: str = "data/dwd/weather_national.csv") -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return path


def dwd_load(path: str = "data/dwd/weather_national.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.tz_convert("Europe/Berlin")
    return df


def dwd_quality_report(df: pd.DataFrame) -> str:
    """Return a markdown table with missing-value stats for each weather column."""
    cols = ["wind_speed", "sunshine_min", "global_radiation"]
    lines = [
        "| Column | Available | Missing | Missing % | Status |",
        "|--------|-----------|---------|-----------|--------|",
    ]
    for c in cols:
        if c not in df.columns:
            continue
        n_miss = int(df[c].isna().sum())
        pct    = n_miss / len(df) * 100
        status = "✅ good" if pct < 5 else ("⚠️ watch" if pct < 10 else "❌ high")
        lines.append(f"| `{c}` | {len(df) - n_miss:,} | {n_miss:,} | {pct:.1f}% | {status} |")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  SMARD  —  API FETCH (generation + consumption combined)
# ═══════════════════════════════════════════════════════════════════════════════

def smard_fetch_api(start_date: str, end_date: str) -> "pd.DataFrame":
    """
    Fetch SMARD generation + consumption data directly from the SMARD API
    and return a single merged DataFrame identical to what the CSV pipeline
    produces — so all downstream functions (smard_add_features, smard_merge,
    smard_save, etc.) work without any changes.

    Args:
        start_date: "YYYY-MM-DD"  e.g. "2025-01-01"
        end_date:   "YYYY-MM-DD"  e.g. "2026-01-01"  (exclusive upper bound)

    Filter IDs (verified May 2026):
        1223  Photovoltaics (Solar)
        1224  Wind offshore
        1225  Wind onshore
        1226  Biomass
        1227  Hydropower
        1228  Other renewable
        1229  Nuclear
        1230  Lignite
        1231  Hard coal
        1232  Fossil gas
        4066  Hydro pumped storage
        1233  Other conventional
        5078  Grid load (consumption)
        5079  Grid load incl. pumped storage
        5097  Residual load
    """
    import requests as _req

    BASE = "https://www.smard.de/app/chart_data"
    REGION = "DE"
    RESOLUTION = "hour"

    # (filter_id, output_column_name, category)
    # IDs verified from working smard_filters dict (May 2026).
    # Nuclear excluded — Germany shut down last reactors April 2023,
    # API returns empty body for any period after that.
    SOURCES = [
        (4068, "Solar",              "gen"),
        (1225, "Wind_Offshore",      "gen"),
        (4067, "Wind_Onshore",       "gen"),
        (4066, "Biomass",            "gen"),
        (1226, "Hydro",              "gen"),
        (1228, "Other_Renewable",    "gen"),
        (1223, "Lignite",            "gen"),
        (4069, "Hard_Coal",          "gen"),
        (4071, "Gas",                "gen"),
        (4070, "Pumped_Storage",     "gen"),
        (1227, "Other_Conventional", "gen"),
        (5078, "Grid_Load",          "con"),
        (5097, "Residual_Load",      "con"),
    ]

    start_dt = pd.to_datetime(start_date)
    end_dt   = pd.to_datetime(end_date)

    def _fetch_series(filter_id: int, col_name: str) -> "pd.DataFrame | None":
        """
        Fetch one series. Returns None when:
          - API returns empty body (e.g. Nuclear after 2023 shutdown)
          - Response is not valid JSON (server error, rate limit)
          - No timestamps fall in the requested date range
        Caller fills the missing column with zeros so nothing downstream breaks.
        """
        index_url = f"{BASE}/{filter_id}/{REGION}/index_{RESOLUTION}.json"
        try:
            resp = _req.get(index_url, timeout=30)
            if not resp.content:
                return None                        # empty body → source not available
            index_data = resp.json()
        except Exception:
            return None                            # JSON decode / network error

        selected = [
            ts for ts in index_data.get("timestamps", [])
            if (pd.to_datetime(ts, unit="ms") >= start_dt - pd.Timedelta(days=10))
            and (pd.to_datetime(ts, unit="ms") <= end_dt)
        ]
        if not selected:
            return None                            # no data in this date window

        rows = []
        for ts in selected:
            url = f"{BASE}/{filter_id}/{REGION}/{filter_id}_{REGION}_{RESOLUTION}_{ts}.json"
            try:
                chunk = _req.get(url, timeout=30)
                if not chunk.content:
                    continue
                rows.extend(chunk.json().get("series", []))
            except Exception:
                continue                           # skip bad chunk, keep going

        if not rows:
            return None

        df = pd.DataFrame(rows, columns=["timestamp", col_name])
        df["Date"] = pd.to_datetime(df["timestamp"], unit="ms")
        df[col_name] = pd.to_numeric(df[col_name], errors="coerce").fillna(0)
        df = df[(df["Date"] >= start_dt) & (df["Date"] < end_dt)]
        return df[["Date", col_name]].reset_index(drop=True)

    # Fetch all series and merge on Date
    print("Fetching SMARD data from API...")
    merged = None
    skipped = []
    for fid, col, cat in SOURCES:
        print(f"  {col}...", end=" ", flush=True)
        series = _fetch_series(fid, col)
        if series is None:
            skipped.append(col)
            print("skipped (no data for this period)")
            continue
        merged = series if merged is None else merged.merge(series, on="Date", how="outer")
        print("ok")

    merged = merged.sort_values("Date").reset_index(drop=True)

    # Fill NaN gaps and add zero columns for any skipped sources
    for _, col, _ in SOURCES:
        if col not in merged.columns:
            merged[col] = 0          # skipped source → fill with 0
        else:
            merged[col] = merged[col].fillna(0)

    if skipped:
        print(f"  Note: {', '.join(skipped)} had no data — filled with 0.")
    print(f"Done — {len(merged):,} rows, {merged['Date'].min()} → {merged['Date'].max()}")
    return merged


# ═══════════════════════════════════════════════════════════════════════════════
# 4b. SMARD  —  SINGLE SERIES FETCH (for consumption breakdown, etc.)
# ═══════════════════════════════════════════════════════════════════════════════

def load_smard_series(
    filter_id: int,
    name: str,
    start_date: str,
    end_date: str,
    region: str = "DE",
    resolution: str = "hour",
) -> pd.DataFrame:
    """
    Fetch a single SMARD time series by filter_id.

    Returns a two-column DataFrame:
        "Start date"  — timestamp (datetime, timezone-naive)
        <name>        — values in MWh

    Uses the same SMARD chart_data API as smard_fetch_api.

    Consumption filter IDs (verified May 2026):
        410   Consumption (grid load)
        4359  Grid Load incl. Hydro Pumped Storage
        4387  Hydro Pumped Storage Consumption
        4355  Residual Load
    """
    import requests as _req

    BASE     = "https://www.smard.de/app/chart_data"
    start_dt = pd.to_datetime(start_date)
    end_dt   = pd.to_datetime(end_date)

    index_url = f"{BASE}/{filter_id}/{region}/index_{resolution}.json"
    try:
        resp = _req.get(index_url, timeout=30)
        resp.raise_for_status()
        index_data = resp.json()
    except Exception as e:
        raise RuntimeError(f"load_smard_series: index fetch failed for filter {filter_id}: {e}")

    selected = [
        ts for ts in index_data.get("timestamps", [])
        if (pd.to_datetime(ts, unit="ms") >= start_dt - pd.Timedelta(days=10))
        and (pd.to_datetime(ts, unit="ms") <= end_dt)
    ]

    rows = []
    for ts in selected:
        url = f"{BASE}/{filter_id}/{region}/{filter_id}_{region}_{resolution}_{ts}.json"
        try:
            chunk = _req.get(url, timeout=30)
            if chunk.content:
                rows.extend(chunk.json().get("series", []))
        except Exception:
            continue

    if not rows:
        return pd.DataFrame(columns=["Start date", name])

    df = pd.DataFrame(rows, columns=["Start date", name])
    df["Start date"] = pd.to_datetime(df["Start date"], unit="ms")
    df[name] = pd.to_numeric(df[name], errors="coerce").fillna(0)
    df = df[(df["Start date"] >= start_dt) & (df["Start date"] < end_dt)]
    return df.reset_index(drop=True)


def smard_fetch_consumption(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    Fetch all four SMARD consumption series and return a single merged DataFrame.

    Columns: Start date, Consumption, Grid Load incl. Hydro Pumped Storage,
             Hydro Pumped Storage Consumption, Residual Load

    Args:
        start_date: "YYYY-MM-DD"
        end_date:   "YYYY-MM-DD" (exclusive)
    """
    consumption_filters = {
        "Consumption":                          410,
        "Grid Load incl. Hydro Pumped Storage": 4359,
        "Hydro Pumped Storage Consumption":     4387,
        "Residual Load":                        4355,
    }

    dfs = []
    for series_name, filter_id in consumption_filters.items():
        print(f"  Loading {series_name}...")
        dfs.append(
            load_smard_series(
                filter_id=filter_id,
                name=series_name,
                start_date=start_date,
                end_date=end_date,
            )
        )

    merged = dfs[0]
    for df in dfs[1:]:
        merged = merged.merge(df, on="Start date", how="outer")

    merged = merged.sort_values("Start date").fillna(0).reset_index(drop=True)
    print(f"  Done — {len(merged):,} rows")
    return merged


# ═══════════════════════════════════════════════════════════════════════════════
# 4c. SMARD  —  GENERATION COLUMN GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

#: All generation source columns present in the smard_fetch_api output
RENEWABLE_COLS    = ["Solar", "Wind_Offshore", "Wind_Onshore", "Biomass", "Hydro", "Other_Renewable"]
CONVENTIONAL_COLS = ["Lignite", "Hard_Coal", "Gas", "Pumped_Storage", "Other_Conventional"]
ENERGY_COLS       = RENEWABLE_COLS + CONVENTIONAL_COLS


# ═══════════════════════════════════════════════════════════════════════════════
# 4d. SMARD  —  CSV PIPELINE (legacy / offline fallback)
# ═══════════════════════════════════════════════════════════════════════════════

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
# 4e. SMARD  —  MARKET TRADE / IMPORT-EXPORT DATA
# ═══════════════════════════════════════════════════════════════════════════════

def load_smard_market_trade(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Load German electricity import/export market data from SMARD.

    Returns hourly import/export totals and net trade balance.

    Columns added:
      Total_Export_MWh  — sum of all export columns
      Total_Import_MWh  — sum of all import columns, converted to positive values
      Net_Trade_MWh     — exports minus imports
                          positive = net exporter, negative = net importer
    """
    import requests as _req

    url = "https://www.smard.de/nip-download-manager/nip/download/market-data"

    start_ts = int(pd.to_datetime(start_date, utc=True).timestamp() * 1000)
    end_ts   = int(pd.to_datetime(end_date, utc=True).timestamp() * 1000)

    payload = {
        "request_form": [
            {
                "format": "CSV",
                "moduleIds": [
                    22004629, 22004722, 22004724, 22004404,
                    22004409, 22004545, 22004546, 22004548,
                    22004550, 22004551, 22004552, 22004405,
                    22004547, 22004403, 22004406, 22004407,
                    22004408, 22004410, 22004412, 22004549,
                    22004553, 22004998, 22004712,
                ],
                "region": "DE",
                "timestamp_from": start_ts,
                "timestamp_to": end_ts,
                "type": "discrete",
                "language": "en",
                "resolution": "hour",
            }
        ]
    }

    response = _req.post(url, json=payload, timeout=60)
    response.raise_for_status()

    df_trade = pd.read_csv(io.StringIO(response.text), sep=";")

    df_trade.columns = (
        df_trade.columns
        .str.replace(" Calculated resolutions", "", regex=False)
        .str.strip()
    )

    df_trade["Start date"] = pd.to_datetime(df_trade["Start date"])
    df_trade["End date"]   = pd.to_datetime(df_trade["End date"])

    for col in df_trade.columns:
        if col not in ["Start date", "End date"]:
            df_trade[col] = (
                df_trade[col]
                .astype(str)
                .str.replace(",", "", regex=False)
            )
            df_trade[col] = pd.to_numeric(df_trade[col], errors="coerce").fillna(0)

    export_cols = [
        col for col in df_trade.columns
        if "(export)" in col.lower()
    ]

    import_cols = [
        col for col in df_trade.columns
        if "(import)" in col.lower()
    ]

    # SMARD often stores imports as negative values. Convert them to positive
    # so import and export totals are easy to compare in charts.
    df_trade[import_cols] = df_trade[import_cols].abs()

    df_trade["Total_Export_MWh"] = df_trade[export_cols].sum(axis=1)
    df_trade["Total_Import_MWh"] = df_trade[import_cols].sum(axis=1)
    df_trade["Net_Trade_MWh"] = (
        df_trade["Total_Export_MWh"] - df_trade["Total_Import_MWh"]
    )

    return df_trade


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
    df["Total_Wind"]        = df["Wind_Onshore"] + df["Wind_Offshore"]
    df["Total_Renewable"]   = df[["Solar", "Total_Wind", "Biomass", "Hydro", "Other_Renewable"]].sum(axis=1)
    df["Total_Fossil"]      = df[["Lignite", "Hard_Coal", "Gas", "Other_Conventional"]].sum(axis=1)
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
    # 'day' may not exist if df came via merge_energy_weather instead of
    # smard_merge — derive it on the fly in that case.
    if "day" not in df.columns:
        df = df.copy()
        df["day"] = df["Date"].dt.date

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
      outside the SMARD window.
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


# ═══════════════════════════════════════════════════════════════════════════════
# 8.  MONTHLY ANALYSIS HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

# Canonical month ordering for full-year 2025 displays
MONTHS_2025 = [
    "Jan 2025", "Feb 2025", "Mar 2025", "Apr 2025",
    "May 2025", "Jun 2025", "Jul 2025", "Aug 2025",
    "Sep 2025", "Oct 2025", "Nov 2025", "Dec 2025",
]


def build_monthly_balance(
    df_generation: pd.DataFrame,
    df_consumption: pd.DataFrame,
    renewable_cols: list,
    date_col: str = "Start date",
) -> pd.DataFrame:
    """
    Build a monthly renewable-vs-demand balance table.

    Args:
        df_generation:  hourly generation DataFrame (contains renewable_cols)
        df_consumption: hourly consumption DataFrame (contains 'Consumption')
        renewable_cols: list of column names to sum as Total Renewable Generation
        date_col:       name of the timestamp column (default "Start date")

    Returns a DataFrame indexed by month (e.g. "Jan 2025") with columns:
        Total_Renewable_Generation_MWh, Total_Demand_MWh,
        Demand Met by Renewables [MWh], Remaining Demand [MWh],
        Renewable Share [%],
        Minimum Renewable Generation [MWh], Maximum Renewable Generation [MWh]
    """
    df = df_generation.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df["Month"]  = df[date_col].dt.strftime("%b %Y")
    df["Total Renewable Generation"] = df[renewable_cols].sum(axis=1)

    df = df.merge(
        df_consumption[[date_col, "Consumption"]],
        on=date_col,
        how="inner",
    )

    summary = df.groupby("Month").agg(
        Total_Renewable_Generation_MWh=("Total Renewable Generation", "sum"),
        Total_Demand_MWh=("Consumption", "sum"),
    )

    summary["Demand Met by Renewables [MWh]"] = summary[
        ["Total_Renewable_Generation_MWh", "Total_Demand_MWh"]
    ].min(axis=1)

    summary["Remaining Demand [MWh]"] = (
        summary["Total_Demand_MWh"] - summary["Demand Met by Renewables [MWh]"]
    )

    summary["Renewable Share [%]"] = (
        summary["Demand Met by Renewables [MWh]"] / summary["Total_Demand_MWh"] * 100
    )

    min_max = df.groupby("Month")["Total Renewable Generation"].agg(["min", "max"])
    summary["Minimum Renewable Generation [MWh]"] = min_max["min"]
    summary["Maximum Renewable Generation [MWh]"] = min_max["max"]

    # Reindex to canonical month order, keeping only months present in data
    present = [m for m in MONTHS_2025 if m in summary.index]
    summary = summary.reindex(present)

    return summary.round(3)


def build_monthly_generation(
    df_generation: pd.DataFrame,
    energy_cols: list,
    date_col: str = "Start date",
) -> pd.DataFrame:
    """
    Aggregate hourly generation to monthly totals per source.

    Returns a DataFrame indexed by month with one column per energy source.
    """
    df = df_generation.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df["Month"]  = df[date_col].dt.strftime("%b %Y")

    monthly = df.groupby("Month")[energy_cols].sum()

    present = [m for m in MONTHS_2025 if m in monthly.index]
    return monthly.reindex(present)


# ═══════════════════════════════════════════════════════════════════════════════
# 9.  SMARD  —  CROSS-BORDER TRADE
# ═══════════════════════════════════════════════════════════════════════════════

def load_smard_market_trade(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch hourly cross-border electricity trade data from the SMARD market-data API.

    Returns a DataFrame with per-country export/import columns plus:
        Total_Export_MWh, Total_Import_MWh, Net_Trade_MWh

    Positive Net_Trade_MWh → Germany is a net exporter that hour.
    Negative Net_Trade_MWh → Germany is a net importer that hour.

    Module IDs cover all bilateral flows with DE neighbours verified
    against SMARD market-data catalogue May 2026.
    """
    import io as _io
    import requests as _req

    url      = "https://www.smard.de/nip-download-manager/nip/download/market-data"
    start_ts = int(pd.to_datetime(start_date, utc=True).timestamp() * 1000)
    end_ts   = int(pd.to_datetime(end_date,   utc=True).timestamp() * 1000)

    payload = {
        "request_form": [
            {
                "format": "CSV",
                "moduleIds": [
                    22004629, 22004722, 22004724, 22004404,
                    22004409, 22004545, 22004546, 22004548,
                    22004550, 22004551, 22004552, 22004405,
                    22004547, 22004403, 22004406, 22004407,
                    22004408, 22004410, 22004412, 22004549,
                    22004553, 22004998, 22004712,
                ],
                "region": "DE",
                "timestamp_from": start_ts,
                "timestamp_to":   end_ts,
                "type": "discrete",
                "language": "en",
                "resolution": "hour",
            }
        ]
    }

    resp = _req.post(url, json=payload, timeout=60)
    resp.raise_for_status()

    df = pd.read_csv(_io.StringIO(resp.text), sep=";")
    df.columns = (
        df.columns
        .str.replace(" Calculated resolutions", "", regex=False)
        .str.strip()
    )

    df["Start date"] = pd.to_datetime(df["Start date"])
    df["End date"]   = pd.to_datetime(df["End date"])

    for col in df.columns:
        if col not in ("Start date", "End date"):
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "", regex=False),
                errors="coerce",
            ).fillna(0)

    export_cols = [c for c in df.columns if "(export)" in c.lower()]
    import_cols = [c for c in df.columns if "(import)" in c.lower()]

    # SMARD encodes imports as negative values — take absolute value
    df[import_cols] = df[import_cols].abs()

    df["Total_Export_MWh"] = df[export_cols].sum(axis=1)
    df["Total_Import_MWh"] = df[import_cols].sum(axis=1)
    df["Net_Trade_MWh"]    = df["Total_Export_MWh"] - df["Total_Import_MWh"]

    return df


def build_demand_balance_check(
    df_generation: pd.DataFrame,
    df_consumption: pd.DataFrame,
    df_trade: pd.DataFrame,
    renewable_cols: list,
    conventional_cols: list,
) -> pd.DataFrame:
    """
    Monthly system energy balance including cross-border trade.

    Accounting identity:
        Available = Generation (renewable + conventional) + Imports − Exports
        Balance   = Available − Consumption   (should be ≈ 0; ~2–3% residual is normal)

    Returns a monthly DataFrame with:
        Month, Total Renewable Generation, Total Conventional Generation,
        Consumption, Total_Export_MWh, Total_Import_MWh,
        Available_Energy_MWh, Balance_MWh, Demand_Met (bool)
    """
    _gen = df_generation.copy()
    _gen["Start date"] = pd.to_datetime(_gen["Date"])
    _gen["Total Renewable Generation"]    = _gen[renewable_cols].sum(axis=1)
    _gen["Total Conventional Generation"] = _gen[conventional_cols].sum(axis=1)
    _gen["Month"] = _gen["Start date"].dt.to_period("M").astype(str)
    _gen_m = (
        _gen.groupby("Month")[
            ["Total Renewable Generation", "Total Conventional Generation"]
        ]
        .sum()
        .reset_index()
    )

    _cons = df_consumption[["Start date", "Consumption"]].copy()
    _cons["Start date"] = pd.to_datetime(_cons["Start date"])
    _cons["Month"] = _cons["Start date"].dt.to_period("M").astype(str)
    _cons_m = _cons.groupby("Month")["Consumption"].sum().reset_index()

    _trade = df_trade.copy()
    _trade["Month"] = pd.to_datetime(_trade["Start date"]).dt.to_period("M").astype(str)
    _trade_m = (
        _trade.groupby("Month")[["Total_Export_MWh", "Total_Import_MWh"]]
        .sum()
        .reset_index()
    )

    out = _gen_m.merge(_cons_m, on="Month", how="inner")
    out = out.merge(_trade_m, on="Month", how="inner")

    out["Available_Energy_MWh"] = (
        out["Total Renewable Generation"]
        + out["Total Conventional Generation"]
        + out["Total_Import_MWh"]
        - out["Total_Export_MWh"]
    )
    out["Balance_MWh"] = out["Available_Energy_MWh"] - out["Consumption"]
    out["Demand_Met"]  = out["Balance_MWh"] >= 0

    return out


# ═══════════════════════════════════════════════════════════════════════════════
# 10.  WIND DIRECTION ANALYSIS
#      The D column is already present in the same produkt_ff_*.txt files
#      downloaded by dwd_download_all() — no extra download needed.
# ═══════════════════════════════════════════════════════════════════════════════

# Compass rose: 8 cardinal + intercardinal directions, each covering 45°
# Convention: 0°/360° = North, 90° = East, 180° = South, 270° = West
DIRECTION_BINS   = [0, 45, 90, 135, 180, 225, 270, 315, 360]
DIRECTION_LABELS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Prevailing westerlies: directions that bring Atlantic air → strongest winds in Germany
WESTERLY_RANGE = (225, 315)   # SW–W–NW band


def _dwd_parse_wind_with_direction(path: str) -> pd.DataFrame:
    """
    Parse a DWD wind file and return both F (speed, m/s) and D (direction, °).

    D = 0°   → variable / calm (special DWD code — treated as NaN)
    D = 360° → North (same as 0° meteorologically — kept as-is for binning)
    D = -999 → missing → NaN
    """
    df = pd.read_csv(path, sep=";", encoding="latin-1")
    df.columns = df.columns.str.strip()

    df = df[["STATIONS_ID", "MESS_DATUM", "F", "D"]].copy()
    df.columns = ["station_id", "ts", "wind_speed", "wind_dir"]

    df["ts"] = pd.to_datetime(
        df["ts"].astype(str), format="%Y%m%d%H", errors="coerce"
    )
    df["wind_speed"] = (
        pd.to_numeric(df["wind_speed"], errors="coerce").replace(-999, float("nan"))
    )
    df["wind_dir"] = (
        pd.to_numeric(df["wind_dir"], errors="coerce").replace(-999, float("nan"))
    )
    # D = 0 means "calm / variable" in DWD encoding — not a true direction
    df.loc[df["wind_dir"] == 0, "wind_dir"] = float("nan")

    return df.dropna(subset=["ts"])


def load_wind_direction_all_stations(stations: dict = None) -> pd.DataFrame:
    """
    Load wind speed + direction for all stations from already-downloaded wind files.

    Returns a long DataFrame with columns:
        ts, station_id, station_name, wind_speed, wind_dir,
        dir_bin (compass label: N/NE/E/SE/S/SW/W/NW),
        is_westerly (bool: True when direction is in the SW–W–NW band)

    Only rows where both F and D are valid are kept.
    """
    if stations is None:
        stations = DWD_STATIONS

    frames = []
    for sid, name in stations.items():
        matches = glob.glob(f"data/dwd/{sid}_wind/produkt_ff*.txt")
        if not matches:
            print(f"  ⚠️  No wind file found for {name} ({sid}) — skipping")
            continue
        df = _dwd_parse_wind_with_direction(matches[0])
        df["station_name"] = name
        frames.append(df)
        print(f"  ✅  {name} ({sid}): {len(df):,} rows")

    if not frames:
        raise RuntimeError(
            "No wind files found — run dwd_download_all() first, "
            "then re-run this cell."
        )

    out = pd.concat(frames, ignore_index=True)
    out = out.dropna(subset=["wind_speed", "wind_dir"])

    # 8-direction compass bin
    # pd.cut with right=False: [0,45) → N, [45,90) → NE, …, [315,360) → NW
    # 360° wraps back to North — remap after cut
    out["dir_bin"] = pd.cut(
        out["wind_dir"],
        bins=DIRECTION_BINS,
        labels=DIRECTION_LABELS,
        right=False,
        include_lowest=True,
    ).astype(str)
    # 360° lands in the last bin (315–360] → same as N
    out.loc[out["wind_dir"] == 360, "dir_bin"] = "N"

    # Westerly flag: SW / W / NW
    out["is_westerly"] = out["wind_dir"].between(
        WESTERLY_RANGE[0], WESTERLY_RANGE[1]
    )

    return out.sort_values(["ts", "station_id"]).reset_index(drop=True)


def wind_direction_station_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per-station, per-direction summary:
        count    — how many hours this direction was recorded
        freq_pct — percentage of all hours at this station
        mean_speed_ms — average wind speed when wind came from this direction
        mean_speed_kmh — same in km/h (× 3.6)

    Useful for comparing which directions dominate at each station.
    """
    total_per_station = df.groupby("station_name")["dir_bin"].count().rename("total")
    grouped = (
        df.groupby(["station_name", "dir_bin"])
        .agg(
            count=("wind_speed", "count"),
            mean_speed_ms=("wind_speed", "mean"),
        )
        .reset_index()
    )
    grouped = grouped.merge(total_per_station, on="station_name")
    grouped["freq_pct"]       = (grouped["count"] / grouped["total"] * 100).round(1)
    grouped["mean_speed_kmh"] = (grouped["mean_speed_ms"] * 3.6).round(2)
    grouped["mean_speed_ms"]  = grouped["mean_speed_ms"].round(2)

    # Sort by compass order within each station
    dir_order = {d: i for i, d in enumerate(DIRECTION_LABELS)}
    grouped["_sort"] = grouped["dir_bin"].map(dir_order)
    return (
        grouped.sort_values(["station_name", "_sort"])
        .drop(columns=["total", "_sort"])
        .reset_index(drop=True)
    )


def wind_direction_generation_correlation(
    df_wind_dir: pd.DataFrame,
    df_generation: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge wind direction data with SMARD generation and compute mean Total_Wind
    generation per compass direction per station.

    Args:
        df_wind_dir:   output of load_wind_direction_all_stations()
        df_generation: SMARD hourly DataFrame with "Date" and "Total_Wind" columns

    Returns a DataFrame with columns:
        station_name, dir_bin, mean_wind_gen_mwh, mean_wind_speed_ms,
        freq_pct, count
    """
    _gen = df_generation[["Date", "Total_Wind"]].copy()
    _gen["ts"] = pd.to_datetime(_gen["Date"]).dt.floor("h")

    _dir = df_wind_dir.copy()
    _dir["ts"] = pd.to_datetime(_dir["ts"]).dt.floor("h")

    merged = _dir.merge(_gen, on="ts", how="inner")

    result = (
        merged.groupby(["station_name", "dir_bin"])
        .agg(
            mean_wind_gen_mwh=("Total_Wind", "mean"),
            mean_wind_speed_ms=("wind_speed", "mean"),
            count=("wind_speed", "count"),
        )
        .reset_index()
    )

    total = merged.groupby("station_name")["dir_bin"].count().rename("total")
    result = result.merge(total, on="station_name")
    result["freq_pct"] = (result["count"] / result["total"] * 100).round(1)
    result["mean_wind_gen_mwh"] = result["mean_wind_gen_mwh"].round(1)
    result["mean_wind_speed_ms"] = result["mean_wind_speed_ms"].round(2)

    dir_order = {d: i for i, d in enumerate(DIRECTION_LABELS)}
    result["_sort"] = result["dir_bin"].map(dir_order)
    return (
        result.sort_values(["station_name", "_sort"])
        .drop(columns=["total", "_sort"])
        .reset_index(drop=True)
    )

# ═══════════════════════════════════════════════════════════════════════════════
# 11.  WIND DIRECTION — PRESENTATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def build_wind_rose_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build wind-direction frequency table for wind rose charts.

    Returns:
        dir_bin, count, freq_pct
    """
    out = (
        df.groupby("dir_bin")
        .size()
        .reset_index(name="count")
    )

    out["freq_pct"] = out["count"] / out["count"].sum() * 100

    dir_order = {d: i for i, d in enumerate(DIRECTION_LABELS)}
    out["_sort"] = out["dir_bin"].map(dir_order)

    return (
        out.sort_values("_sort")
        .drop(columns="_sort")
        .reset_index(drop=True)
    )


def build_direction_generation_summary(
    df_wind_dir: pd.DataFrame,
    df_generation: pd.DataFrame,
) -> pd.DataFrame:
    """
    Average wind generation by compass direction.

    Returns:
        dir_bin
        avg_wind_generation_mwh
        avg_wind_speed_ms
        freq_pct
    """

    _gen = df_generation[["Date", "Total_Wind", "Renewable_Share_Pct"]].copy()
    _gen["ts"] = pd.to_datetime(_gen["Date"]).dt.floor("h")

    _dir = df_wind_dir.copy()
    _dir["ts"] = pd.to_datetime(_dir["ts"]).dt.floor("h")

    merged = _dir.merge(_gen, on="ts", how="inner")

    out = (
        merged.groupby("dir_bin")
        .agg(
            avg_wind_generation_mwh=("Total_Wind", "mean"),
            avg_wind_speed_ms=("wind_speed", "mean"),
            avg_renewable_share_pct=("Renewable_Share_Pct", "mean"),
            count=("wind_speed", "count"),
        )
        .reset_index()
    )

    out["freq_pct"] = out["count"] / out["count"].sum() * 100

    out["avg_wind_generation_mwh"] = (
        out["avg_wind_generation_mwh"].round(1)
    )

    out["avg_wind_speed_ms"] = (
        out["avg_wind_speed_ms"].round(2)
    )

    out["avg_renewable_share_pct"] = (
        out["avg_renewable_share_pct"].round(1)
    )

    dir_order = {d: i for i, d in enumerate(DIRECTION_LABELS)}
    out["_sort"] = out["dir_bin"].map(dir_order)

    return (
        out.sort_values("_sort")
        .drop(columns="_sort")
        .reset_index(drop=True)
    )