"""
STAGES Project — Complete Code from Chat Session 1
====================================================
Contains every piece of analysis built in this conversation:
  1. Q3 2025 SMARD analysis (Cells 1-10)
  2. Headline demand/residual-load metrics for the main report
     (new cell, right after df_clean)
  3. Weather data integration with Open-Meteo (Cells 11-13)
  4. Weather × Energy correlations (Cell 14)
  5. Scatter plots (Cell 15)
  6. Wind & Solar regression models (Cells 16-17)
  7. Fitted model curves (Cell 18)
  8. Q4 ADDITIONAL: Full year combining (Cells 19-22)
  9. Q5 ADDITIONAL: Dunkelflaute detection (Cell 23)

Each code cell is preceded by its own explanation cell (rendered as
markdown text in the notebook) describing what that cell does and why.

Required files in the same folder:
  - Actual_generation_202507010000_202510010000_Hour.csv   (SMARD Q3 generation)
  - Actual_consumption_202507010000_202510010000_Hour.csv  (SMARD Q3 demand)
  - weather_hamburg.csv, weather_munich.csv,
    weather_berlin.csv, weather_frankfurt.csv              (Q3 weather)

Optional (for full-year combining):
  - merged_q1_2025.csv, merged_q2_2025.csv, merged_q4_2025.csv

Open with:
  python -m marimo edit stages_full_chat.py
"""

import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    **Cell 1 explanation.**
    Loads the four libraries used throughout the notebook: marimo for
    the reactive notebook itself, pandas for data handling, matplotlib
    for charts, and numpy for numerical helpers (e.g. smooth curves).
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np

    return mo, np, pd, plt


@app.cell
def _(mo):
    mo.md("""
    **Cell 2 explanation.**
    Loads the raw SMARD generation export for Q3 2025 (hourly, MWh per
    source). `sep=";"` and `thousands=","` match SMARD's export format
    (German-style CSV). `encoding="utf-8-sig"` strips the BOM character
    SMARD/Excel adds at the start of the file.
    """)
    return


@app.cell
def _(pd):
    df = pd.read_csv(
        "data/raw/Actual_generation_202507010000_202510010000_Hour.csv",
        sep=";",
        thousands=",",
        encoding="utf-8-sig"
    )
    df
    return (df,)


@app.cell
def _(mo):
    mo.md("""
    **Cell 3 explanation.**
    Cleans the raw data before analysis:
    1. Renames the long SMARD column headers to short, readable names.
    2. Parses the "start" timestamp string into a real datetime object.
    3. Replaces "-" (SMARD's symbol for "no data") with 0 so we can do
       math on it.
    4. Forces the Nuclear column to numeric (it should be 0 all
       quarter, since Germany's nuclear phase-out finished in April 2023).
    """)
    return


@app.cell
def _(df, pd):
    df_clean = df.copy()

    df_clean.columns = [
        "start", "end",
        "Biomass", "Hydropower", "Wind Offshore", "Wind Onshore",
        "Solar", "Other Renewable", "Nuclear",
        "Lignite", "Hard Coal", "Fossil Gas",
        "Pumped Storage", "Other Conventional"
    ]

    df_clean["start"] = pd.to_datetime(df_clean["start"], format="%b %d, %Y %I:%M %p")
    df_clean = df_clean.replace("-", 0)
    df_clean["Nuclear"] = pd.to_numeric(df_clean["Nuclear"], errors="coerce").fillna(0)

    df_clean
    return (df_clean,)


@app.cell
def _(mo):
    mo.md("""
    **Cell 4 explanation.**
    Exports aggregated CSVs for LaTeX pgfplots figures used directly in
    `main.tex`. Column names are renamed to remove spaces so pgfplots
    can reference them safely as table columns (e.g. "Wind Onshore" ->
    "Wind_Onshore"). Five CSVs are written, each aggregated a different
    way for a different figure: daily mean per renewable source, daily
    mean per conventional source, daily mean pumped storage, average
    output per hour of day (for the diurnal profile chart), and average
    output per month (for the monthly bar chart).
    """)
    return


