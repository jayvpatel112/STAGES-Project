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
    alt.data_transformers.enable("vegafusion")

    from utils import (
        DWD_STATIONS,
        dwd_download_all, dwd_download_summary,
        dwd_build_national, dwd_save, dwd_load, dwd_quality_report,
        smard_load_raw, smard_clean_generation, smard_clean_consumption,
        smard_add_features, smard_merge, smard_aggregate_daily,
        smard_save, smard_load,
        merge_energy_weather, compute_summary, summary_to_markdown,
    )

    return (
        alt,
        compute_summary,
        dwd_build_national,
        dwd_download_all,
        dwd_download_summary,
        dwd_load,
        dwd_quality_report,
        dwd_save,
        merge_energy_weather,
        mo,
        pd,
        smard_add_features,
        smard_aggregate_daily,
        smard_clean_consumption,
        smard_clean_generation,
        smard_load,
        smard_load_raw,
        smard_merge,
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
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
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


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## Step 2 · Clean & average the weather data

    > Raw DWD files have quirks that must be fixed before analysis:
    >
    > | Problem | How we fix it |
    > |---------|--------------|
    > | Missing values coded as **-999** | Replace with `NaN` — never treat as real data |
    > | Timestamps in **UTC** | Convert to `Europe/Berlin` to align with SMARD |
    > | Trailing semicolons in CSV | Handled automatically by pandas `sep=";"` |
    > | Column name whitespace | Strip with `.str.strip()` |
    >
    > After cleaning each station, we **average across all 6** to get one national
    > weather signal per hour. This is a simplification — a full analysis would
    > weight stations by the installed renewable capacity in their region.
    >
    > All of this logic lives in `utils.py` — the cell below calls a single function.
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
    > We use two files downloaded from [smard.de](https://www.smard.de):
    >
    > | File | What it contains |
    > |------|-----------------|
    > | `Actual_generation_*.csv` | Hourly MWh from each source: solar, wind, gas, coal… |
    > | `Actual_consumption_*.csv` | Hourly grid load and residual load |
    >
    > **What is residual load?**
    > Residual load = Grid demand − Renewable generation.
    > When this is low, renewables are doing the heavy lifting.
    > When it goes **negative**, renewables produce more than Germany needs — surplus is exported.
    """)
    return


@app.cell
def _(
    mo,
    smard_add_features,
    smard_clean_consumption,
    smard_clean_generation,
    smard_load_raw,
    smard_merge,
    smard_save,
):

    def _run_smard():
        _gen_raw = smard_load_raw("Actual_generation_202501010000_202601010000_Hour.csv")
        _con_raw = smard_load_raw("Actual_consumption_202501010000_202601010000_Hour.csv")
        _gen = smard_add_features(smard_clean_generation(_gen_raw))
        _con = smard_clean_consumption(_con_raw)
        _df  = smard_merge(_gen, _con)
        smard_save(_df, "cleaned_smard_2025.csv")
        return _df

    _smard = _run_smard()

    mo.md(f"""
    ### SMARD data loaded and saved

    | | Value |
    |-|-------|
    | Hourly rows | {len(_smard):,} |
    | Date range | {_smard["Date"].min().strftime("%b %d, %Y")} → {_smard["Date"].max().strftime("%b %d, %Y")} |
    | Sources tracked | Solar, Wind (on+offshore), Biomass, Hydro, Lignite, Hard Coal, Gas |
    | Overall renewable share | **{_smard["Total_Renewable"].sum() / _smard["Total_Generation"].sum() * 100:.1f}%** |

    > Saved to `data/cleaned/cleaned_smard_2025.csv`.
    > All chart cells below load from this file — no re-downloading needed.
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
    ## 📊 Chart 1 · Daily electricity mix — renewables vs. fossil fuels

    > Each bar = one day. **Green = renewable**. **Brown = fossil fuels**.
    > Bar height = total daily generation in GWh (1 GWh powers ~1,000 homes for a day).
    >
    > Watch how the green portion changes across the full year — solar peaks in summer,
    > wind peaks in winter. On calm, cloudy days the brown portion expands — those are the days
    > gas and coal plants have to work hardest to keep the lights on.
    """)
    return


@app.cell
def _(alt, pd, smard_aggregate_daily, smard_load):
    def _chart_stacked():
        _d = smard_aggregate_daily(smard_load("cleaned_smard_2025.csv"))
        _m = pd.melt(
            _d[["Date","Total_Renewable","Total_Fossil"]].assign(
                Total_Renewable=_d["Total_Renewable"]/1000,
                Total_Fossil=_d["Total_Fossil"]/1000,
            ),
            id_vars="Date", var_name="Type", value_name="GWh"
        )
        _m["Label"] = _m["Type"].map({
            "Total_Renewable": "🌱 Renewables",
            "Total_Fossil":    "🏭 Fossil Fuels",
        })
        return alt.Chart(_m).mark_bar(size=5).encode(
            x=alt.X("Date:T", axis=alt.Axis(format="%b %d", labelAngle=-45, title="")),
            y=alt.Y("GWh:Q", stack="zero", title="Daily Generation (GWh)"),
            color=alt.Color("Label:N",
                scale=alt.Scale(
                    domain=["🌱 Renewables","🏭 Fossil Fuels"],
                    range=["#22C55E","#78350F"]
                ),
                legend=alt.Legend(title="")
            ),
            tooltip=[
                alt.Tooltip("Date:T", format="%B %d, %Y"),
                alt.Tooltip("Label:N"),
                alt.Tooltip("GWh:Q", title="GWh", format=".0f"),
            ]
        ).properties(
            title="Daily Generation: Renewables vs. Fossil Fuels (Full Year 2025)",
            width=900, height=320
        ).interactive()

    _chart_stacked()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 📊 Chart 2 · Supply vs. demand — is Germany self-sufficient?

    > 🔵 **Blue** = total electricity generated | 🟡 **Yellow dashed** = actual demand
    > 🔴 **Red dotted** = residual load (what fossil fuels or imports must cover)
    >
    > When blue > yellow → Germany exports surplus to neighbours.
    > When red is near zero → renewables are almost fully covering demand.
    > When red spikes → gas and coal plants fire up to fill the gap.
    """)
    return


@app.cell
def _(alt, pd, smard_aggregate_daily, smard_load):
    def _chart_supply():
        _d = smard_aggregate_daily(smard_load("cleaned_smard_2025.csv"))
        _labels = {
            "Total_Generation": "⚡ Generation",
            "Grid_Load":        "🏠 Demand",
            "Residual_Load":    "🔺 Residual (fossil needed)",
        }
        _m = pd.melt(
            _d[["Date","Total_Generation","Grid_Load","Residual_Load"]].assign(
                Total_Generation=_d["Total_Generation"]/1000,
                Grid_Load=_d["Grid_Load"]/1000,
                Residual_Load=_d["Residual_Load"]/1000,
            ),
            id_vars="Date", var_name="Metric", value_name="GWh"
        )
        _m["Label"] = _m["Metric"].map(_labels)
        return alt.Chart(_m).mark_line(strokeWidth=2).encode(
            x=alt.X("Date:T", axis=alt.Axis(format="%b %d", labelAngle=-45)),
            y=alt.Y("GWh:Q", title="Daily Total (GWh)"),
            color=alt.Color("Label:N",
                scale=alt.Scale(
                    domain=list(_labels.values()),
                    range=["#3B82F6","#F59E0B","#EF4444"]
                ),
                legend=alt.Legend(title="")
            ),
            strokeDash=alt.StrokeDash("Label:N",
                scale=alt.Scale(
                    domain=list(_labels.values()),
                    range=[[1,0],[4,2],[6,3]]
                )
            ),
            tooltip=[
                alt.Tooltip("Date:T", format="%B %d, %Y"),
                alt.Tooltip("Label:N"),
                alt.Tooltip("GWh:Q", format=".0f"),
            ]
        ).properties(
            title="Supply vs. Demand — Germany Full Year 2025",
            width=900, height=320
        ).interactive()

    _chart_supply()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 📊 Chart 3 · Solar ☀️ vs. Wind 🌬️ — the two workhorses

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
    ## 📊 Chart 4 · The daily rhythm — when do we generate and consume?

    > Average power by hour of day, averaged across all 365 days in the dataset.
    >
    > **The "duck curve" problem:** Solar peaks sharply around **noon**,
    > but demand peaks in the **morning and evening** when people wake up and come home.
    > This mismatch means the grid needs either energy storage (batteries, pumped hydro)
    > or flexible backup generation (gas peakers) to bridge the difference.
    > This is one of the central engineering challenges of the energy transition.
    """)
    return


@app.cell
def _(alt, pd, smard_load):
    def _chart_hourly():
        _df = smard_load("cleaned_smard_2025.csv")
        _df["Hour"] = _df["Date"].dt.hour
        _h = _df.groupby("Hour")[["Solar","Total_Wind","Grid_Load"]].mean().reset_index()
        _h = _h.assign(Solar=_h["Solar"]/1000, Total_Wind=_h["Total_Wind"]/1000, Grid_Load=_h["Grid_Load"]/1000)
        _labels = {"Solar":"☀️ Solar","Total_Wind":"🌬️ Wind","Grid_Load":"🏠 Demand"}
        _m = pd.melt(_h, id_vars="Hour", value_vars=list(_labels.keys()), var_name="Metric", value_name="GW")
        _m["Label"] = _m["Metric"].map(_labels)
        return alt.Chart(_m).mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X("Hour:O", title="Hour of day (0 = midnight, 12 = noon)"),
            y=alt.Y("GW:Q", title="Average power (GW)"),
            color=alt.Color("Label:N",
                scale=alt.Scale(domain=list(_labels.values()), range=["#F59E0B","#3B82F6","#EF4444"])
            ),
            tooltip=[alt.Tooltip("Hour:O"), alt.Tooltip("Label:N"), alt.Tooltip("GW:Q", format=".2f")]
        ).properties(
            title="Average Hourly Power — Solar, Wind, and Demand (Full Year 2025)",
            width=700, height=320
        )

    _chart_hourly()
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 📊 Chart 5 · Renewable risk days — when did the grid struggle?

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
def _(mo, smard_load, dwd_load, merge_energy_weather):
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
