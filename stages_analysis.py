import marimo

__generated_with = "0.23.0"
app = marimo.App(
    width="medium",
    layout_file="layouts/stages_analysis.slides.json",
)


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import plotly.express as px
    import matplotlib.pyplot as plt
    alt.data_transformers.enable("vegafusion")

    from utils import (
        DWD_STATIONS,
        dwd_download_all, dwd_download_summary,
        dwd_build_national, dwd_save, dwd_load, dwd_quality_report,
        smard_fetch_api, smard_fetch_consumption, load_smard_series,
        load_smard_market_trade,
        smard_add_features, smard_aggregate_daily,
        smard_save, smard_load,
        merge_energy_weather, compute_summary, summary_to_markdown,
        build_monthly_balance, build_monthly_generation,
        RENEWABLE_COLS, CONVENTIONAL_COLS, ENERGY_COLS,
        MONTHS_2025,
    )

    return (
        CONVENTIONAL_COLS,
        ENERGY_COLS,
        RENEWABLE_COLS,
        alt,
        build_monthly_balance,
        build_monthly_generation,
        compute_summary,
        dwd_build_national,
        dwd_download_all,
        dwd_download_summary,
        dwd_load,
        dwd_quality_report,
        dwd_save,
        load_smard_market_trade,
        merge_energy_weather,
        mo,
        pd,
        plt,
        px,
        smard_add_features,
        smard_aggregate_daily,
        smard_fetch_api,
        smard_fetch_consumption,
        smard_load,
        smard_save,
        summary_to_markdown,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # ⚡ STAGES Project
    ---

    > **The central question:** Can wind turbines, solar panels, and hydropower plants
    > cover Germany's entire electricity demand — and what happens when the weather turns bad?

    **Data sources:**
    - 🔌 [SMARD (Bundesnetzagentur)](https://www.smard.de) — hourly electricity generation & consumption
    - 🌦️ [DWD CDC Open Data](https://opendata.dwd.de/climate_environment/CDC/) — hourly weather at 6 stations across Germany

    ---
    ## Step 1 · Download weather data from DWD

    > The **Deutscher Wetterdienst (DWD)** is Germany's national weather service.
    > It publishes free hourly measurements from over 500 stations across Germany
    > through its **Climate Data Center (CDC)** open data portal.
    >
    > We download three variables from **6 stations** spread across Germany:
    >
    > | Variable | What it measures | Why we need it |
    > |----------|-----------------|----------------|
    > | Wind speed (m/s) | How fast the wind blows at 10 m height | Predicts wind power generation |
    > | Sunshine duration (min/hr) | Minutes of sunshine per hour | Predicts solar power generation |
    > | Global radiation (J/cm²) | Total solar energy at ground level | More precise solar predictor |
    >
    > The 6 stations were chosen to represent Germany's main renewable energy regions.
    > Station IDs are verified against the official DWD station description file.
    > **Note:** DWD IDs look random — `01975` is Hamburg, not "station 1975 of something."
    > Always verify against the official list, never guess.
    """)
    return


@app.cell
def _(mo):
    _station_info = [
        ("01975", "Hamburg-Fuhlsbüttel",  "North",   "Wind — near North Sea coast"),
        ("03379", "München",               "South",   "Solar — Bavaria's sunny region"),
        ("03987", "Potsdam",               "Central", "Central Brandenburg wind & sun"),
        ("01420", "Frankfurt/Main",        "Central", "Good all-round baseline station"),
        ("05792", "Zugspitze",             "Alpine",  "2962 m — extreme high-altitude wind"),
        ("02564", "Kiel-Holtenau",         "North",   "Baltic coast — offshore wind proxy"),
    ]
    _rows = "\n".join(
        f"| `{sid}` | {name} | {region} | {desc} |"
        for sid, name, region, desc in _station_info
    )

    mo.md(f"""
    ### Stations selected (IDs verified May 2026)

    | ID | Station | Region | Why chosen |
    |----|---------|--------|-----------|
    {_rows}
    """)
    return


@app.cell
def _(dwd_download_all, dwd_download_summary, mo):
    def _run_dwd_download():
        return dwd_download_all()

    _dl_status = _run_dwd_download()
    _dl_table  = dwd_download_summary(_dl_status)

    mo.md(f"""
    ### Download results

    {_dl_table}

    > ✅ = downloaded successfully · ❌ = not available (404) or no internet
    >
    > **Why might solar show ❌?**
    > The `solar/` folder only covers stations with pyranometer instruments —
    > not all 500+ DWD stations have one. Wind and sun data are far more widely available.
    """)
    return


@app.cell
def _(mo, pd):
    import glob
    def _load_preview(station_id="01975"):
        def _find(folder_suffix):
            matches = glob.glob(f"data/dwd/{station_id}_{folder_suffix}/produkt_*.txt")
            if not matches:
                raise FileNotFoundError(
                    f"No file found in data/dwd/{station_id}_{folder_suffix}/\n"
                    f"Run dwd_download.py first."
                )
            return matches[0]

        _w = pd.read_csv(_find("wind"),  sep=";", encoding="latin-1")
        _s = pd.read_csv(_find("sun"),   sep=";", encoding="latin-1")
        _r = pd.read_csv(_find("solar"), sep=";", encoding="latin-1")
        for _df in [_w, _s, _r]:
            _df.columns = _df.columns.str.strip()
        return _w, _s, _r

    def _df_to_md(df, n=4):
        _sub = df.head(n).copy()
        for col in _sub.columns:
            _sub[col] = _sub[col].astype(str).str.strip()
        _header = "| " + " | ".join(_sub.columns) + " |"
        _sep    = "|" + "|".join(["---"] * len(_sub.columns)) + "|"
        _rows   = "\n".join(
            "| " + " | ".join(str(v) for v in row) + " |"
            for row in _sub.itertuples(index=False)
        )
        return f"{_header}\n{_sep}\n{_rows}"

    _wind, _sun, _solar = _load_preview()
    _wind_tbl  = _df_to_md(_wind)
    _sun_tbl   = _df_to_md(_sun)
    _solar_tbl = _df_to_md(_solar)

    mo.md(f"""
    ---
    ## 🗂️ Raw data preview — Hamburg-Fuhlsbüttel (Station 01975)

    > Before we clean anything, let's look at what DWD actually gives us.
    > Below are the first few rows of each file, exactly as downloaded.
    > Each table has its own column structure — understanding these is essential
    > before writing any cleaning code.

    ---

    ### 💨 Wind file — `produkt_ff_stunde_...txt`

    {_wind_tbl}

    | Column | What it means |
    |--------|--------------|
    | `STATIONS_ID` | DWD station number — `1975` = Hamburg-Fuhlsbüttel |
    | `MESS_DATUM` | Timestamp in **YYYYMMDDHH** format (e.g. `2024110600` = Nov 6 2024, 00:00) |
    | `QN_3` | Quality level (10 = passed all automated checks, 1 = only basic check) |
    | `F` | **Mean wind speed in m/s** — this is the key column we use |
    | `D` | Wind direction in degrees (110° = roughly southeast) |
    | `eor` | End-of-record marker — always ignore this column |

    > ⚠️ **Missing values** are coded as `-999` in the `F` column.
    > We replace these with `NaN` during cleaning so they don't corrupt calculations.

    ---

    ### ☀️ Sunshine file — `produkt_sd_stunde_...txt`

    {_sun_tbl}

    | Column | What it means |
    |--------|--------------|
    | `STATIONS_ID` | Station number |
    | `MESS_DATUM` | Timestamp — same **YYYYMMDDHH** format as wind |
    | `QN_7` | Quality level for sunshine measurements |
    | `SD_SO` | **Sunshine duration in minutes per hour** (range: 0–60) |
    | `eor` | End-of-record marker — ignore |

    > A value of `60.0` means the full hour was sunny.
    > A value of `0.0` means no sunshine at all (night or fully overcast).
    > This column directly predicts how much solar energy was generated that hour.

    ---

    ### 🌞 Solar radiation file — `produkt_st_stunde_...txt`

    {_solar_tbl}

    | Column | What it means |
    |--------|--------------|
    | `STATIONS_ID` | Station number |
    | `MESS_DATUM` | Timestamp in **YYYYMMDDhh:mm** format ← different from wind/sun! |
    | `QN_592` | Quality level for radiation measurements |
    | `ATMO_LBERG` | Atmospheric radiation (downward longwave) in J/cm² |
    | `FD_LBERG` | Diffuse solar radiation (scattered from clouds/sky) in J/cm² |
    | `FG_LBERG` | **Global radiation (total incoming solar energy) in J/cm²** — key column |
    | `SD_LBERG` | Sunshine duration (minutes) measured at this radiation station |
    | `ZENIT` | Solar zenith angle in degrees (0° = sun directly overhead) |
    | `MESS_DATUM_WOZ` | Timestamp in local solar time — we use this for cleaning |
    | `eor` | End-of-record marker — ignore |

    > ⚠️ **The solar timestamp is different!**
    > It uses format `2005010100:23` (YYYYMMDD**hh:mm**) instead of `YYYYMMDDHH`.
    > This is why the cleaning code needs special handling for this file —
    > using the wrong format causes the `ValueError: unconverted data remains` error.
    > We fix this by parsing `MESS_DATUM_WOZ` with `format='%Y%m%d%H:%M'` instead.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2 · Clean & average the weather data

    > Raw DWD files have quirks that must be fixed before analysis:
    >
    > | Problem | How we fix it |
    > |---------|--------------|
    > | Missing values coded as **-999** | Replace with `NaN`  never treat as real data |
    > | Timestamps in **UTC** | Convert to `Europe/Berlin` to align with SMARD |
    > | Trailing semicolons in CSV | Handled automatically by pandas `sep=";"` |
    > | Column name whitespace | Strip with `.str.strip()` |
    >
    > After cleaning each station, we **average across all 6** to get one national
    > weather signal per hour. This is a simplification  a full analysis would
    > weight stations by the installed renewable capacity in their region.
    >
    > All of this logic lives in `utils.py`  the cell below calls a single function.
    """)
    return


@app.cell
def _(dwd_build_national, dwd_quality_report, dwd_save, mo):
    def _run_dwd_clean():
        _df = dwd_build_national()
        dwd_save(_df)
        return _df

    _weather = _run_dwd_clean()
    _qr      = dwd_quality_report(_weather)

    mo.md(f"""
    ### Weather data quality report

    {_qr}

    > **Missing %** below 5% is acceptable.
    > Above 10% means that variable should be used with caution or excluded.
    >
    > **Date range:** {_weather["Date"].min()} → {_weather["Date"].max()}
    > · **Rows:** {len(_weather):,} hourly observations
    > · **Saved to:** `data/dwd/weather_national.csv`
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## Step 3 · Load & clean SMARD electricity data

    > **SMARD** is the official German electricity market platform run by the
    > Bundesnetzagentur (Federal Network Agency).
    > It publishes real-time and historical data on what every power plant in Germany produces.
    >
    > We fetch data **directly from the SMARD API** — no CSV files needed.
    > The API returns exactly the same hourly data as the website download:
    >
    > | Data | What it contains |
    > |------|-----------------|
    > | Generation by source | Hourly MWh: solar, wind on/offshore, biomass, hydro, gas, coal… |
    > | Grid consumption | Hourly grid load and residual load |
    >
    > **What is residual load?**
    > Residual load = Grid demand − Renewable generation.
    > When this is low, renewables are doing the heavy lifting.
    > When it goes **negative**, renewables produce more than Germany needs — surplus is exported.
    """)
    return


@app.cell
def _(mo, smard_add_features, smard_fetch_api, smard_save):

    # ── change only these two lines to update the whole analysis ──────────
    START_DATE = "2025-01-01"
    END_DATE   = "2026-01-01"   # exclusive (up to but not including this date)
    SAVE_FILE  = "cleaned_smard_2025.csv"
    # ──────────────────────────────────────────────────────────────────────

    def _run_smard():
        _raw = smard_fetch_api(START_DATE, END_DATE)   # live fetch from SMARD API
        _df  = smard_add_features(_raw)                # adds Total_Wind, Total_Renewable etc.
        smard_save(_df, SAVE_FILE)
        return _df

    _smard = _run_smard()

    mo.md(f"""
    ### SMARD generation data loaded via API

    | | Value |
    |-|-------|
    | Hourly rows | {len(_smard):,} |
    | Date range | {_smard["Date"].min().strftime("%b %d, %Y")} → {_smard["Date"].max().strftime("%b %d, %Y")} |
    | Sources tracked | Solar, Wind (on+offshore), Biomass, Hydro, Lignite, Hard Coal, Gas |
    | Overall renewable share | **{_smard["Total_Renewable"].sum() / _smard["Total_Generation"].sum() * 100:.1f}%** |

    > Fetched live from the SMARD API — no CSV files needed.
    > Saved to `data/cleaned/{SAVE_FILE}` so all chart cells load instantly on re-run.
    > To change the time period, edit `START_DATE` and `END_DATE` at the top of this cell only.
    """)
    return END_DATE, START_DATE


@app.cell
def _(END_DATE, START_DATE, mo, smard_fetch_consumption):
    # ── Fetch all four consumption series from SMARD API ──────────────────
    print("Fetching SMARD consumption data...")
    df_smard_consumption = smard_fetch_consumption(START_DATE, END_DATE)

    mo.md(f"""
    ### ⚡ Consumption data loaded

    | Series | Rows | Total [TWh] |
    |--------|------|-------------|
    | `Consumption` | {df_smard_consumption["Consumption"].count():,} | {df_smard_consumption["Consumption"].sum() / 1e6:.2f} |
    | `Grid Load incl. Hydro Pumped Storage` | {df_smard_consumption["Grid Load incl. Hydro Pumped Storage"].count():,} | {df_smard_consumption["Grid Load incl. Hydro Pumped Storage"].sum() / 1e6:.2f} |
    | `Hydro Pumped Storage Consumption` | {df_smard_consumption["Hydro Pumped Storage Consumption"].count():,} | {df_smard_consumption["Hydro Pumped Storage Consumption"].sum() / 1e6:.2f} |
    | `Residual Load` | {df_smard_consumption["Residual Load"].count():,} | {df_smard_consumption["Residual Load"].sum() / 1e6:.2f} |

    > **{len(df_smard_consumption):,} hourly rows** ·
    > {df_smard_consumption["Start date"].min().strftime("%b %d, %Y")} → {df_smard_consumption["Start date"].max().strftime("%b %d, %Y")}
    >
    > `Residual Load` = Grid Load − Total Renewable Generation.
    > When negative, renewables overproduce and Germany exports surplus.
    """)
    return (df_smard_consumption,)


@app.cell
def _(mo, smard_load):
    def _smard_preview():
        _df = smard_load("cleaned_smard_2025.csv")

        # ── shape & date range ────────────────────────────────────────
        _rows, _cols = _df.shape
        _date_min = _df["Date"].min().strftime("%b %d, %Y")
        _date_max = _df["Date"].max().strftime("%b %d, %Y")

        # ── sample rows table (first 5) ───────────────────────────────
        _show_cols = [
            "Date", "Solar", "Wind_Offshore", "Wind_Onshore",
            "Biomass", "Hydro", "Lignite", "Hard_Coal", "Gas",
            "Total_Renewable", "Total_Fossil", "Total_Generation",
            "Grid_Load", "Residual_Load", "Renewable_Share_Pct",
        ]
        _show = [c for c in _show_cols if c in _df.columns]
        _sub  = _df[_show].head(5).copy()
        _sub["Date"] = _sub["Date"].astype(str).str[:16]
        for c in _show[1:]:
            _sub[c] = _sub[c].apply(
                lambda x: f"{float(x):,.1f}" if str(x) != "nan" else "—"
            )

        _hdr  = "| " + " | ".join(_show) + " |"
        _sep  = "|" + "|".join(["---"] * len(_show)) + "|"
        _rows_md = "\n".join(
            "| " + " | ".join(str(v) for v in row) + " |"
            for row in _sub.itertuples(index=False)
        )

        # ── column summary (min / max / mean for key columns) ─────────
        _key = ["Solar", "Wind_Offshore", "Wind_Onshore", "Total_Renewable",
                "Total_Fossil", "Grid_Load", "Residual_Load", "Renewable_Share_Pct"]
        _key = [c for c in _key if c in _df.columns]
        _stats_lines = []
        for c in _key:
            _mn  = _df[c].min()
            _mx  = _df[c].max()
            _avg = _df[c].mean()
            _stats_lines.append(
                f"| `{c}` | {_mn:,.1f} | {_avg:,.1f} | {_mx:,.1f} |"
            )
        _stats_md = "\n".join(_stats_lines)

        return _rows, _cols, _date_min, _date_max, _hdr, _sep, _rows_md, _stats_md

    (_n_rows, _n_cols, _d_min, _d_max,
     _hdr, _sep, _rows_md, _stats_md) = _smard_preview()

    mo.md(f"""
    ---
    ### 📋 SMARD data — what it looks like

    > **{_n_rows:,} rows · {_n_cols} columns** · {_d_min} → {_d_max}
    > Each row = one hour of electricity data for all of Germany.

    **First 5 rows:**

    {_hdr}
    {_sep}
    {_rows_md}

    ---

    **Column statistics (hourly values in MWh, share in %):**

    | Column | Min | Mean | Max |
    |--------|-----|------|-----|
    {_stats_md}

    > All generation values are in **MWh per hour**.
    > `Renewable_Share_Pct` = Total\\_Renewable ÷ Total\\_Generation × 100.
    > `Residual_Load` = Grid\\_Load − Total\\_Renewable — when negative, renewables overproduce.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## Step 4 · Merge energy data with weather data

    > Now we combine SMARD and DWD into one dataset.
    > Each row will have: date/hour · energy by source · grid demand · wind speed · sunshine.
    >
    > **The critical timezone issue:**
    > - SMARD timestamps = **CET/CEST** (Berlin local time, UTC+1 or +2)
    > - DWD timestamps = **UTC** (always 1–2 hours behind Berlin)
    >
    > Without fixing this, solar generation at noon appears to match weather at 10am.
    > Correlations look weaker than reality. `utils.merge_energy_weather()` strips
    > the timezone from DWD before merging so both datasets share the same clock.
    """)
    return


@app.cell
def _(
    compute_summary,
    dwd_load,
    merge_energy_weather,
    mo,
    smard_load,
    summary_to_markdown,
):

    def _build_combined():
        _s = smard_load("cleaned_smard_2025.csv")
        _w = dwd_load()
        return merge_energy_weather(_s, _w)

    _combined  = _build_combined()
    _summary   = compute_summary(_combined)
    _kpi_table = summary_to_markdown(_summary)

    mo.md(f"""
    ### Key findings — Full Year 2025

    {_kpi_table}

    > This table is the **executive summary** of the entire dataset.
    > Every chart below explores one of these numbers in more detail.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 📊 Chart 1 · Solar ☀️ vs. Wind 🌬️ — the two workhorses

    > Solar grows predictably: longer days → more energy (visible Jan → Jun → Dec).
    > You can clearly see the seasonal arc of solar across the year.
    > Wind follows no seasonal pattern — it comes in unpredictable bursts and lulls.
    >
    > This **complementary behaviour** is actually helpful for grid stability.
    > The dangerous days are when **both** are weak simultaneously — that is the *Dunkelflaute*.
    """)
    return


@app.cell
def _(alt, pd, smard_aggregate_daily, smard_load):
    def _chart_solar_wind():
        _d = smard_aggregate_daily(smard_load("cleaned_smard_2025.csv"))
        _m = pd.melt(
            _d[["Date","Solar","Total_Wind"]].assign(
                Solar=_d["Solar"]/1000,
                Total_Wind=_d["Total_Wind"]/1000,
            ),
            id_vars="Date", var_name="Source", value_name="GWh"
        )
        _m["Source"] = _m["Source"].map({"Solar":"☀️ Solar","Total_Wind":"🌬️ Wind"})
        return alt.Chart(_m).mark_area(opacity=0.65).encode(
            x=alt.X("Date:T", axis=alt.Axis(format="%b %d", labelAngle=-45)),
            y=alt.Y("GWh:Q", title="Daily Generation (GWh)", stack=None),
            color=alt.Color("Source:N",
                scale=alt.Scale(domain=["☀️ Solar","🌬️ Wind"], range=["#F59E0B","#3B82F6"])
            ),
            tooltip=[
                alt.Tooltip("Date:T", format="%B %d"),
                alt.Tooltip("Source:N"),
                alt.Tooltip("GWh:Q", format=".0f"),
            ]
        ).properties(
            title="Solar vs. Wind — Daily Generation overlaid (Full Year 2025)",
            width=900, height=300
        ).interactive()

    _chart_solar_wind()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 📊 Chart 2 · Renewable risk days — when did the grid struggle?

    > A **Dunkelflaute** (German: "dark doldrums") is several consecutive days
    > with both low wind and low sunshine — the worst case for a renewable grid.
    >
    > Traffic-light colouring for every day:
    > 🟢 **≥60%** renewable — comfortable · 🟡 **50–60%** — watch zone · 🔴 **<50%** — significant fossil use
    >
    > The dashed red line marks the 50% threshold.
    """)
    return


@app.cell
def _(alt, smard_aggregate_daily, smard_load):
    def _chart_risk():
        _d = smard_aggregate_daily(smard_load("cleaned_smard_2025.csv"))
        _d = _d.copy()
        _d["Risk"] = "🟢 Normal (≥60%)"
        _d.loc[_d["Renewable_Share_Pct"] < 60, "Risk"] = "🟡 Watch zone (50–60%)"
        _d.loc[_d["Renewable_Share_Pct"] < 50, "Risk"] = "🔴 Low renewable (<50%)"

        _bars = alt.Chart(_d).mark_bar(size=6).encode(
            x=alt.X("Date:T", axis=alt.Axis(format="%b %d", labelAngle=-45)),
            y=alt.Y("Renewable_Share_Pct:Q",
                    title="Daily renewable share (%)",
                    scale=alt.Scale(domain=[0,100])),
            color=alt.Color("Risk:N",
                scale=alt.Scale(
                    domain=["🟢 Normal (≥60%)","🟡 Watch zone (50–60%)","🔴 Low renewable (<50%)"],
                    range=["#22C55E","#F59E0B","#EF4444"]
                ),
                legend=alt.Legend(title="")
            ),
            tooltip=[
                alt.Tooltip("Date:T", format="%B %d, %Y"),
                alt.Tooltip("Renewable_Share_Pct:Q", title="Renewable %", format=".1f"),
                alt.Tooltip("Risk:N"),
            ]
        ).properties(
            title="Daily Renewable Share — Risk Assessment (Full Year 2025)",
            width=900, height=320
        ).interactive()

        _rule = alt.Chart(alt.Data(values=[{"y": 50}])).mark_rule(
            color="red", strokeDash=[6,3], strokeWidth=1.5
        ).encode(y="y:Q")

        return _bars + _rule

    _chart_risk()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 📊 Chart 3 · Renewable Energy Generation — Hourly Time Series

    > Interactive visualization of hourly renewable electricity generation
    > for the **full year 2025**.
    >
    > Sources shown:
    >
    > | Source | What it is |
    > |--------|-----------|
    > | **Biomass** | Burning organic material — stable, dispatchable, 24/7 |
    > | **Hydropower** | Run-of-river plants — steady but weather-dependent |
    > | **Wind Offshore** | North Sea & Baltic wind farms — highest capacity factor |
    > | **Wind Onshore** | Land-based wind — more variable, widely distributed |
    > | **Solar** | Photovoltaic panels — strong seasonal arc, zero at night |
    > | **Other Renewable** | Geothermal, tidal, landfill gas, etc. |
    >
    > Use the **range slider** below the chart to zoom into any period.
    """)
    return


@app.cell
def _(RENEWABLE_COLS, px, smard_load):
    def _chart_renewables_interactive():
        _df = smard_load("cleaned_smard_2025.csv")

        # Rename to friendly display names for the legend
        _col_labels = {
            "Solar":          "Solar",
            "Wind_Offshore":  "Wind Offshore",
            "Wind_Onshore":   "Wind Onshore",
            "Biomass":        "Biomass",
            "Hydro":          "Hydropower",
            "Other_Renewable":"Other Renewable",
        }
        _display_cols = [c for c in RENEWABLE_COLS if c in _df.columns]
        _df_plot = _df[["Date"] + _display_cols].copy()
        _df_plot = _df_plot.rename(columns=_col_labels)
        _friendly_cols = [_col_labels.get(c, c) for c in _display_cols]

        _long = _df_plot.melt(
            id_vars="Date",
            value_vars=_friendly_cols,
            var_name="Source",
            value_name="Production [MWh]",
        )

        _fig = px.line(
            _long,
            x="Date",
            y="Production [MWh]",
            color="Source",
            title="Renewable Energy Sources — Full Year 2025",
            color_discrete_map={
                "Solar":          "#F59E0B",
                "Wind Offshore":  "#1D4ED8",
                "Wind Onshore":   "#60A5FA",
                "Biomass":        "#16A34A",
                "Hydropower":     "#0EA5E9",
                "Other Renewable":"#8B5CF6",
            },
        )
        _fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
                type="date",
                title="",
            ),
            yaxis_title="Production [MWh]",
            height=520,
            legend_title="Source",
            hovermode="x unified",
        )
        _fig.update_traces(
            hovertemplate="<b>%{fullData.name}</b><br>Date=%{x}<br>Energy=%{y:,.0f} MWh<extra></extra>"
        )
        return _fig

    _chart_renewables_interactive()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 📊 Chart 4 · Conventional Energy Generation — Hourly Time Series

    > Interactive visualization of hourly **conventional** (fossil + dispatchable)
    > electricity generation for the **full year 2025**.
    >
    > Sources shown:
    >
    > | Source | What it is |
    > |--------|-----------|
    > | **Lignite** | Brown coal — Germany's cheapest but most carbon-intensive source |
    > | **Hard Coal** | Black coal — somewhat cleaner, partly imported |
    > | **Fossil Gas** | Natural gas peakers — fast to ramp, used for balancing |
    > | **Hydro Pumped Storage** | Water pumped uphill when surplus exists, released when needed |
    > | **Other Conventional** | Oil, waste incineration, emergency reserves |
    >
    > Notice how conventional generation **mirrors** the renewable signal — it fills the gaps
    > when wind and solar are low. This is the backup role that gas and coal still play.
    """)
    return


@app.cell
def _(CONVENTIONAL_COLS, px, smard_load):
    def _chart_conventional_interactive():
        _df = smard_load("cleaned_smard_2025.csv")

        _col_labels = {
            "Lignite":           "Lignite",
            "Hard_Coal":         "Hard Coal",
            "Gas":               "Fossil Gas",
            "Pumped_Storage":    "Hydro Pumped Storage",
            "Other_Conventional":"Other Conventional",
        }
        _display_cols = [c for c in CONVENTIONAL_COLS if c in _df.columns]
        _df_plot = _df[["Date"] + _display_cols].copy()
        _df_plot = _df_plot.rename(columns=_col_labels)
        _friendly_cols = [_col_labels.get(c, c) for c in _display_cols]

        _long = _df_plot.melt(
            id_vars="Date",
            value_vars=_friendly_cols,
            var_name="Source",
            value_name="Production [MWh]",
        )

        _fig = px.line(
            _long,
            x="Date",
            y="Production [MWh]",
            color="Source",
            title="Conventional Energy Sources — Full Year 2025",
            color_discrete_map={
                "Lignite":             "#78350F",
                "Hard Coal":           "#44403C",
                "Fossil Gas":          "#EF4444",
                "Hydro Pumped Storage":"#0EA5E9",
                "Other Conventional":  "#9CA3AF",
            },
        )
        _fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
                type="date",
                title="",
            ),
            yaxis_title="Production [MWh]",
            height=520,
            legend_title="Source",
            hovermode="x unified",
        )
        _fig.update_traces(
            hovertemplate="<b>%{fullData.name}</b><br>Date=%{x}<br>Energy=%{y:,.0f} MWh<extra></extra>"
        )
        return _fig

    _chart_conventional_interactive()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 📊 Chart 5 · Renewable vs. Conventional Generation vs. Electricity Demand

    > This chart answers the big question directly:
    > **How close is Germany to running on renewables alone?**
    >
    > - 🟢 **Total Renewable Generation** — everything from sun, wind, biomass, hydro
    > - 🟤 **Total Conventional Generation** — fossil fuels + pumped storage dispatch
    > - 🔵 **Consumption** — actual national electricity demand
    >
    > When the green line is **above** the blue line, renewables alone cover all demand.
    > The gap between green and blue, when green is below, shows how much conventional
    > generation is still needed.
    """)
    return


@app.cell
def _(CONVENTIONAL_COLS, RENEWABLE_COLS, df_smard_consumption, px, smard_load):
    def _chart_compare_interactive():
        _df = smard_load("cleaned_smard_2025.csv")

        _df["Total Renewable Generation"]   = _df[RENEWABLE_COLS].sum(axis=1)
        _df["Total Conventional Generation"] = _df[CONVENTIONAL_COLS].sum(axis=1)

        # Align on Date — consumption uses "Start date", generation uses "Date"
        _cons = df_smard_consumption[["Start date", "Consumption"]].copy()
        _cons = _cons.rename(columns={"Start date": "Date"})
        _cons["Date"] = _df["Date"].iloc[:len(_cons)].values  # align dtype

        _merged = _df.merge(_cons, on="Date", how="inner")

        _long = _merged.melt(
            id_vars="Date",
            value_vars=[
                "Total Renewable Generation",
                "Total Conventional Generation",
                "Consumption",
            ],
            var_name="Category",
            value_name="Energy [MWh]",
        )

        _fig = px.line(
            _long,
            x="Date",
            y="Energy [MWh]",
            color="Category",
            title="Renewable vs. Conventional Generation vs. Electricity Demand — Full Year 2025",
            color_discrete_map={
                "Total Renewable Generation":   "#22C55E",
                "Total Conventional Generation":"#78350F",
                "Consumption":                  "#3B82F6",
            },
        )
        _fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
                type="date",
                title="",
            ),
            yaxis_title="Energy [MWh]",
            height=560,
            legend_title="",
            hovermode="x unified",
        )
        _fig.update_traces(
            hovertemplate="<b>%{fullData.name}</b><br>Date=%{x}<br>Energy=%{y:,.0f} MWh<extra></extra>"
        )
        return _fig

    _chart_compare_interactive()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 📊 Chart 6 · Monthly Renewable Energy Balance — Full Year 2025

    > This table evaluates how well renewables cover Germany's electricity demand
    > **month by month** across the entire year.
    >
    > | Column | What it means |
    > |--------|--------------|
    > | **Total Renewable Generation** | All solar + wind + biomass + hydro that month |
    > | **Total Demand** | National electricity consumption |
    > | **Demand Met by Renewables** | min(generation, demand) — how much demand renewables actually covered |
    > | **Remaining Demand** | What still had to come from fossil fuels or imports |
    > | **Renewable Share %** | Coverage ratio — 100% = fully renewable month |
    > | **Min / Max Renewable** | Hourly extremes within the month |
    >
    > Summer months show high solar → high share.
    > Winter months show the challenge: less sun, variable wind, high heating demand.
    """)
    return