@app.cell
def _(df_clean):
    csv_rename = {
        "Wind Offshore": "Wind_Offshore", "Wind Onshore": "Wind_Onshore",
        "Other Renewable": "Other_Renewable", "Hard Coal": "Hard_Coal",
        "Fossil Gas": "Fossil_Gas", "Pumped Storage": "Pumped_Storage",
        "Other Conventional": "Other_Conventional",
    }
    df_csv = df_clean.rename(columns=csv_rename)

    renewables_csv = ["Biomass", "Hydropower", "Wind_Offshore", "Wind_Onshore",
                      "Solar", "Other_Renewable"]
    conventional_csv = ["Lignite", "Hard_Coal", "Fossil_Gas", "Other_Conventional"]

    df_csv["Date"] = df_csv["start"].dt.date

    daily_renewable = df_csv.groupby("Date")[renewables_csv].mean().reset_index()
    daily_renewable.to_csv("outputs/q3/q3_renewable_daily.csv", index=False)

    daily_conventional = df_csv.groupby("Date")[conventional_csv].mean().reset_index()
    daily_conventional.to_csv("outputs/q3/q3_conventional_daily.csv", index=False)

    daily_pumped = df_csv.groupby("Date")[["Pumped_Storage"]].mean().reset_index()
    daily_pumped.to_csv("outputs/q3/q3_pumped_storage_daily.csv", index=False)

    df_csv["Hour"] = df_csv["start"].dt.hour
    hourly_profile = df_csv.groupby("Hour")[
        ["Wind_Onshore", "Solar", "Fossil_Gas", "Lignite", "Biomass"]
    ].mean().reset_index()
    hourly_profile.to_csv("outputs/q3/q3_hourly_profile.csv", index=False)

    df_csv["Month"] = df_csv["start"].dt.month_name()
    monthly_mix = df_csv.groupby("Month")[
        ["Wind_Onshore", "Solar", "Lignite", "Fossil_Gas", "Biomass", "Hydropower"]
    ].mean()
    monthly_mix = monthly_mix.reindex(["July", "August", "September"]).reset_index()
    monthly_mix.to_csv("outputs/q3/q3_monthly_mix.csv", index=False)

    print("Written: q3_renewable_daily.csv, q3_conventional_daily.csv,")
    print("         q3_pumped_storage_daily.csv, q3_hourly_profile.csv,")
    print("         q3_monthly_mix.csv")
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 5 explanation.**
    Loads demand data (requires
    `Actual_consumption_202507010000_202510010000_Hour.csv` in the same
    folder) and merges it with generation to compute the report's key
    summary numbers:
    - `Total_Renewable_MWh` = sum of the six renewable sources, per hour
    - `Residual_Load_MWh` = demand minus renewables (negative = renewables
      alone exceeded demand that hour)
    - `Total_Generation_MWh` = all domestic generation, renewable + conventional
    - `Net_Trade_Proxy_MWh` = generation minus demand (positive = net
      export proxy, negative = net import proxy; simplified, ignores grid
      losses and actual cross-border flow)
    """)
    return


@app.cell
def _(df_clean, pd):
    df_demand = pd.read_csv(
        "data/raw/Actual_consumption_202507010000_202510010000_Hour.csv",
        sep=";", thousands=",", encoding="utf-8-sig"
    )

    df_demand = df_demand.rename(columns={
        "Start date": "start",
        "grid load [MWh] Calculated resolutions": "Grid_Load_MWh",
        "Residual load [MWh] Calculated resolutions": "SMARD_Residual_Load_MWh",
    })
    df_demand["start"] = pd.to_datetime(df_demand["start"], format="%b %d, %Y %I:%M %p")

    df_balance = pd.merge(
        df_clean,
        df_demand[["start", "Grid_Load_MWh", "SMARD_Residual_Load_MWh"]],
        on="start",
        how="inner"
    )

    renewables_list_q3 = ["Biomass", "Hydropower", "Wind Offshore", "Wind Onshore",
                          "Solar", "Other Renewable"]
    conventional_list_q3 = ["Lignite", "Hard Coal", "Fossil Gas",
                            "Other Conventional", "Pumped Storage"]

    df_balance["Total_Renewable_MWh"] = df_balance[renewables_list_q3].sum(axis=1)
    df_balance["Residual_Load_MWh"] = df_balance["Grid_Load_MWh"] - df_balance["Total_Renewable_MWh"]
    df_balance["Total_Generation_MWh"] = (
        df_balance["Total_Renewable_MWh"] + df_balance[conventional_list_q3].sum(axis=1)
    )
    df_balance["Net_Trade_Proxy_MWh"] = df_balance["Total_Generation_MWh"] - df_balance["Grid_Load_MWh"]

    total_renewable_twh = df_balance[renewables_list_q3].sum().sum() / 1e6
    total_conventional_twh = df_balance[conventional_list_q3].sum().sum() / 1e6
    total_generation_twh = total_renewable_twh + total_conventional_twh
    renewable_share_of_generation = total_renewable_twh / total_generation_twh * 100

    total_demand_twh = df_balance["Grid_Load_MWh"].sum() / 1e6
    avg_grid_load_gw = df_balance["Grid_Load_MWh"].mean() / 1000
    generation_coverage_pct = total_generation_twh / total_demand_twh * 100
    renewable_share_of_demand = (
        df_balance["Total_Renewable_MWh"].sum() / df_balance["Grid_Load_MWh"].sum() * 100
    )

    avg_residual_load = df_balance["Residual_Load_MWh"].mean()
    max_residual_load = df_balance["Residual_Load_MWh"].max()
    hours_renewables_met_demand = (df_balance["Residual_Load_MWh"] < 0).sum()
    net_export_hours = (df_balance["Net_Trade_Proxy_MWh"] > 0).sum()
    net_import_hours = (df_balance["Net_Trade_Proxy_MWh"] < 0).sum()

    print(f"Merged rows: {len(df_balance)}")
    print()
    print(f"Total renewable generation:      {total_renewable_twh:.2f} TWh")
    print(f"Total conventional generation:   {total_conventional_twh:.2f} TWh")
    print(f"Total domestic generation:       {total_generation_twh:.2f} TWh")
    print(f"Renewable share of generation:   {renewable_share_of_generation:.1f}%")
    print()
    print(f"Total electricity demand:        {total_demand_twh:.2f} TWh")
    print(f"Average grid load:               {avg_grid_load_gw:.1f} GW")
    print(f"Generation coverage of demand:   {generation_coverage_pct:.1f}%")
    print(f"Renewable share of demand:       {renewable_share_of_demand:.1f}%")
    print(f"Average residual load:           {avg_residual_load:,.0f} MWh/h")
    print(f"Maximum residual load:           {max_residual_load:,.0f} MWh/h")
    print(f"Hours renewables met demand:     {hours_renewables_met_demand}")
    print(f"Net-export hours (proxy):        {net_export_hours}")
    print(f"Net-import hours (proxy):        {net_import_hours}")
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 6 explanation.**
    Chart 1 — one line per renewable source, plotted hourly across the
    full quarter. Solar shows a clear daily on/off pulse; wind is
    irregular and weather-driven; biomass/hydropower are relatively
    flat baseload.
    """)
    return


@app.cell
def _(df_clean, plt):
    renewables_list = ["Biomass", "Hydropower", "Wind Offshore", "Wind Onshore", "Solar", "Other Renewable"]
    conventional_list = ["Lignite", "Hard Coal", "Fossil Gas", "Other Conventional"]

    renewable_colors = ["#6A994E", "#4B9CD3", "#64A6BD", "#3A7CA5", "#F2C14E", "#A7C957"]
    conventional_colors = ["#5C4033", "#C97B2E", "#C0392B", "#7F8C8D"]

    fig_renew, ax_renew = plt.subplots(figsize=(16, 6))
    for source, color in zip(renewables_list, renewable_colors):
        ax_renew.plot(df_clean["start"], df_clean[source], label=source,
                      color=color, linewidth=1.1, alpha=0.85)
    ax_renew.set_title("Renewable Energy Production — Q3 2025 (Jul–Sep)", fontsize=14, fontweight="bold")
    ax_renew.set_ylabel("Production (MWh)")
    ax_renew.set_xlabel("Date")
    ax_renew.legend(loc="upper right", fontsize=9, ncol=2, framealpha=0.9)
    ax_renew.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.gca()
    return conventional_colors, conventional_list


@app.cell
def _(mo):
    mo.md("""
    **Cell 7 explanation.**
    Chart 2 — same idea as Chart 1 but for fossil/thermal sources.
    Lignite is Germany's inflexible baseload (roughly flat); Fossil Gas
    ramps up and down daily to fill the gap left by variable renewables.
    """)
    return


@app.cell
def _(conventional_colors, conventional_list, df_clean, plt):
    fig_conv, ax_conv = plt.subplots(figsize=(16, 6))
    for source_c, color_c in zip(conventional_list, conventional_colors):
        ax_conv.plot(df_clean["start"], df_clean[source_c], label=source_c,
                     color=color_c, linewidth=1.1, alpha=0.85)
    ax_conv.set_title("Conventional Energy Production — Q3 2025", fontsize=14, fontweight="bold")
    ax_conv.set_ylabel("Production (MWh)")
    ax_conv.set_xlabel("Date")
    ax_conv.legend(loc="upper right", fontsize=9, ncol=2, framealpha=0.9)
    ax_conv.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 8 explanation.**
    Chart 3 — pumped storage plotted separately because it behaves
    differently from other sources: it's dispatched opportunistically
    (mostly released in the evening after a high-solar day), producing
    an irregular, spiky pattern rather than a steady or cyclical one.
    """)
    return


@app.cell
def _(df_clean, plt):
    fig_pumped, ax_pumped = plt.subplots(figsize=(16, 5))
    ax_pumped.plot(df_clean["start"], df_clean["Pumped Storage"],
                   color="purple", linewidth=1.1)
    ax_pumped.set_title("Pumped Storage — Q3 2025", fontsize=14, fontweight="bold")
    ax_pumped.set_ylabel("Production (MWh)")
    ax_pumped.set_xlabel("Date")
    ax_pumped.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 9 explanation.**
    Chart 4 — averages the 24 hourly readings for each day into a
    single daily value, which removes solar's daily on/off cycle so we
    can see longer-term (day-to-day and week-to-week) trends instead.
    On high-wind/high-solar days, Fossil Gas and Lignite output visibly
    drop — evidence of renewables displacing conventional generation.
    """)
    return