@app.cell
def _(
    RENEWABLE_COLS,
    build_monthly_balance,
    df_smard_consumption,
    mo,
    smard_load,
):
    def _monthly_balance_table():
        _df_gen = smard_load("cleaned_smard_2025.csv")

        # Rename "Date" → "Start date" so build_monthly_balance can join on it
        _df_gen_renamed = _df_gen.rename(columns={"Date": "Start date"})

        _balance = build_monthly_balance(
            df_generation=_df_gen_renamed,
            df_consumption=df_smard_consumption,
            renewable_cols=RENEWABLE_COLS,
            date_col="Start date",
        )

        # Format for display
        _lines = []
        for _month, _row in _balance.iterrows():
            _lines.append(
                f"| {_month} "
                f"| {_row['Total_Renewable_Generation_MWh']:>14,.0f} "
                f"| {_row['Total_Demand_MWh']:>14,.0f} "
                f"| {_row['Demand Met by Renewables [MWh]']:>14,.0f} "
                f"| {_row['Remaining Demand [MWh]']:>14,.0f} "
                f"| {_row['Renewable Share [%]']:>6.1f}% "
                f"| {_row['Minimum Renewable Generation [MWh]']:>10,.0f} "
                f"| {_row['Maximum Renewable Generation [MWh]']:>10,.0f} |"
            )

        _header = (
            "| Month "
            "| Total Renewable Gen [MWh] "
            "| Total Demand [MWh] "
            "| Demand Met [MWh] "
            "| Remaining [MWh] "
            "| Share "
            "| Min Gen [MWh] "
            "| Max Gen [MWh] |"
        )
        _sep = "|-------|--------------------------|--------------------|--------------------|-----------------|--------|---------------|---------------|"

        return _header + "\n" + _sep + "\n" + "\n".join(_lines)

    _table_md = _monthly_balance_table()

    mo.md(f"""
    ### Monthly Renewable Energy Balance — Full Year 2025

    {_table_md}

    > **Demand Met** = min(Total Renewable Generation, Total Demand) per month.
    > When renewable generation exceeds demand, the surplus goes to exports or pumped storage.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 📊 Chart 7 · Monthly Electricity Generation by Energy Source

    > Each bar = one month. **Stacked** to show how each source contributed to
    > the total generation mix across the full year.
    >
    > This chart makes the **seasonal story** of the German grid immediately visible:
    > - Solar (yellow) dominates spring and summer
    > - Wind (blue) is the backbone in autumn and winter
    > - Lignite and gas (brown/red) fill the gaps year-round
    > - Biomass (green) stays flat — it is the only truly dispatchable renewable
    """)
    return


@app.cell
def _(ENERGY_COLS, build_monthly_generation, plt, smard_load):
    def _chart_monthly_stacked():
        _df_gen = smard_load("cleaned_smard_2025.csv")
        _df_gen_renamed = _df_gen.rename(columns={"Date": "Start date"})

        _monthly = build_monthly_generation(
            df_generation=_df_gen_renamed,
            energy_cols=[c for c in ENERGY_COLS if c in _df_gen.columns],
            date_col="Start date",
        )

        # Friendly column names for the legend
        _rename = {
            "Solar":           "Solar",
            "Wind_Offshore":   "Wind Offshore",
            "Wind_Onshore":    "Wind Onshore",
            "Biomass":         "Biomass",
            "Hydro":           "Hydropower",
            "Other_Renewable": "Other Renewable",
            "Lignite":         "Lignite",
            "Hard_Coal":       "Hard Coal",
            "Gas":             "Fossil Gas",
            "Pumped_Storage":  "Pumped Storage",
            "Other_Conventional": "Other Conventional",
        }
        _monthly = _monthly.rename(columns=_rename)

        # Colour palette aligned with other charts
        _colors = {
            "Solar":             "#F59E0B",
            "Wind Offshore":     "#1D4ED8",
            "Wind Onshore":      "#60A5FA",
            "Biomass":           "#16A34A",
            "Hydropower":        "#0EA5E9",
            "Other Renewable":   "#8B5CF6",
            "Lignite":           "#78350F",
            "Hard Coal":         "#44403C",
            "Fossil Gas":        "#EF4444",
            "Pumped Storage":    "#6B7280",
            "Other Conventional":"#9CA3AF",
        }
        _col_order = [c for c in _colors if c in _monthly.columns]
        _plot_colors = [_colors[c] for c in _col_order]

        _fig, _ax = plt.subplots(figsize=(14, 7))
        _monthly[_col_order].plot(
            kind="bar",
            stacked=True,
            ax=_ax,
            color=_plot_colors,
            width=0.75,
        )
        _ax.set_title("Monthly Electricity Generation by Source — Full Year 2025", fontsize=14)
        _ax.set_xlabel("")
        _ax.set_ylabel("Energy Generated [MWh]")

        # Shorten x-axis labels: "Jan 2025" → "Jan"
        _ax.set_xticklabels(
            [lbl.get_text().replace(" 2025", "") for lbl in _ax.get_xticklabels()],
            rotation=0,
        )
        _ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"{x/1e6:.1f}M")
        )
        _ax.legend(
            title="Energy Source",
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            fontsize=9,
        )
        _ax.grid(axis="y", alpha=0.4)
        plt.tight_layout()
        return _fig

    _chart_monthly_stacked()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## Step 5 · Does weather actually explain energy production?

    > linking weather to energy.
    > We compute the **Pearson correlation coefficient (r)**:
    >
    > | r value | Meaning |
    > |---------|---------|
    > | 1.0 | Perfect positive relationship |
    > | 0.5–0.9 | Strong relationship |
    > | 0.0 | No relationship |
    > | negative | Inverse relationship |
    >
    > **Expected results:**

    > - `sunshine_min` vs `Solar` → r ≈ **0.85–0.95** (very high — sun drives solar)
    > - `wind_speed` vs `Total_Wind` → r ≈ **0.60–0.80** (strong, but non-linear)
    > - `wind_speed` vs `Solar` → r ≈ **0.0** (wind doesn't affect solar panels)
    """)
    return


@app.cell
def _(dwd_load, merge_energy_weather, mo, smard_load):
    def _build_analysis():
        _s = smard_load("cleaned_smard_2025.csv")
        _w = dwd_load()
        _m = merge_energy_weather(_s, _w)

        # ── sample rows ───────────────────────────────────────────────
        _preview_cols = ["Date", "Solar", "Total_Wind", "Total_Renewable",
                         "Total_Fossil", "Grid_Load", "Residual_Load",
                         "wind_speed", "sunshine_min", "global_radiation"]
        _show = [c for c in _preview_cols if c in _m.columns]
        _sub  = _m[_show].head(4).copy()
        _sub["Date"] = _sub["Date"].astype(str).str[:16]
        for c in _show[1:]:
            _sub[c] = _sub[c].apply(
                lambda x: f"{float(x):,.1f}" if str(x) != "nan" else "—"
            )
        _hdr  = "| " + " | ".join(_show) + " |"
        _sep  = "|" + "|".join(["---"] * len(_show)) + "|"
        _rows_md = "\n".join(
            "| " + " | ".join(str(v) for v in row) + " |"
            for row in _sub.itertuples(index=False)
        )

        # ── missing values ────────────────────────────────────────────
        _miss_lines = []
        for c in ["wind_speed", "sunshine_min", "global_radiation"]:
            if c in _m.columns:
                _n_miss = int(_m[c].isna().sum())
                _pct    = _n_miss / len(_m) * 100
                _status = "✅ good" if _pct < 5 else "⚠️ watch" if _pct < 10 else "❌ high"
                _miss_lines.append(
                    f"| `{c}` | {len(_m) - _n_miss:,} | {_n_miss:,} "
                    f"| {_pct:.1f}% | {_status} |"
                )
        _miss_md = "\n".join(_miss_lines)

        # ── correlation matrix ────────────────────────────────────────
        _corr_cols = ["Solar", "Total_Wind", "Residual_Load",
                      "wind_speed", "sunshine_min", "global_radiation"]
        _avail = [c for c in _corr_cols if c in _m.columns]
        _corr  = _m[_avail].corr().round(2)

        # colour-code each cell: strong=bold, moderate=normal, weak=muted
        def _fmt_cell(val, row_col, col_col):
            if row_col == col_col:
                return "**1.00**"          # diagonal
            v = _corr.loc[row_col, col_col]
            if abs(v) >= 0.7:
                return f"**{v}** 🔴" if v < 0 else f"**{v}** 🟢"
            elif abs(v) >= 0.4:
                return f"{v} 🟡"
            else:
                return f"*{v}*"            # italics = weak

        _c_hdr = "| | " + " | ".join(f"`{c}`" for c in _avail) + " |"
        _c_sep = "|---|" + "|".join(["---"] * len(_avail)) + "|"
        _c_rows = "\n".join(
            "| **`" + r + "`** | " +
            " | ".join(_fmt_cell(None, r, c) for c in _avail) + " |"
            for r in _avail
        )

        return _m, _hdr, _sep, _rows_md, _miss_md, _c_hdr, _c_sep, _c_rows

    (_merged, _hdr, _sep, _rows_md,
     _miss_md, _c_hdr, _c_sep, _c_rows) = _build_analysis()

    mo.md(f"""
    ---
    ## 🔍 Merged dataset — energy meets weather

    > Every row = one hour. SMARD columns (energy) joined with DWD columns (weather) on Date.
    > **{len(_merged):,} rows · {len(_merged.columns)} columns**
    > · {_merged['Date'].min()} → {_merged['Date'].max()}

    ### Sample rows (first 4 hours)

    {_hdr}
    {_sep}
    {_rows_md}

    > `—` means no weather reading that hour (sensor missing or night-time).
    > These rows are automatically skipped in the correlation calculation.

    ---

    ### Missing values in weather columns

    | Column | Available rows | Missing | Missing % | Status |
    |--------|---------------|---------|-----------|--------|
    {_miss_md}

    > ✅ below 5% = safe to use · ⚠️ 5–10% = use with caution · ❌ above 10% = consider excluding

    ---

    ### Correlation matrix (hourly data, Full Year 2025)

    > How strongly does each variable move with every other?
    > **r = 1.0** = perfect positive link · **r = 0.0** = no link · **r = −1.0** = perfect inverse link

    {_c_hdr}
    {_c_sep}
    {_c_rows}

    **How to read this:**
    - 🟢 **bold green** = strong positive (≥ 0.7) — one goes up, other goes up
    - 🔴 **bold red** = strong negative (≤ −0.7) — one goes up, other goes down
    - 🟡 moderate (0.4–0.7) · *italic* = weak (< 0.4)

    **Key findings to highlight to audience:**
    - `global_radiation` vs `Solar` → should be the strongest link in the table
    - `wind_speed` vs `Total_Wind` → strong but not as high — wind power is non-linear
    - `wind_speed` vs `Solar` → near zero — wind doesn't affect solar panels at all
    - `Residual_Load` vs renewables → negative — more sun/wind = less fossil needed ✅
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 🌍 Step 6 · Electricity Imports, Exports & Grid Balancing

    > Germany is part of the interconnected European electricity grid.
    > Electricity constantly flows between countries depending on renewable generation,
    > electricity prices, industrial demand, and grid stability.
    >
    > This creates an important question:
    >
    > **Why does Germany export electricity even when it still imports electricity overall?**

    Electricity trading happens dynamically every hour.

    During periods of strong wind or solar production, Germany may temporarily generate
    more electricity than it needs. That surplus is exported to neighboring countries.

    During periods of low renewable generation or high demand, Germany imports electricity
    to stabilize the grid.

    Germany can therefore be an exporter during sunny/windy hours and an importer during
    dark calm periods — sometimes within the same week or even the same day.
    """)
    return


@app.cell
def _(END_DATE, START_DATE, load_smard_market_trade, mo):
    df_smard_trade = load_smard_market_trade(
        start_date=START_DATE,
        end_date=END_DATE,
    )

    df_smard_trade["Month"] = (
        df_smard_trade["Start date"]
        .dt.to_period("M")
        .astype(str)
    )

    df_trade_monthly = (
        df_smard_trade
        .groupby("Month")[[
            "Total_Export_MWh",
            "Total_Import_MWh",
            "Net_Trade_MWh",
        ]]
        .sum()
        .reset_index()
    )

    _total_export = df_smard_trade["Total_Export_MWh"].sum() / 1e6
    _total_import = df_smard_trade["Total_Import_MWh"].sum() / 1e6
    _net_trade = df_smard_trade["Net_Trade_MWh"].sum() / 1e6
    _status = "net exporter" if _net_trade > 0 else "net importer"

    mo.md(f"""
    ### Import/export summary — Full Year 2025

    | Metric | Value | Meaning |
    |--------|-------|---------|
    | Total exports | **{_total_export:.2f} TWh** | Electricity sent from Germany to neighboring countries |
    | Total imports | **{_total_import:.2f} TWh** | Electricity received from neighboring countries |
    | Net trade balance | **{_net_trade:.2f} TWh** | Germany was a **{_status}** overall |

    > Positive net trade means Germany exported more than it imported.
    > Negative net trade means Germany imported more than it exported.
    """)
    return df_smard_trade, df_trade_monthly


@app.cell
def _(df_trade_monthly, px):
    def _chart_trade_monthly():
        _plot = df_trade_monthly.copy()
        _fig = px.bar(
            _plot,
            x="Month",
            y=[
                "Total_Export_MWh",
                "Total_Import_MWh",
            ],
            barmode="group",
            title="Monthly Electricity Export vs Import in Germany (2025)",
            labels={
                "value": "Energy [MWh]",
                "variable": "Trade Type",
            },
        )
        _fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Energy [MWh]",
            height=550,
            legend_title="",
            hovermode="x unified",
        )
        _fig.update_traces(
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                + "Month=%{x}<br>"
                + "Energy=%{y:,.0f} MWh<extra></extra>"
            )
        )
        return _fig

    _chart_trade_monthly()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 🔍 Why does Germany export electricity while still importing?

    At first glance, this seems contradictory.

    If Germany sometimes lacks enough electricity, why export power at all?

    The reason is that electricity production and demand change every hour.

    ### Germany exports electricity when:

    - wind generation is very high
    - solar production exceeds daytime demand
    - electricity prices become very low
    - neighboring countries need additional supply

    ### Germany imports electricity when:

    - wind and solar production are weak
    - industrial demand is high
    - imported electricity is temporarily cheaper
    - neighboring countries have surplus stable generation

    ### Example: France

    France can export nuclear electricity to Germany because nuclear plants run continuously.
    At night or during low-price periods, this electricity may be cheaper than increasing
    domestic fossil generation in Germany.

    Therefore, Germany can export renewable electricity during surplus periods and import
    electricity during deficit periods. This is normal behavior in the interconnected
    European electricity market.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 🔋 Why not simply store excess renewable energy?

    > A common question is:
    >
    > **Why export renewable electricity instead of storing it for later?**

    The main limitation is that large-scale electricity storage is still expensive and limited.

    | Technology | Limitation |
    |------------|-----------|
    | Batteries | Very expensive at national scale |
    | Pumped hydro | Limited geographic capacity |
    | Hydrogen | Efficiency losses remain high |

    Renewable generation is highly variable: solar peaks during summer daytime, wind
    fluctuates unpredictably, and electricity demand exists continuously. Because of this
    mismatch, Germany cannot currently store all renewable surplus energy efficiently.

    The European electricity grid therefore acts like a shared balancing system: countries
    export surplus electricity when production is high and import electricity when production
    is low. This interconnected system improves grid stability across Europe.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 📘 Final Interpretation

    Germany's electricity system demonstrates both the strengths and the challenges of
    renewable integration.

    The analysis shows that:

    - renewable generation frequently exceeds demand during high wind and solar periods
    - renewable output remains highly weather-dependent
    - imports and exports are essential for balancing the grid
    - the European interconnected market increases overall system stability

    Although Germany may show a yearly generation deficit during some periods, this does
    not prevent temporary renewable surpluses and electricity exports.

    Electricity trading therefore reflects market economics, weather variability, grid
    balancing requirements, and cross-border cooperation rather than simple national
    self-sufficiency.

    The European grid effectively acts as a continental balancing mechanism for renewable
    electricity systems.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 🗺️ What comes next — project roadmap

    > This notebook covers the **full year 2025** (8,760 hourly rows).
    > The full STAGES project extends this to **multiple years** and deeper analysis.

    ### Open research questions

    | # | Question | Method |
    |---|----------|--------|
    | 1 | How has renewable share changed since 2015? | Download SMARD annual files, plot trend |
    | 2 | How accurately does weather predict generation? | Linear regression, R² score |
    | 3 | How often does Dunkelflaute occur — and how long does it last? | Rolling window on DWD winter data |
    | 4 | What backup capacity does Germany always need? | 5th percentile of renewable generation |
    | 5 | Does geographic station diversity reduce risk? | Correlate Hamburg vs München wind |

    ### Data still to add

    | Source | What | Why |
    |--------|------|-----|
    | SMARD | 2015–2024 annual CSVs | Long-term trend |
    | DWD `wind/historical/` | Winter months | Dunkelflaute seasons |
    | ENTSO-E | Cross-border flows | Did Germany import during low-ren periods? |

    ### Timeline

    | When | Milestone |
    |------|-----------|
    | Week 3–4 | Multi-year SMARD download + pipeline extension |
    | Week 4–6 | DWD winter data + Dunkelflaute detection |
    | Week 6–8 | Regression model (weather → generation) |
    | Week 8–10 | Dashboard polish + GitHub Pages |
    | **July 10, 2026** | **📬 Report submission (via email)** |

    ---
    *STAGES Project · Bauhaus-Universität Weimar · SoSe 2026 · All code in `utils.py`*
    """)
    return


if __name__ == "__main__":
    app.run()