@app.cell
def _(df_clean, pd, plt):
    df_daily = df_clean.copy()
    df_daily["date"] = df_clean["start"].dt.date

    df_daily = df_daily.groupby("date")[
        ["Biomass", "Hydropower", "Wind Offshore", "Wind Onshore",
         "Solar", "Other Renewable", "Lignite", "Hard Coal",
         "Fossil Gas", "Pumped Storage"]
    ].mean().reset_index()
    df_daily["date"] = pd.to_datetime(df_daily["date"])

    fig2, ax2 = plt.subplots(figsize=(16, 7))
    ax2.plot(df_daily["date"], df_daily["Wind Onshore"], label="Wind Onshore", linewidth=2, color="#1f77b4")
    ax2.plot(df_daily["date"], df_daily["Solar"], label="Solar", linewidth=2, color="#ff7f0e")
    ax2.plot(df_daily["date"], df_daily["Fossil Gas"], label="Fossil Gas", linewidth=2, linestyle="--", color="#d62728")
    ax2.plot(df_daily["date"], df_daily["Lignite"], label="Lignite", linewidth=2, linestyle="--", color="#8c564b")
    ax2.set_title("Daily Average Energy Production — Q3 2025", fontsize=14, fontweight="bold")
    ax2.set_ylabel("Average Production (MWh/hr)")
    ax2.set_xlabel("Date")
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 10 explanation.**
    Chart 5 — groups every hourly reading by hour-of-day (0-23) and
    averages across all days in Q3, producing a "typical day" profile.
    Solar peaks sharply around noon; Fossil Gas roughly mirrors it in
    reverse, ramping down at midday and back up in the evening — the
    classic "solar duck curve".
    """)
    return


@app.cell
def _(df_clean, plt):
    df_pattern = df_clean.copy()
    df_pattern["hour"] = df_clean["start"].dt.hour

    df_hourly_avg = df_pattern.groupby("hour")[
        ["Wind Onshore", "Solar", "Fossil Gas", "Lignite", "Biomass"]
    ].mean()

    fig3, ax3 = plt.subplots(figsize=(12, 7))
    ax3.plot(df_hourly_avg.index, df_hourly_avg["Wind Onshore"], label="Wind Onshore", linewidth=2.5, marker="o")
    ax3.plot(df_hourly_avg.index, df_hourly_avg["Solar"], label="Solar", linewidth=2.5, marker="s")
    ax3.plot(df_hourly_avg.index, df_hourly_avg["Fossil Gas"], label="Fossil Gas", linewidth=2.5, linestyle="--", marker="^")
    ax3.plot(df_hourly_avg.index, df_hourly_avg["Lignite"], label="Lignite", linewidth=2.5, linestyle="--", marker="v")
    ax3.plot(df_hourly_avg.index, df_hourly_avg["Biomass"], label="Biomass", linewidth=2.5, marker="d")
    ax3.set_title("Average Hourly Production Pattern — Q3 2025", fontsize=14, fontweight="bold")
    ax3.set_xlabel("Hour of Day (0 = midnight, 12 = noon)")
    ax3.set_ylabel("Average Production (MWh)")
    ax3.set_xticks(range(0, 24))
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 11 explanation.**
    Builds the monthly average production table. Averages (not totals)
    are used so July, August, and September are directly comparable
    despite having different numbers of days. Reindexed to force
    calendar order, since pandas would otherwise sort month names
    alphabetically (August, July, September).
    """)
    return


@app.cell
def _(df_clean):
    df_month = df_clean.copy()
    df_month["month"] = df_clean["start"].dt.month_name()

    monthly_avg = df_month.groupby("month")[
        ["Wind Onshore", "Solar", "Lignite", "Fossil Gas", "Biomass", "Hydropower"]
    ].mean()

    monthly_avg = monthly_avg.reindex(["July", "August", "September"])
    monthly_avg.round(0)
    return (monthly_avg,)


@app.cell
def _(mo):
    mo.md("""
    **Cell 12 explanation.**
    Chart 6 — turns the monthly table above into a grouped bar chart:
    each cluster of bars is one month, and each bar within a cluster is
    one source. Makes it easy to see, e.g., solar declining from July
    into September as days shorten heading into autumn.
    """)
    return


@app.cell
def _(monthly_avg, plt):
    fig4, ax4 = plt.subplots(figsize=(12, 7))
    monthly_avg.plot(kind="bar", ax=ax4, width=0.8)
    ax4.set_title("Monthly Average Production — Q3 2025", fontsize=14, fontweight="bold")
    ax4.set_xlabel("Month")
    ax4.set_ylabel("Average Production (MWh/hr)")
    ax4.legend(loc="upper right", fontsize=9)
    ax4.grid(True, alpha=0.3, axis="y")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 13 explanation.**
    `describe().T` gives one row per source with
    count/mean/std/min/25%/50%/75%/max. Useful sanity checks: min
    should be 0 (no negative generation), and Nuclear's min/max/mean
    should all be 0, confirming Germany's 2023 nuclear phase-out.
    """)
    return


@app.cell
def _(df_clean):
    energy_cols = [
        "Biomass", "Hydropower", "Wind Offshore", "Wind Onshore",
        "Solar", "Other Renewable", "Nuclear",
        "Lignite", "Hard Coal", "Fossil Gas",
        "Pumped Storage", "Other Conventional"
    ]
    summary = df_clean[energy_cols].describe().T
    summary
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 14 explanation.**
    For every hour: Renewable Share % = renewables / (renewables +
    conventional). Pumped Storage is excluded from "conventional" here
    since it's storage, not a fuel source. The average/max/min at the
    end show how much renewable penetration varies hour to hour (e.g. a
    calm, cloudy hour vs. a windy, sunny midday).
    """)
    return


@app.cell
def _(df_clean):
    renewables_share = ["Biomass", "Hydropower", "Wind Offshore", "Wind Onshore", "Solar", "Other Renewable"]
    conventional_share = ["Lignite", "Hard Coal", "Fossil Gas", "Other Conventional"]

    df_share = df_clean.copy()
    df_share["Total Renewable"] = df_share[renewables_share].sum(axis=1)
    df_share["Total Conventional"] = df_share[conventional_share].sum(axis=1)
    df_share["Total Production"] = df_share["Total Renewable"] + df_share["Total Conventional"]
    df_share["Renewable Share %"] = df_share["Total Renewable"] / df_share["Total Production"] * 100

    avg_renewable_share = df_share["Renewable Share %"].mean()
    print(f"Average renewable share in Q3 2025: {avg_renewable_share:.1f}%")
    print(f"Maximum renewable share (one hour): {df_share['Renewable Share %'].max():.1f}%")
    print(f"Minimum renewable share (one hour): {df_share['Renewable Share %'].min():.1f}%")

    df_share[["start", "Total Renewable", "Total Conventional", "Renewable Share %"]]
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 15 explanation.**
    Previews one weather file before merging all four. Open-Meteo
    exports have two metadata rows (lat/lon/elevation/timezone) before
    the real header, so `skiprows=2` is needed. Loading Hamburg alone
    first is a quick check that the file format/columns look right
    before repeating the process for all four cities in the next cell.
    """)
    return


@app.cell
def _(pd):
    weather_hamburg = pd.read_csv("data/raw/weather_hamburg.csv", skiprows=2)
    weather_hamburg
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 16 explanation.**
    Germany is too large to represent with one weather station, so we
    use four spread-out cities (Hamburg=north, Munich=south,
    Berlin=east, Frankfurt=central) and average them into one national
    hourly value. Timezone note: Open-Meteo returns UTC; SMARD
    timestamps are in German local time. In summer that's CEST =
    UTC+2, so we shift the weather timestamps forward 2 hours to line
    them up correctly for the merge later — getting this wrong would
    silently misalign every row.
    """)
    return


@app.cell
def _(pd):
    cities = {
        "Hamburg":   "data/raw/weather_hamburg.csv",
        "Munich":    "data/raw/weather_munich.csv",
        "Berlin":    "data/raw/weather_berlin.csv",
        "Frankfurt": "data/raw/weather_frankfurt.csv"
    }

    clean_cols = {
        "time": "time",
        "temperature_2m (°C)":        "temp_C",
        "cloud_cover (%)":            "cloud_pct",
        "wind_speed_10m (km/h)":      "wind_10m",
        "wind_speed_100m (km/h)":     "wind_100m",
        "shortwave_radiation (W/m²)": "solar_total",
        "direct_radiation (W/m²)":    "solar_direct",
        "diffuse_radiation (W/m²)":   "solar_diffuse"
    }

    weather_dfs = {}
    for city, filename in cities.items():
        w = pd.read_csv(filename, skiprows=2)
        w = w.rename(columns=clean_cols)
        w["time"] = pd.to_datetime(w["time"])
        weather_dfs[city] = w

    numeric_cols = ["temp_C", "cloud_pct", "wind_10m", "wind_100m",
                    "solar_total", "solar_direct", "solar_diffuse"]

    all_weather = pd.concat([_df.assign(city=_city) for _city, _df in weather_dfs.items()])
    weather_avg = all_weather.groupby("time")[numeric_cols].mean().reset_index()

    # UTC to CEST (German summer time = UTC+2)
    # For Q1/Q4 use: weather_avg["time"] = pd.to_datetime(weather_avg["time"], utc=True).dt.tz_convert("Europe/Berlin").dt.tz_localize(None)
    weather_avg["time"] = weather_avg["time"] + pd.Timedelta(hours=2)

    weather_avg
    return (weather_avg,)


@app.cell
def _(mo):
    mo.md("""
    **Cell 17 explanation.**
    Inner join on the shared timestamp: keeps only hours present in
    both the generation data and the weather data. Since both cover
    exactly Q3 2025, very few (ideally zero) rows should be dropped —
    the printed row count is a quick check that the timestamps
    actually lined up.
    """)
    return


@app.cell
def _(df_clean, pd, weather_avg):
    df_merged = pd.merge(
        df_clean,
        weather_avg,
        left_on="start",
        right_on="time",
        how="inner"
    )

    print(f"Merged dataset has {len(df_merged)} rows and {len(df_merged.columns)} columns")
    df_merged
    return (df_merged,)


@app.cell
def _(mo):
    mo.md("""
    **Cell 18 explanation.**
    Wind speed is converted from km/h to m/s (÷3.6) since that's the
    standard unit for wind-power physics and turbine specs. The
    correlation table shows how strongly each weather variable moves
    together with each energy source (Pearson r, from -1 to +1).
    Expect: wind speed <-> wind generation strongly positive, solar
    radiation <-> solar generation strongly positive, cloud cover <->
    solar negative.
    """)
    return


@app.cell
def _(df_merged):
    df_merged["wind_100m_ms"] = df_merged["wind_100m"] / 3.6

    weather_vars = ["wind_100m_ms", "solar_total", "cloud_pct", "temp_C"]
    energy_vars = ["Wind Onshore", "Wind Offshore", "Solar", "Lignite", "Fossil Gas"]

    correlations = df_merged[weather_vars + energy_vars].corr()
    correlations.loc[weather_vars, energy_vars].round(3)
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 19 explanation.**
    Chart 7 — one dot per hour (~2,200 hours). Wind speed vs wind
    generation should look like a curve (not a straight line) — output
    rises steeply then flattens at high wind speeds. Solar radiation
    vs solar generation should look close to a straight line. Cloud
    cover vs solar should trend downward (more cloud, less solar).
    These shapes justify the regression models fit in the next two
    cells.
    """)
    return


@app.cell
def _(df_merged, plt):
    fig5, axes5 = plt.subplots(1, 3, figsize=(18, 6))

    axes5[0].scatter(df_merged["wind_100m_ms"], df_merged["Wind Onshore"], alpha=0.3, s=10, color="#047857")
    axes5[0].set_xlabel("Wind Speed at 100m (m/s)")
    axes5[0].set_ylabel("Wind Onshore Generation (MWh)")
    axes5[0].set_title("Wind Speed → Wind Generation", fontsize=13, fontweight="bold")
    axes5[0].grid(True, alpha=0.3)

    axes5[1].scatter(df_merged["solar_total"], df_merged["Solar"], alpha=0.3, s=10, color="#F59E0B")
    axes5[1].set_xlabel("Solar Radiation (W/m²)")
    axes5[1].set_ylabel("Solar Generation (MWh)")
    axes5[1].set_title("Solar Radiation → Solar Generation", fontsize=13, fontweight="bold")
    axes5[1].grid(True, alpha=0.3)

    axes5[2].scatter(df_merged["cloud_pct"], df_merged["Solar"], alpha=0.3, s=10, color="#64748B")
    axes5[2].set_xlabel("Cloud Cover (%)")
    axes5[2].set_ylabel("Solar Generation (MWh)")
    axes5[2].set_title("Cloud Cover → Solar Generation", fontsize=13, fontweight="bold")
    axes5[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 20 explanation.**
    Wind turbines physically follow output ∝ (wind speed)^3 in their
    normal operating range, so we fit a linear regression using v³ as
    the input feature — this makes a nonlinear physical relationship
    solvable with ordinary linear regression. R² tells us what
    fraction of wind generation's variation is explained by wind speed
    alone (1.0 = all of it, 0.0 = none of it). Known limitation: the
    intercept can come out negative, which isn't physically possible —
    a caveat worth noting in the report rather than a fatal flaw.
    """)
    return


@app.cell
def _(df_merged):
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score, mean_absolute_error

    X = (df_merged["wind_100m_ms"] ** 3).values.reshape(-1, 1)
    y = df_merged["Wind Onshore"].values

    model_wind = LinearRegression()
    model_wind.fit(X, y)
    y_pred = model_wind.predict(X)

    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)

    print(f"Wind power model:  P = {model_wind.coef_[0]:.2f} × v³ + {model_wind.intercept_:.0f}")
    print(f"R² score: {r2:.3f}  (1.0 = perfect, 0.0 = useless)")
    print(f"Mean absolute error: {mae:.0f} MWh")
    print(f"In plain terms: this model explains {r2*100:.1f}% of wind generation from wind speed alone.")
    return LinearRegression, mean_absolute_error, model_wind, r2, r2_score


@app.cell
def _(mo):
    mo.md("""
    **Cell 21 explanation.**
    Solar panel output is approximately linear in incoming radiation
    (more sunlight = proportionally more power), so a plain linear
    regression fits well here — no cubing needed like with wind. R² is
    usually higher than the wind model since solar's relationship to
    radiation is more physically direct and less chaotic than wind.
    """)
    return


@app.cell
def _(LinearRegression, df_merged, mean_absolute_error, r2_score):
    X_solar = df_merged["solar_total"].values.reshape(-1, 1)
    y_solar = df_merged["Solar"].values

    model_solar = LinearRegression()
    model_solar.fit(X_solar, y_solar)
    y_solar_pred = model_solar.predict(X_solar)

    r2_solar = r2_score(y_solar, y_solar_pred)
    mae_solar = mean_absolute_error(y_solar, y_solar_pred)

    print(f"Solar power model:  P = {model_solar.coef_[0]:.2f} × G + {model_solar.intercept_:.0f}")
    print(f"R² score: {r2_solar:.3f}")
    print(f"Mean absolute error: {mae_solar:.0f} MWh")
    print(f"In plain terms: this model explains {r2_solar*100:.1f}% of solar generation from radiation alone.")
    return model_solar, r2_solar


@app.cell
def _(mo):
    mo.md("""
    **Cell 22 explanation.**
    Chart 8 — draws the two regression models from the previous cells
    as smooth red lines on top of the raw scatter points, so we can
    visually check how well each model fits: does the red line run
    through the middle of the point cloud with roughly even scatter
    above and below it?
    """)
    return


@app.cell
def _(df_merged, model_solar, model_wind, np, plt, r2, r2_solar):
    fig6, axes6 = plt.subplots(1, 2, figsize=(16, 6))

    v_range = np.linspace(0, df_merged["wind_100m_ms"].max(), 200)
    P_wind_curve = model_wind.coef_[0] * v_range**3 + model_wind.intercept_

    axes6[0].scatter(df_merged["wind_100m_ms"], df_merged["Wind Onshore"],
                     alpha=0.25, s=8, color="#047857", label="Real data")
    axes6[0].plot(v_range, P_wind_curve, color="#DC2626", linewidth=3,
                  label=f"Model: P = {model_wind.coef_[0]:.1f}·v³ + {model_wind.intercept_:.0f}")
    axes6[0].set_xlabel("Wind Speed at 100m (m/s)", fontsize=12)
    axes6[0].set_ylabel("Wind Onshore Generation (MWh)", fontsize=12)
    axes6[0].set_title(f"Wind Power Curve (R² = {r2:.3f})", fontsize=13, fontweight="bold")
    axes6[0].legend(fontsize=10)
    axes6[0].grid(True, alpha=0.3)

    G_range = np.linspace(0, df_merged["solar_total"].max(), 200)
    P_solar_curve = model_solar.coef_[0] * G_range + model_solar.intercept_

    axes6[1].scatter(df_merged["solar_total"], df_merged["Solar"],
                     alpha=0.25, s=8, color="#F59E0B", label="Real data")
    axes6[1].plot(G_range, P_solar_curve, color="#DC2626", linewidth=3,
                  label=f"Model: P = {model_solar.coef_[0]:.1f}·G + {model_solar.intercept_:.0f}")
    axes6[1].set_xlabel("Solar Radiation (W/m²)", fontsize=12)
    axes6[1].set_ylabel("Solar Generation (MWh)", fontsize=12)
    axes6[1].set_title(f"Solar Linear Response (R² = {r2_solar:.3f})", fontsize=13, fontweight="bold")
    axes6[1].legend(fontsize=10)
    axes6[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 23 explanation.**
    Exports scatter + fitted-curve data for the LaTeX weather figure.
    Scatter points are subsampled (every 3rd hour) to keep pgfplots
    compile time reasonable while preserving the shape of the
    relationship. Two extra CSVs give pgfplots a smooth 100-point line
    for each fitted model, so the report's figure can show data points
    + fitted curve exactly like Chart 8 above, but rendered natively
    in LaTeX.
    """)
    return


@app.cell
def _(df_merged, model_solar, model_wind, np, pd):
    scatter_export = df_merged[[
        "wind_100m_ms", "Wind Onshore", "solar_total", "Solar", "cloud_pct"
    ]].iloc[::3].rename(columns={
        "wind_100m_ms": "Wind_Speed_ms",
        "Wind Onshore": "Wind_Gen_MWh",
        "solar_total": "Solar_Radiation_Wm2",
        "Solar": "Solar_Gen_MWh",
        "cloud_pct": "Cloud_Cover_pct",
    })
    scatter_export.to_csv("outputs/q3/q3_weather_scatter.csv", index=False)

    v_range_csv = np.linspace(0, df_merged["wind_100m_ms"].max(), 100)
    wind_curve_export = pd.DataFrame({
        "Wind_Speed_ms": v_range_csv,
        "Wind_Gen_Fit_MWh": model_wind.coef_[0] * v_range_csv**3 + model_wind.intercept_,
    })
    wind_curve_export.to_csv("outputs/q3/q3_wind_curve.csv", index=False)

    G_range_csv = np.linspace(0, df_merged["solar_total"].max(), 100)
    solar_curve_export = pd.DataFrame({
        "Solar_Radiation_Wm2": G_range_csv,
        "Solar_Gen_Fit_MWh": model_solar.coef_[0] * G_range_csv + model_solar.intercept_,
    })
    solar_curve_export.to_csv("outputs/q3/q3_solar_curve.csv", index=False)

    print("Written: q3_weather_scatter.csv, q3_wind_curve.csv, q3_solar_curve.csv")
    print(f"Wind formula:  P = {model_wind.coef_[0]:.2f} * v^3 + {model_wind.intercept_:.0f}")
    print(f"Solar formula: P = {model_solar.coef_[0]:.2f} * G + {model_solar.intercept_:.0f}")
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 24 explanation.**
    Writes the combined generation+weather data to a single CSV so it
    can be reused without re-running the full pipeline — e.g. by the
    full-year notebook, which concatenates
    merged_q1/q2/q3/q4_2025.csv together.
    """)
    return


@app.cell
def _(df_merged):
    df_merged.to_csv("outputs/q3/merged_q3_2025.csv", index=False)
    print(f"Saved merged_q3_2025.csv ({len(df_merged)} rows)")
    return


@app.cell
def _(mo):
    mo.md("""
    **Cell 25 explanation.**
    A self-contained fallback that computes the renewable share using
    only generation data, without needing the demand CSV. Useful as a
    quick sanity check, or if the demand file isn't available yet — if
    these numbers match the equivalent ones in the headline-metrics
    cell (Cell 5), that's a good sign the demand merge worked
    correctly. The commented-out block inside shows how this cell
    would extend to include demand once available.
    """)
    return


@app.cell
def _(df_clean):
    def _():


        import pandas as pd

        renewables = ["Biomass", "Hydropower", "Wind Offshore", "Wind Onshore",
                      "Solar", "Other Renewable"]
        conventional = ["Lignite", "Hard Coal", "Fossil Gas", "Other Conventional",
                        "Pumped Storage"]

        # --- Generation totals (TWh) ---
        total_renewable_twh = df_clean[renewables].sum().sum() / 1e6   # MWh -> TWh
        total_conventional_twh = df_clean[conventional].sum().sum() / 1e6
        total_generation_twh = total_renewable_twh + total_conventional_twh

        renewable_share_of_generation = total_renewable_twh / total_generation_twh * 100

        print(f"Total renewable generation:     {total_renewable_twh:.2f} TWh")
        print(f"Total conventional generation:  {total_conventional_twh:.2f} TWh")
        print(f"Total domestic generation:      {total_generation_twh:.2f} TWh")
        return print(f"Renewable share of generation:  {renewable_share_of_generation:.1f}%")

        # --- If you have the demand/consumption file, load and merge it here ---
        # df_demand = pd.read_csv(
        #     "data/raw/Actual_consumption_202507010000_202510010000_Hour.csv",
        #     sep=";", thousands=",", encoding="utf-8-sig"
        # )
        # df_demand.columns = ["start", "end", "Total_Load_MWh", ...]  # adjust to actual columns
        # df_demand["start"] = pd.to_datetime(df_demand["start"], format="%b %d, %Y %I:%M %p")
        #
        # df_balance = pd.merge(df_clean, df_demand[["start", "Total_Load_MWh"]], on="start")
        # df_balance["Total_Renewable_MWh"] = df_balance[renewables].sum(axis=1)
        # df_balance["Residual_Load_MWh"] = df_balance["Total_Load_MWh"] - df_balance["Total_Renewable_MWh"]
        #
        # total_demand_twh = df_balance["Total_Load_MWh"].sum() / 1e6
        # renewable_share_of_demand = df_balance["Total_Renewable_MWh"].sum() / df_balance["Total_Load_MWh"].sum() * 100
        # avg_residual_load = df_balance["Residual_Load_MWh"].mean()
        # max_residual_load = df_balance["Residual_Load_MWh"].max()
        # hours_renewables_met_demand = (df_balance["Residual_Load_MWh"] < 0).sum()
        #
        # net_export_proxy = (df_balance["Total_Renewable_MWh"] + df_balance[conventional].sum(axis=1)
        #                      - df_balance["Total_Load_MWh"])
        # net_export_hours = (net_export_proxy > 0).sum()
        # net_import_hours = (net_export_proxy < 0).sum()
        #
        # print(f"\\nTotal electricity demand:       {total_demand_twh:.2f} TWh")
        # print(f"Renewable share of demand:      {renewable_share_of_demand:.1f}%")
        # print(f"Average residual load:          {avg_residual_load:,.0f} MWh/h")
        # print(f"Maximum residual load:          {max_residual_load:,.0f} MWh/h")
        # print(f"Hours renewables met demand:    {hours_renewables_met_demand}")
        # print(f"Net-export hours (proxy):       {net_export_hours}")
        # print(f"Net-import hours (proxy):       {net_import_hours}")


    _()
    return


if __name__ == "__main__":
    app.run()
