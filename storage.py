import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import pandas as pd
    import requests
    import matplotlib.pyplot as plt
    import seaborn as sns
    import matplotlib.dates as mdates
    import plotly.express as px
    import zipfile
    import io
    import re
    import marimo as mo
    from open_mastr import Mastr
    from pathlib import Path
    import os
    from sqlalchemy import inspect
    from utils import load_smard_series
    from utils import load_smard_market_trade

    return (
        Mastr,
        inspect,
        io,
        load_smard_market_trade,
        load_smard_series,
        mdates,
        mo,
        pd,
        plt,
        px,
        re,
        requests,
        sns,
        zipfile,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # German Energy System Analysis (STAGES Project)

    This project analyzes:
    - SMARD electricity generation data
    - DWD weather observations
    - Renewable energy behavior
    - Relationship between weather and power generation
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Loading SMARD Renewable Energy Generation Data
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Define Analysis Time Period
    """)
    return


@app.cell
def _():
    start_date = "2025-01-01"
    end_date = "2026-01-01"
    return end_date, start_date


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Loading SMARD Electricity Generation Data

    This section loads hourly electricity generation data from the SMARD platform for Germany.
    https://github.com/bundesAPI/smard-api/blob/main/openapi.yaml

    The dataset includes:
    - Renewable energy sources
    - Conventional energy sources
    - Hourly production values
    - National-level electricity generation
    """)
    return


@app.cell
def _(end_date, load_smard_series, start_date):
    smard_filters = {
        "Biomass": 4066,
        "Hydropower": 1226,
        "Wind Offshore": 1225,
        "Wind Onshore": 4067,
        "Solar": 4068,
        "Other Renewable": 1228,
        "Nuclear": 1224,
        "Lignite": 1223,
        "Hard Coal": 4069,
        "Fossil Gas": 4071,
        "Hydro Pumped Storage": 4070,
        "Other Conventional": 1227,
    }

    dfs = []

    for name, filter_id in smard_filters.items():
        print(f"Loading {name}...")
        dfs.append(
            load_smard_series(
                filter_id=filter_id,
                name=name,
                start_date=start_date,
                end_date=end_date,
                region="DE",
                resolution="hour",
            )
        )

    df_smard_generation = dfs[0]

    for df_source in dfs[1:]:
        df_smard_generation = df_smard_generation.merge(
            df_source,
            on="Start date",
            how="outer"
        )

    df_smard_generation = df_smard_generation.sort_values("Start date").fillna(0)

    df_smard_generation.head()
    return (df_smard_generation,)


@app.cell
def _():
    energy_cols = [
        "Biomass",
        "Hydropower",
        "Wind Offshore",
        "Wind Onshore",
        "Solar",
        "Other Renewable",
        "Lignite",
        "Hard Coal",
        "Fossil Gas",
        "Hydro Pumped Storage",
        "Other Conventional",
    ]

    renewable_cols = [
        "Biomass",
        "Hydropower",
        "Wind Offshore",
        "Wind Onshore",
        "Solar",
        "Other Renewable",
    ]

    conventional_cols = [
        "Lignite",
        "Hard Coal",
        "Fossil Gas",
        "Hydro Pumped Storage",
        "Other Conventional",
    ]
    return conventional_cols, energy_cols, renewable_cols


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Visualization of Renewable Energy Generation

    This section visualizes hourly renewable electricity generation in Germany using interactive time-series plots.

    The visualization includes:
    - Biomass
    - Hydropower
    - Wind Offshore
    - Wind Onshore
    - Solar
    - Other Renewable Sources
    """)
    return


@app.cell
def _(df_smard_generation, pd, px, renewable_cols):
    df_interactive = df_smard_generation.copy()
    df_interactive["Start date"] = pd.to_datetime(df_interactive["Start date"])

    df_renewables_interactive = df_interactive.melt(
        id_vars="Start date",
        value_vars=renewable_cols,
        var_name="Source",
        value_name="Production [MWh]",
    )

    fig_renewable = px.line(
        df_renewables_interactive,
        x="Start date",
        y="Production [MWh]",
        color="Source",
        title="Renewable Energy Sources - Jan to Dec 2025"
    )

    fig_renewable.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date"
        ),
        height=500
    )

    fig_renewable.show()
    return (df_interactive,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Interactive Visualization of Conventional Energy Generation

    This section visualizes hourly conventional electricity generation in Germany using interactive time-series plots.

    The visualization includes:
    - Lignite
    - Hard Coal
    - Fossil Gas
    - Hydro Pumped Storage
    - Other Conventional Sources
    """)
    return


@app.cell
def _(conventional_cols, df_interactive, px):
    df_conventional_interactive = df_interactive.melt(
        id_vars="Start date",
        value_vars=conventional_cols,
        var_name="Source",
        value_name="Production [MWh]",
    )

    fig_conventional = px.line(
        df_conventional_interactive,
        x="Start date",
        y="Production [MWh]",
        color="Source",
        title="Conventional Energy Sources - Oct to Dec 2025"
    )

    fig_conventional.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date"
        ),
        height=500
    )
    fig_conventional.update_traces(
        hovertemplate=
        "<b>%{fullData.name}</b><br>" +
        "Date=%{x}<br>" +
        "Energy=%{y:,.0f} MWh"
    )


    fig_conventional.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    y conventional energy(lignite and fossil fuel) contribution is less on winter?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Electricity generation in Germany in the fourth quarter of 2025 was 117.3 TWh, 3.2% higher than in the same quarter of 2024, while consumption was 124.3 TWh and 2.4% higher. The average day-ahead wholesale electricity price was €93.15/MWh, 9.2% lower than a year earlier. Germany was a net importer in commercial foreign trade.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The renewable and conventional generation profiles show clear seasonal compensation effects throughout 2025. During spring and summer months, especially from April to September, solar energy generation increased significantly due to higher solar radiation and longer sunshine duration. This increase partially compensated for lower wind-based renewable generation and reduced conventional generation during these periods.

    In contrast, during autumn and winter months, solar generation decreased considerably, while Wind Onshore generation increased and contributed more strongly to the electricity supply. At the same time, conventional energy sources such as Fossil Gas and Lignite also showed increased production during colder months, helping maintain system stability and satisfy higher electricity demand.

    The larger generation-demand gaps observed during July and August can likely be associated with reduced conventional energy generation, particularly lower Fossil Gas and Lignite production during these months. Although solar generation reached high levels during summer, the reduction in conventional backup generation appears to have contributed to the larger energy deficits observed in mid-year periods. This indicates that high solar production alone was not sufficient to fully compensate for reduced conventional generation and national electricity demand.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The reduced conventional electricity generation observed during summer months is likely associated with increased renewable energy production, particularly solar power generation. Since renewable electricity receives priority within the German electricity market, conventional sources such as Fossil Gas and Lignite are often reduced when renewable availability is high. Additional contributing factors may include lower seasonal industrial demand and planned maintenance periods for conventional power plants. However, despite increased solar generation during summer, total domestic electricity generation still remained below national electricity demand, indicating that solar generation alone was insufficient to fully compensate for reduced conventional generation.
    """)
    return


@app.cell
def _(
    conventional_cols,
    df_smard_generation,
    mdates,
    pd,
    plt,
    renewable_cols,
    sns,
):
    df_plot = df_smard_generation.copy()
    df_plot["Start date"] = pd.to_datetime(df_plot["Start date"])

    plot_start = "2025-10-01"
    plot_end = "2025-10-04"

    df_timed = df_plot[
        (df_plot["Start date"] >= plot_start) &
        (df_plot["Start date"] < plot_end)
    ]

    df_renewables_timed = df_timed.melt(
        id_vars="Start date",
        value_vars=renewable_cols,
        var_name="Source",
        value_name="Production [MWh]",
    )

    df_conventionals_timed = df_timed.melt(
        id_vars="Start date",
        value_vars=conventional_cols,
        var_name="Source",
        value_name="Production [MWh]",
    )

    sns.set_theme(style="darkgrid")

    fig, axes = plt.subplots(2, 1, figsize=(18, 10))

    sns.lineplot(
        data=df_renewables_timed,
        x="Start date",
        y="Production [MWh]",
        hue="Source",
        ax=axes[0],
        linewidth=2,
    )

    axes[0].set_title("Renewable Energy Sources - Timely View")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Production [MWh]")

    sns.lineplot(
        data=df_conventionals_timed,
        x="Start date",
        y="Production [MWh]",
        hue="Source",
        ax=axes[1],
        linewidth=2,
    )

    axes[1].set_title("Conventional Energy Sources - Timely View")
    axes[1].set_xlabel("Date & Time")
    axes[1].set_ylabel("Production [MWh]")

    for plot_axis in axes:
        plot_axis.xaxis.set_major_formatter(
            mdates.DateFormatter("%d-%b %H:%M")
        )
        plot_axis.xaxis.set_major_locator(
            mdates.HourLocator(interval=6)
        )
        plot_axis.tick_params(axis="x", rotation=45)

    axes[0].legend(loc="upper left", bbox_to_anchor=(1.01, 1))
    axes[1].legend(loc="upper left", bbox_to_anchor=(1.01, 1))

    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Loading SMARD Electricity Consumption and Load Data

    This section loads hourly electricity consumption and grid load data from the SMARD platform for Germany.

    The dataset includes:
    - Total electricity consumption
    - Grid load including hydro pumped storage
    - Hydro pumped storage consumption
    - Residual load
    """)
    return


@app.cell
def _(end_date, load_smard_series, start_date):
    consumption_filters = {
        "Consumption": 410,
        "Grid Load incl. Hydro Pumped Storage": 4359,
        "Hydro Pumped Storage Consumption": 4387,
        "Residual Load": 4355,
    }

    dfs_cons = []

    for cons_name, cons_filter_id in consumption_filters.items():
        print(f"Loading {cons_name}...")

        df_cons_temp = load_smard_series(
            filter_id=cons_filter_id,
            name=cons_name,
            start_date=start_date,
            end_date=end_date,
            region="DE",
            resolution="hour",
        )

        dfs_cons.append(df_cons_temp)

    df_smard_consumption = dfs_cons[0]

    for df_cons_source in dfs_cons[1:]:
        df_smard_consumption = df_smard_consumption.merge(
            df_cons_source,
            on="Start date",
            how="outer"
        )

    df_smard_consumption = df_smard_consumption.sort_values("Start date").fillna(0)

    df_smard_consumption.head()
    return (df_smard_consumption,)


@app.cell
def _(df_smard_consumption, mdates, pd, plt):
    df_cons_plot = df_smard_consumption.copy()

    df_cons_plot["Start date"] = pd.to_datetime(
        df_cons_plot["Start date"]
    )

    cons_plot_start = "2025-10-01"
    cons_plot_end = "2025-10-04"

    df_cons_timed = df_cons_plot[
        (df_cons_plot["Start date"] >= cons_plot_start) &
        (df_cons_plot["Start date"] < cons_plot_end)
    ]

    plt.figure(figsize=(18, 6))

    plt.plot(
        df_cons_timed["Start date"],
        df_cons_timed["Consumption"],
        label="Consumption",
        linewidth=2,
    )

    plt.plot(
        df_cons_timed["Start date"],
        df_cons_timed["Residual Load"],
        label="Residual Load",
        linewidth=2,
    )

    plt.plot(
        df_cons_timed["Start date"],
        df_cons_timed["Grid Load incl. Hydro Pumped Storage"],
        label="Grid Load incl. Hydro Pumped Storage",
        linewidth=2,
    )

    plt.title("Electricity Consumption - Timely View")
    plt.xlabel("Date & Time")
    plt.ylabel("Energy [MWh]")

    cons_axis = plt.gca()

    cons_axis.xaxis.set_major_formatter(
        mdates.DateFormatter("%d-%b %H:%M")
    )

    cons_axis.xaxis.set_major_locator(
        mdates.HourLocator(interval=6)
    )

    plt.xticks(rotation=45)

    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Comparison of Renewable Generation, Conventional Generation, and Electricity Demand

    This section compares the temporal behavior of:
    - Total renewable electricity generation
    - Total conventional electricity generation
    - National electricity consumption in Germany
    """)
    return


@app.cell
def _(
    conventional_cols,
    df_smard_consumption,
    df_smard_generation,
    pd,
    px,
    renewable_cols,
):
    df_compare_interactive = df_smard_generation.copy()

    df_compare_interactive["Start date"] = pd.to_datetime(
        df_compare_interactive["Start date"]
    )

    df_compare_interactive["Total Renewable Generation"] = (
        df_compare_interactive[renewable_cols].sum(axis=1)
    )

    df_compare_interactive["Total Conventional Generation"] = (
        df_compare_interactive[conventional_cols].sum(axis=1)
    )

    df_compare_interactive = df_compare_interactive.merge(
        df_smard_consumption[["Start date", "Consumption"]],
        on="Start date",
        how="inner",
    )

    df_compare_long = df_compare_interactive.melt(
        id_vars="Start date",
        value_vars=[
            "Total Renewable Generation",
            "Total Conventional Generation",
            "Consumption",
        ],
        var_name="Category",
        value_name="Energy [MWh]",
    )

    fig_compare = px.line(
        df_compare_long,
        x="Start date",
        y="Energy [MWh]",
        color="Category",
        title="Renewable vs Conventional Generation vs Electricity Demand"
    )

    fig_compare.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date"
        ),
        height=550
    )

    fig_compare.update_traces(
        hovertemplate=
        "<b>%{fullData.name}</b><br>" +
        "Date=%{x}<br>" +
        "Energy=%{y:,.0f} MWh"
    )

    fig_compare.show()
    return (df_compare_interactive,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Monthly Renewable Energy Balance Analysis

    This section evaluates the monthly balance between renewable electricity generation and electricity demand in Germany.

    The analysis includes:
    - Total renewable electricity generation
    - Total electricity demand
    - Demand covered by renewable sources
    - Remaining unmet demand
    - Renewable energy share
    - Minimum renewable generation
    - Maximum renewable generation
    """)
    return


@app.cell
def _(df_smard_consumption, df_smard_generation, pd, renewable_cols):
    df_monthly_balance = df_smard_generation.copy()

    df_monthly_balance["Start date"] = pd.to_datetime(
        df_monthly_balance["Start date"]
    )

    df_monthly_balance["Month"] = df_monthly_balance["Start date"].dt.strftime("%b 2025")

    df_monthly_balance["Total Renewable Generation"] = df_monthly_balance[
        renewable_cols
    ].sum(axis=1)

    df_monthly_balance = df_monthly_balance.merge(
        df_smard_consumption[["Start date", "Consumption"]],
        on="Start date",
        how="inner",
    )

    monthly_summary = df_monthly_balance.groupby("Month").agg(
        Total_Renewable_Generation_MWh=("Total Renewable Generation", "sum"),
        Total_Demand_MWh=("Consumption", "sum"),
    )

    monthly_summary["Demand Met by Renewables [MWh]"] = monthly_summary[
        ["Total_Renewable_Generation_MWh", "Total_Demand_MWh"]
    ].min(axis=1)

    monthly_summary["Remaining Demand [MWh]"] = (
        monthly_summary["Total_Demand_MWh"]
        - monthly_summary["Demand Met by Renewables [MWh]"]
    )

    monthly_summary["Renewable Share [%]"] = (
        monthly_summary["Demand Met by Renewables [MWh]"]
        / monthly_summary["Total_Demand_MWh"]
    ) * 100

    monthly_summary["Minimum Renewable Generation [MWh]"] = (
        df_monthly_balance.groupby("Month")[
            "Total Renewable Generation"
        ].min()
    )

    monthly_summary["Maximum Renewable Generation [MWh]"] = (
        df_monthly_balance.groupby("Month")[
            "Total Renewable Generation"
        ].max()
    )

    monthly_summary = monthly_summary.reindex([
        "Jan 2025",
        "Feb 2025",
        "Mar 2025",
        "Apr 2025",
        "May 2025",
        "Jun 2025",
        "Jul 2025",
        "Aug 2025",
        "Sep 2025",
        "Oct 2025",
        "Nov 2025",
        "Dec 2025",
    ])
    monthly_summary = monthly_summary.round(3)
    monthly_summary
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Monthly Electricity Generation by Energy Source
    """)
    return


@app.cell
def _(df_smard_generation, energy_cols, pd, plt):
    df_monthly = df_smard_generation.copy()

    df_monthly["Start date"] = pd.to_datetime(df_monthly["Start date"])

    df_monthly["Month"] = df_monthly["Start date"].dt.strftime("%b 2025")

    monthly_generation = df_monthly.groupby("Month")[energy_cols].sum()

    monthly_generation = monthly_generation.reindex([
        "Jan 2025",
        "Feb 2025",
        "Mar 2025",
        "Apr 2025",
        "May 2025",
        "Jun 2025",
        "Jul 2025",
        "Aug 2025",
        "Sep 2025",
        "Oct 2025",
        "Nov 2025",
        "Dec 2025",
    ])

    monthly_generation.plot(
        kind="bar",
        stacked=True,
        figsize=(14, 7)
    )

    plt.title("Monthly Energy Generation by Source - Oct to Dec 2025")
    plt.xlabel("Month")
    plt.ylabel("Energy Generated [MWh]")

    plt.xticks(rotation=0)
    plt.legend(
        title="Energy Source",
        bbox_to_anchor=(1.02, 1),
        loc="upper left"
    )

    plt.grid(axis="y")

    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##Extra energy needed to import
    Total difference = total demand - total generation
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The statistical analysis of Germany’s electricity system in 2025 indicates that total electricity demand consistently exceeded total domestic electricity generation throughout the year. Monthly demand values ranged approximately between 35 million MWh and 44 million MWh, while total electricity generation varied between nearly 32 million MWh and 42 million MWh.

    The highest electricity demand was recorded during winter months, particularly in January and December, where demand exceeded 42 million MWh. At the same time, electricity generation also increased during these months, reaching nearly 39–42 million MWh, mainly supported by stronger wind generation and increased conventional energy production. However, generation still remained below demand levels.

    The lowest total generation occurred during summer months, especially in July and August, where total generation dropped to approximately 32–34 million MWh. During the same period, electricity demand remained comparatively high at around 35–37 million MWh. Consequently, the largest monthly deficits were observed in July (-3.43 million MWh) and August (-3.38 million MWh), indicating a significant gap between electricity production and consumption.

    The energy mix analysis further shows that renewable energy sources such as Wind Onshore and Solar contributed substantially to total electricity generation. Solar generation increased strongly during spring and summer months due to higher solar radiation and longer sunshine duration, while wind generation became more dominant during autumn and winter months. Despite this strong renewable contribution, conventional sources such as Fossil Gas and Hard Coal continued to provide a considerable share of electricity generation throughout the year, supporting grid stability and compensating for renewable variability.

    The monthly negative energy balance observed in all months suggests that Germany’s domestic electricity generation capacity alone was insufficient to fully satisfy national electricity demand during 2025. Therefore, the electricity system likely relied on electricity imports, storage systems, or reserve generation capacities to maintain supply reliability and grid stability.

    Overall, the results demonstrate both the increasing importance of renewable energy sources and the continuing need for conventional backup systems and external balancing mechanisms within Germany’s energy system.
    """)
    return


@app.cell
def _(
    conventional_cols,
    df_smard_consumption,
    df_smard_generation,
    renewable_cols,
):
    # Calculate total renewable generation
    df_check = df_smard_generation.copy()

    df_check["Total Renewable Generation"] = (
        df_check[renewable_cols].sum(axis=1)
    )

    # Calculate total conventional generation
    df_check["Total Conventional Generation"] = (
        df_check[conventional_cols].sum(axis=1)
    )

    # Total generation
    df_check["Total Generation"] = (
        df_check["Total Renewable Generation"]
        + df_check["Total Conventional Generation"]
    )

    # Merge with demand/consumption data
    df_check = df_check.merge(
        df_smard_consumption[["Start date", "Consumption"]],
        on="Start date",
        how="inner"
    )

    # Difference between generation and demand
    df_check["Difference"] = (
        df_check["Total Generation"]
        - df_check["Consumption"]
    )

    # Check if approximately equal
    tolerance = 1e-3

    df_check["Generation Equals Demand"] = (
        df_check["Difference"].abs() < tolerance
    )

    # Show first rows
    df_check[[
        "Start date",
        "Total Renewable Generation",
        "Total Conventional Generation",
        "Total Generation",
        "Consumption",
        "Difference",
        "Generation Equals Demand"
    ]].head()
    return (df_check,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Plotting monthly difference in demand and generation
    """)
    return


@app.cell
def _(df_check, plt):
    df_check["Month"] = df_check["Start date"].dt.strftime("%b %Y")

    monthly_check = df_check.groupby("Month").agg(
        Total_Generation_MWh=("Total Generation", "sum"),
        Total_Demand_MWh=("Consumption", "sum"),
        Total_Difference_MWh=("Difference", "sum")
    )

    month_order = [
        "Jan 2025",
        "Feb 2025",
        "Mar 2025",
        "Apr 2025",
        "May 2025",
        "Jun 2025",
        "Jul 2025",
        "Aug 2025",
        "Sep 2025",
        "Oct 2025",
        "Nov 2025",
        "Dec 2025",
    ]

    monthly_check = monthly_check.reindex(month_order)

    monthly_check[
        [
            "Total_Generation_MWh",
            "Total_Demand_MWh"
        ]
    ].plot(
        kind="bar",
        figsize=(15, 7)
    )

    plt.title(
        "Monthly Total Electricity Generation vs Demand - 2025"
    )

    plt.xlabel("Month")
    plt.ylabel("Energy [MWh]")

    plt.xticks(rotation=45)

    plt.grid(axis="y")

    plt.tight_layout()

    plt.show()

    monthly_check
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    https://www.smard.de/page/en/topic-article/217400/219570/records-for-solar-and-wind-offshore
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The monthly electricity generation analysis for 2025 demonstrates that Germany’s energy production was supplied through a combination of renewable and conventional energy sources. Wind Onshore, Solar, and Fossil Gas were among the dominant contributors throughout the year, while Biomass, Hydropower, and Wind Offshore provided relatively stable contributions across all months.

    A strong seasonal variation can be observed in renewable generation patterns. Solar energy production increased significantly during spring and summer months, particularly between May and August, due to higher solar radiation and longer sunshine duration. In contrast, solar generation declined during winter months such as January, November, and December. Wind Onshore generation showed comparatively strong contributions during autumn and winter periods, helping compensate for reduced solar output.

    Conventional energy sources, especially Fossil Gas and Hard Coal, continued to play an important stabilizing role in maintaining electricity supply. Their contribution remained substantial throughout the year, indicating that renewable sources alone were not sufficient to satisfy national electricity demand consistently.

    When comparing total generation with electricity demand, it can be concluded that electricity demand exceeded total domestic generation during all observed months of 2025. This resulted in a persistent negative energy balance, indicating that Germany likely relied on electricity imports, storage systems, or reserve generation capacities to ensure grid stability and meet national demand requirements.

    The largest generation-demand gaps occurred during several summer months, despite increased solar production, suggesting that renewable variability and overall generation capacity were still insufficient to fully satisfy demand. During winter months, electricity demand increased further due to seasonal heating and lighting requirements, while conventional generation sources contributed significantly to maintaining supply reliability.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The statistical analysis of Germany’s electricity system in 2025 indicates that total electricity demand consistently exceeded total domestic electricity generation throughout the year. Monthly demand values ranged from approximately 35 million MWh to 44 million MWh, while total electricity generation ranged from nearly 32 million MWh to 42 million MWh.

    The highest electricity demand was recorded during winter months, particularly in January and December, where demand exceeded 42 million MWh. At the same time, electricity generation also increased during these months, reaching nearly 39–42 million MWh, mainly supported by stronger wind generation and increased conventional energy production. However, generation still remained below demand levels.

    The lowest total generation occurred during summer months, especially in July and August, where total generation dropped to approximately 32–34 million MWh. During the same period, electricity demand remained comparatively high at around 35–37 million MWh. Consequently, the largest monthly deficits were observed in July (-3.43 million MWh) and August (-3.38 million MWh), indicating a significant gap between electricity production and consumption.

    The energy mix analysis further shows that renewable energy sources such as Wind Onshore and Solar contributed substantially to total electricity generation. Solar generation increased strongly during spring and summer months due to higher solar radiation and longer sunshine duration, while wind generation became more dominant during autumn and winter months. Despite this strong renewable contribution, conventional sources such as Fossil Gas and Hard Coal continued to provide a considerable share of electricity generation throughout the year, supporting grid stability and compensating for renewable variability.

    The monthly negative energy balance observed in all months suggests that Germany’s domestic electricity generation capacity alone was insufficient to fully satisfy national electricity demand during 2025. Therefore, the electricity system likely relied on electricity imports, storage systems, or reserve generation capacities to maintain supply reliability and grid stability.

    Overall, the results demonstrate both the increasing importance of renewable energy sources and the continuing need for conventional backup systems and external balancing mechanisms within Germany’s energy system.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The largest amounts of electricity imported into Germany were from Denmark (5.6 TWh), France (4.3 TWh) and the Netherlands (3.7 TWh).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##Slightly higher imports and considerably higher exports
    Germany exported a total of 15.7 TWh of electricity in Q4 2025, 18.6% more than in Q4 2024. The higher level of generation by renewables overall contributed to this increase. Imports rose by 4.5% to 19.8 TWh, bringing net imports down by 28.7% to 4.0 TWh. While imports in November and December by far exceeded exports, net imports in October were only about 0.1 TWh.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    why does germany export their energy when they are not sufficient and need import

             1) generation temporarily exceeds demand Germany may produce more electricity than it currently needs
             2) Electricity prices Germany sometimes exports because:electricity prices become very low
             3)Nuclear example France often exports nuclear electricity to Germany because:
             French nuclear power is stable sometimes cheaper at night
    Meanwhile Germany may export:
    wind electricity
    solar electricity
    during high renewable periods.

    Germany can simultaneously act as both an electricity importer and exporter because electricity trading occurs dynamically within the interconnected European power grid. During periods of high renewable generation, particularly during strong wind or solar conditions, Germany may temporarily generate surplus electricity and export it to neighboring countries. Conversely, during periods of lower renewable generation or higher demand, Germany imports electricity to maintain grid stability. Therefore, although the overall annual balance may indicate a generation deficit, electricity exports still occur during specific periods of temporary surplus production.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    so why can germany store excess energy and use it later when deficit

    large-scale electricity storage is still limited and expensive.

    Current storage systems are limited

    Renewable generation is highly variable

    Batteries are expensive at national scale

    Exporting is economically easier

    European grid acts like a “shared storage system”

    Although Germany can store a portion of excess renewable electricity using technologies such as pumped hydro storage and battery systems, current storage capacities remain insufficient for long-term national-scale energy balancing. Renewable electricity production, particularly from solar and wind sources, is highly variable and seasonal, while electricity demand remains continuous throughout the year. As a result, excess renewable energy generated during high-production periods cannot always be stored efficiently for later use. Consequently, Germany often exports surplus electricity during periods of high renewable generation and imports electricity during periods of lower domestic production. The interconnected European electricity grid therefore plays a crucial role in balancing supply and demand across the region.
    """)
    return


@app.cell
def _(end_date, load_smard_market_trade, start_date):
    df_smard_trade = load_smard_market_trade(
        start_date=start_date,
        end_date=end_date
    )

    df_smard_trade.head()
    return (df_smard_trade,)


@app.cell
def _(df_smard_trade):
    df_smard_trade.columns.tolist()
    return


@app.cell
def _(df_smard_trade):
    export_cols = [
        col for col in df_smard_trade.columns
        if "(export)" in col.lower()
    ]

    import_cols = [
        col for col in df_smard_trade.columns
        if "(import)" in col.lower()
    ]

    # Convert imports to positive values
    df_smard_trade[import_cols] = (
        df_smard_trade[import_cols]
        .abs()
    )

    # Total export
    df_smard_trade["Total_Export_MWh"] = (
        df_smard_trade[export_cols]
        .sum(axis=1)
    )

    # Total import
    df_smard_trade["Total_Import_MWh"] = (
        df_smard_trade[import_cols]
        .sum(axis=1)
    )

    # Net trade balance
    # Positive = net exporter
    # Negative = net importer
    df_smard_trade["Net_Trade_MWh"] = (
        df_smard_trade["Total_Export_MWh"]
        - df_smard_trade["Total_Import_MWh"]
    )

    df_smard_trade[
        [
            "Start date",
            "Total_Export_MWh",
            "Total_Import_MWh",
            "Net_Trade_MWh"
        ]
    ].head()
    return


@app.cell
def _(df_smard_trade):
    # Create month column
    df_smard_trade["Month"] = (
        df_smard_trade["Start date"]
        .dt.to_period("M")
        .astype(str)
    )

    # Monthly export/import totals
    df_trade_monthly = (
        df_smard_trade
        .groupby("Month")[
            [
                "Total_Export_MWh",
                "Total_Import_MWh",
                "Net_Trade_MWh"
            ]
        ]
        .sum()
        .reset_index()
    )

    df_trade_monthly
    return (df_trade_monthly,)


@app.cell
def _(df_trade_monthly, px):
    fig_trade = px.bar(
        df_trade_monthly,
        x="Month",
        y=[
            "Total_Export_MWh",
            "Total_Import_MWh"
        ],
        barmode="group",
        title="Monthly Electricity Export vs Import in Germany (2025)",
        labels={
            "value": "Energy [MWh]",
            "variable": "Trade Type"
        }
    )

    fig_trade.update_layout(
        xaxis_title="Month",
        yaxis_title="Energy [MWh]",
        height=550
    )

    fig_trade.update_traces(
        hovertemplate=
        "<b>%{fullData.name}</b><br>" +
        "Month=%{x}<br>" +
        "Energy=%{y:,.0f} MWh"
    )

    fig_trade.show()
    return


@app.cell
def _(df_smard_trade):
    # Detect all export/import country columns

    country_export_cols = [
        col for col in df_smard_trade.columns
        if "(export)" in col.lower()
    ]

    country_import_cols = [
        col for col in df_smard_trade.columns
        if "(import)" in col.lower()
    ]

    # Create month column
    df_country_trade = df_smard_trade.copy()

    df_country_trade["Month"] = (
        df_country_trade["Start date"]
        .dt.to_period("M")
        .astype(str)
    )

    # Monthly exports by country
    monthly_country_exports = (
        df_country_trade
        .groupby("Month")[country_export_cols]
        .sum()
        .reset_index()
    )

    # Monthly imports by country
    monthly_country_imports = (
        df_country_trade
        .groupby("Month")[country_import_cols]
        .sum()
        .reset_index()
    )

    monthly_country_exports
    return monthly_country_exports, monthly_country_imports


@app.cell
def _(monthly_country_imports):
    monthly_country_imports
    return


@app.cell
def _(monthly_country_exports, monthly_country_imports):
    # Total export for whole 2025
    total_exports_by_country = (
        monthly_country_exports
        .drop(columns="Month")
        .sum()
        .sort_values(ascending=False)
    )

    # Total import for whole 2025
    total_imports_by_country = (
        monthly_country_imports
        .drop(columns="Month")
        .sum()
        .sort_values(ascending=False)
    )

    print("Top Export Countries")
    print(total_exports_by_country)

    print("\nTop Import Countries")
    print(total_imports_by_country)
    return


@app.cell
def _(monthly_country_exports, monthly_country_imports, pd, plt):
    # Total exports by country
    total_exports_compare = (
        monthly_country_exports
        .drop(columns="Month")
        .sum()
    )

    # Total imports by country
    total_imports_compare = (
        monthly_country_imports
        .drop(columns="Month")
        .sum()
    )

    # Clean country names
    export_names = (
        total_exports_compare.index
        .str.replace(" (export)", "", regex=False)
    )

    import_names = (
        total_imports_compare.index
        .str.replace(" (import)", "", regex=False)
    )

    # Create comparison dataframe
    df_trade_compare = pd.DataFrame({
        "Country": export_names,
        "Export [MWh]": total_exports_compare.values,
        "Import [MWh]": total_imports_compare.values
    })

    # Sort by total trade volume
    df_trade_compare["Total Trade"] = (
        df_trade_compare["Export [MWh]"]
        + df_trade_compare["Import [MWh]"]
    )

    df_trade_compare = df_trade_compare.sort_values(
        "Total Trade",
        ascending=False
    )

    # Plot
    plt.figure(figsize=(16, 8))

    x = range(len(df_trade_compare))

    bar_width = 0.4

    plt.bar(
        [i - bar_width/2 for i in x],
        df_trade_compare["Export [MWh]"],
        width=bar_width,
        label="Export"
    )

    plt.bar(
        [i + bar_width/2 for i in x],
        df_trade_compare["Import [MWh]"],
        width=bar_width,
        label="Import"
    )

    plt.xticks(
        x,
        df_trade_compare["Country"],
        rotation=45
    )

    plt.title(
        "Germany Electricity Import vs Export by Country - 2025"
    )

    plt.xlabel("Country")
    plt.ylabel("Energy [MWh]")

    plt.legend()

    plt.grid(axis="y")

    plt.tight_layout()

    plt.show()
    return


@app.cell
def _(df_compare_interactive, df_trade_monthly):
    df_monthly_system_check = df_compare_interactive.copy()

    df_monthly_system_check["Month"] = (
        df_monthly_system_check["Start date"]
        .dt.to_period("M")
        .astype(str)
    )

    df_monthly_system_check = (
        df_monthly_system_check
        .groupby("Month")[
            [
                "Total Renewable Generation",
                "Total Conventional Generation",
                "Consumption"
            ]
        ]
        .sum()
        .reset_index()
    )

    df_demand_balance_check = df_monthly_system_check.merge(
        df_trade_monthly[
            [
                "Month",
                "Total_Export_MWh",
                "Total_Import_MWh"
            ]
        ],
        on="Month",
        how="inner"
    )

    df_demand_balance_check["Available_Energy_MWh"] = (
        df_demand_balance_check["Total Renewable Generation"]
        + df_demand_balance_check["Total Conventional Generation"]
        + df_demand_balance_check["Total_Import_MWh"]
        - df_demand_balance_check["Total_Export_MWh"]
    )

    df_demand_balance_check["Balance_MWh"] = (
        df_demand_balance_check["Available_Energy_MWh"]
        - df_demand_balance_check["Consumption"]
    )

    df_demand_balance_check["Demand_Met"] = (
        df_demand_balance_check["Balance_MWh"] >= 0
    )

    df_demand_balance_check
    return (df_demand_balance_check,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Remaining mismatch is actually small

    Example from table:

    Demand ≈ 44 million MWh
    Gap ≈ 1 million MWh

    That is only around:

    44
    1
    	​

    ×100≈2.3%

    A ~2–3% mismatch in aggregated energy-system analysis is very normal.

    So results are actually realistic.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Germany plays a central role in the European interconnected electricity grid.
    The country imports and exports electricity depending on renewable generation, demand, and market conditions.
    Even when domestic generation is lower than consumption, imports and conventional generation help maintain grid stability.
    The results show that the European grid enables energy balancing between countries and supports reliable electricity supply.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Hypothetical trial
    """)
    return


@app.cell
def _(df_demand_balance_check):
    df_storage_scenario = df_demand_balance_check.copy()

    storage_efficiency = 0.80

    df_storage_scenario["Recoverable_Export_MWh"] = (
        df_storage_scenario["Total_Export_MWh"] * storage_efficiency
    )

    df_storage_scenario["Reduced_Import_Need_MWh"] = (
        df_storage_scenario["Total_Import_MWh"]
        - df_storage_scenario["Recoverable_Export_MWh"]
    ).clip(lower=0)

    df_storage_scenario["Import_Reduction_MWh"] = (
        df_storage_scenario["Total_Import_MWh"]
        - df_storage_scenario["Reduced_Import_Need_MWh"]
    )

    df_storage_scenario["Import_Reduction_%"] = (
        df_storage_scenario["Import_Reduction_MWh"]
        / df_storage_scenario["Total_Import_MWh"]
        * 100
    )

    df_storage_scenario[
        [
            "Month",
            "Total_Export_MWh",
            "Total_Import_MWh",
            "Recoverable_Export_MWh",
            "Reduced_Import_Need_MWh",
            "Import_Reduction_MWh",
            "Import_Reduction_%"
        ]
    ]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    If 80% of exported electricity could be stored and reused later,
    Germany’s import need could theoretically reduce by this amount.

    Example from January
    Export = 5,444,509 MWh
    Import = 5,971,889 MWh
    Recoverable export = 5,444,509 × 0.80 = 4,355,607 MWh
    Remaining import need = 5,971,889 − 4,355,607 = 1,616,281 MWh
    Import reduction = 72.94%
    """)
    return


@app.cell
def _(io, pd, requests):
    def load_smard_day_ahead_prices_all(start_date, end_date):
        url = "https://www.smard.de/nip-download-manager/nip/download/market-data"

        start_ts = int(pd.to_datetime(start_date, utc=True).timestamp() * 1000)
        end_ts = int(pd.to_datetime(end_date, utc=True).timestamp() * 1000)

        payload = {
            "request_form": [
                {
                    "format": "CSV",
                    "moduleIds": [
                        8004169,
                        8004170,
                        8000251,
                        8005078,
                        8000252,
                        8000253,
                        8000254,
                        8000255,
                        8000256,
                        8000257,
                        8000258,
                        8000259,
                        8000260,
                        8000261,
                        8000262,
                        8004996,
                        8004997
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

        response = requests.post(
            url,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            print(response.text)
            raise Exception(f"SMARD request failed: {response.status_code}")

        df_price_all = pd.read_csv(
            io.StringIO(response.text),
            sep=";"
        )

        df_price_all.columns = df_price_all.columns.str.strip()

        df_price_all["Start date"] = pd.to_datetime(
            df_price_all["Start date"],
            errors="coerce"
        )

        return df_price_all

    return (load_smard_day_ahead_prices_all,)


@app.cell
def _(end_date, load_smard_day_ahead_prices_all, start_date):
    df_price_all = load_smard_day_ahead_prices_all(
        start_date=start_date,
        end_date=end_date
    )

    df_price_all.head()
    return (df_price_all,)


@app.cell
def _(df_price_all):
    df_price_all.columns.tolist()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Burning fossil gas is typically the most expensive way to generate electricity. In 2025 the
    average cost of electricity from gas ranged between €101/MWh and €112/MWh across the EU.
    During peak gas-use hours in 2025, prices were on average 11% higher across the EU than in 2024. By contrast, in the hours when clean power (especially solar) was abundant, typically
    between 7am and 4pm, wholesale electricity prices rose by only 3%. In Germany, for
    instance, electricity prices jumped by 19% during high gas-use periods but grew only by 8%
    when solar generation was plentiful.
    https://ember-energy.org/app/uploads/2026/01/EMBER-Report-European-Electricity-Review-2026.pdf
    """)
    return


@app.cell
def _():
    price_mapping = {
        "Netherlands": "Netherlands [€/MWh] Calculated resolutions",
        "Switzerland": "Switzerland [€/MWh] Calculated resolutions",
        "Denmark": "Denmark 1 [€/MWh] Calculated resolutions",
        "Czech Republic": "Czech Republic [€/MWh] Calculated resolutions",
        "Luxembourg": "Germany/Luxembourg [€/MWh] Calculated resolutions",
        "Sweden": "Sweden 4 [€/MWh] Calculated resolutions",
        "Austria": "Austria [€/MWh] Calculated resolutions",
        "France": "France [€/MWh] Calculated resolutions",
        "Poland": "Poland [€/MWh] Calculated resolutions",
        "Norway": "Norway 2 [€/MWh] Calculated resolutions",
        "Belgium": "Belgium [€/MWh] Calculated resolutions",
    }
    return (price_mapping,)


@app.cell
def _(df_price_all, df_smard_trade, pd, price_mapping):
    df_trade_cost = (
        df_smard_trade.merge(
            df_price_all,
            on="Start date",
            how="inner"
        )
    )

    results = []

    for country, price_col in price_mapping.items():

        import_col = f"{country} (import) [MWh]"
        export_col = f"{country} (export) [MWh]"

        import_cost = (
            df_trade_cost[import_col].abs()
            * df_trade_cost[price_col]
        ).sum()

        export_revenue = (
            df_trade_cost[export_col]
            * df_trade_cost[price_col]
        ).sum()

        results.append({
            "Country": country,
            "Import Cost [Million €]": import_cost / 1e6,
            "Export Revenue [Million €]": export_revenue / 1e6,
            "Net Cost [Million €]":
                (import_cost - export_revenue) / 1e6
        })

    df_country_costs = pd.DataFrame(results)

    df_country_costs = df_country_costs.sort_values(
        "Net Cost [Million €]",
        ascending=False
    )

    df_country_costs.round(2)
    return (df_country_costs,)


@app.cell
def _(df_country_costs, px):

    df_net_cost = df_country_costs.sort_values(
        "Net Cost [Million €]",
        ascending=False
    )

    df_net_cost["Trade Balance"] = df_net_cost["Net Cost [Million €]"].apply(
        lambda x: "Net Cost" if x > 0 else "Net Benefit"
    )

    fig_net_cost = px.bar(
        df_net_cost,
        x="Country",
        y="Net Cost [Million €]",
        color="Trade Balance",
        title="Net Electricity Trade Cost by Country - Germany 2025"
    )

    fig_net_cost.show()
    return


@app.cell
def _(df_country_costs):
    df_country_costs["Net Cost [Million €]"].sum()
    return


@app.cell
def _(df_country_costs):
    total_import_cost_countrywise = (
        df_country_costs["Import Cost [Million €]"].sum()
        / 1000
    )

    total_export_revenue_countrywise = (
        df_country_costs["Export Revenue [Million €]"].sum()
        / 1000
    )

    net_trade_cost_countrywise = (
        total_import_cost_countrywise
        - total_export_revenue_countrywise
    )

    print(f"Import Cost: €{total_import_cost_countrywise:.2f} Billion")
    print(f"Export Revenue: €{total_export_revenue_countrywise:.2f} Billion")
    print(f"Net Trade Cost: €{net_trade_cost_countrywise:.2f} Billion")
    return (
        net_trade_cost_countrywise,
        total_export_revenue_countrywise,
        total_import_cost_countrywise,
    )


@app.cell
def _(
    net_trade_cost_countrywise,
    pd,
    px,
    total_export_revenue_countrywise,
    total_import_cost_countrywise,
):
    df_trade_summary_countrywise = pd.DataFrame({
        "Metric": [
            "Import Cost",
            "Export Revenue",
            "Net Trade Cost"
        ],
        "Value [Billion €]": [
            total_import_cost_countrywise,
            total_export_revenue_countrywise,
            net_trade_cost_countrywise
        ]
    })

    fig_trade_summary_countrywise = px.bar(
        df_trade_summary_countrywise,
        x="Metric",
        y="Value [Billion €]",
        text="Value [Billion €]",
        title="Germany Electricity Trade Economics Using Country-wise Prices (2025)"
    )

    fig_trade_summary_countrywise.update_traces(
        texttemplate="€%{y:.2f} bn",
        textposition="outside"
    )

    fig_trade_summary_countrywise.update_layout(
        yaxis_title="Billion €",
        height=500
    )

    fig_trade_summary_countrywise.show()
    return


@app.cell
def _(df_country_costs, df_smard_trade):
    avg_price_countrywise = (
        df_country_costs["Import Cost [Million €]"].sum() * 1_000_000
        /
        df_smard_trade["Total_Import_MWh"].sum()
    )

    print(avg_price_countrywise)
    return (avg_price_countrywise,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    MaStR stands for Marktstammdatenregister, which is the official German energy market registry maintained by Bundesnetzagentur.”
    """)
    return


@app.cell
def _(Mastr, inspect):

    mastr = Mastr()

    # Run only once locally
    #mastr.download(method="bulk")

    # Get table names
    inspector = inspect(mastr.engine)
    table_names = inspector.get_table_names()

    # Find storage-related tables
    storage_tables = [
        table for table in table_names
        if "speicher" in table.lower() or "storage" in table.lower()
    ]

    storage_tables
    return (mastr,)


@app.cell
def _(mastr, pd):
    df_storage = pd.read_sql_table(
        "storage_units",
        con=mastr.engine
    )

    df_storage.head()
    return (df_storage,)


@app.cell
def _(df_storage):
    df_storage.shape
    return


@app.cell
def _(df_storage):
    df_storage.columns
    return


@app.cell
def _(mastr, pd):
    query_extended = "SELECT * FROM storage_extended LIMIT 1"

    df_extended = pd.read_sql_query(
        query_extended,
        con=mastr.engine
    )

    for col in df_extended.columns:
        print(col)
    return


@app.cell
def _(df_storage):
    df_storage["NutzbareSpeicherkapazitaet"].describe()
    return


@app.cell
def _(mastr, pd):
    query_battery_storage_2026 = """
    SELECT
        SUM(su.NutzbareSpeicherkapazitaet) AS battery_storage_kWh_2026
    FROM storage_units su
    JOIN storage_extended se
    ON su.MastrNummer = se.SpeMastrNummer
    WHERE su.AnlageBetriebsstatus = 'In Betrieb'
    AND su.NutzbareSpeicherkapazitaet IS NOT NULL
    AND se.Technologie = 'Batterie'
    """

    df_battery_storage_2026 = pd.read_sql_query(
        query_battery_storage_2026,
        con=mastr.engine
    )

    battery_storage_GWh_2026 = (
        df_battery_storage_2026["battery_storage_kWh_2026"].iloc[0]
        / 1_000_000
    )

    print(battery_storage_GWh_2026)
    return


@app.cell
def _(mastr, pd):
    query_battery_locations = """
    SELECT DISTINCT
        su.MastrNummer,
        se.Bundesland,
        se.Ort,
        se.Technologie,
        se.Batterietechnologie,
        su.NutzbareSpeicherkapazitaet
    FROM storage_units su
    LEFT JOIN storage_extended se
    ON su.MastrNummer = se.SpeMastrNummer
    WHERE su.AnlageBetriebsstatus = 'In Betrieb'
    AND se.Technologie = 'Batterie'
    AND su.NutzbareSpeicherkapazitaet IS NOT NULL
    """

    df_battery_locations = pd.read_sql_query(
        query_battery_locations,
        con=mastr.engine
    )

    # remove duplicate systems
    df_battery_locations = (
        df_battery_locations
        .drop_duplicates(subset=["MastrNummer"])
    )

    # total Germany battery storage in GWh
    total_battery_GWh = (
        df_battery_locations["NutzbareSpeicherkapazitaet"]
        .sum()
        / 1_000_000
    )

    print(total_battery_GWh)
    df_battery_locations[
        [
            "Bundesland",
            "Ort",
            "NutzbareSpeicherkapazitaet"
        ]
    ].sort_values(
        "NutzbareSpeicherkapazitaet",
        ascending=False
    )
    return (df_battery_locations,)


@app.cell
def _(df_battery_locations, px):
    df_battery_by_state = (
        df_battery_locations
        .groupby("Bundesland")
        .agg(
            Total_Systems=("MastrNummer", "count"),
            Total_Capacity_GWh=("NutzbareSpeicherkapazitaet", "sum")
        )
        .reset_index()
    )

    df_battery_by_state["Total_Capacity_GWh"] = (
        df_battery_by_state["Total_Capacity_GWh"] / 1_000_000
    )

    df_battery_by_state = df_battery_by_state.sort_values(
        "Total_Capacity_GWh", ascending=False
    ).reset_index(drop=True)

    fig_state = px.bar(
        df_battery_by_state,
        x="Bundesland",
        y="Total_Capacity_GWh",
        title="Battery Storage Capacity by Federal State — Germany (MaStR)",
        labels={
            "Bundesland": "Federal State",
            "Total_Capacity_GWh": "Total Battery Capacity [GWh]"
        },
        color="Total_Capacity_GWh",
        color_continuous_scale="Blues",
        text="Total_Systems"
    )

    fig_state.update_traces(texttemplate="%{text} systems", textposition="outside")
    fig_state.update_layout(height=500, coloraxis_showscale=False, xaxis_tickangle=-45)
    fig_state.show()

    df_battery_by_state
    return (df_battery_by_state,)


@app.cell
def _(df_battery_by_state):
    total_battery_by_state_gwh = df_battery_by_state["Total_Capacity_GWh"].sum()
    total_battery_systems = df_battery_by_state["Total_Systems"].sum()

    print(f"Total systems: {total_battery_systems:,}")
    print(f"Total battery capacity: {total_battery_by_state_gwh:.2f} GWh")
    return


@app.cell
def _(mastr, pd):
    query_battery_class = """
    SELECT 
        se.Batterietechnologie,
        se.Technologie,
        COUNT(su.MastrNummer) as Total_Systems,
        SUM(su.NutzbareSpeicherkapazitaet) / 1_000_000 as Total_GWh
    FROM storage_units su
    LEFT JOIN storage_extended se
        ON su.MastrNummer = se.SpeMastrNummer
    WHERE su.AnlageBetriebsstatus = 'In Betrieb'
    AND se.Technologie = 'Batterie'
    AND su.NutzbareSpeicherkapazitaet IS NOT NULL
    AND su.NutzbareSpeicherkapazitaet > 0
    GROUP BY se.Batterietechnologie
    ORDER BY Total_GWh DESC
    """

    df_battery_class = pd.read_sql_query(query_battery_class, con=mastr.engine)
    df_battery_class["Total_GWh"] = df_battery_class["Total_GWh"].round(3)
    df_battery_class
    return


@app.cell
def _(mastr, pd, px):
    def classify_battery(capacity_kwh):
        if capacity_kwh <= 30:
            return "Home Storage"
        elif capacity_kwh <= 1000:
            return "Commercial Storage"
        else:
            return "Large Scale Storage"

    query_all_bat = """
    SELECT 
        su.MastrNummer,
        su.NutzbareSpeicherkapazitaet,
        se.Bundesland
    FROM storage_units su
    LEFT JOIN storage_extended se
        ON su.MastrNummer = se.SpeMastrNummer
    WHERE su.AnlageBetriebsstatus = 'In Betrieb'
    AND se.Technologie = 'Batterie'
    AND su.NutzbareSpeicherkapazitaet IS NOT NULL
    AND su.NutzbareSpeicherkapazitaet > 0
    """

    df_all_bat = pd.read_sql_query(query_all_bat, con=mastr.engine)
    df_all_bat["Category"] = df_all_bat["NutzbareSpeicherkapazitaet"].apply(classify_battery)

    df_category_summary = df_all_bat.groupby("Category").agg(
        Total_Systems=("MastrNummer", "count"),
        Total_GWh=("NutzbareSpeicherkapazitaet", "sum")
    ).reset_index()

    df_category_summary["Total_GWh"] = (
        df_category_summary["Total_GWh"] / 1_000_000
    ).round(3)

    df_category_summary["Share_%"] = (
        df_category_summary["Total_GWh"] /
        df_category_summary["Total_GWh"].sum() * 100
    ).round(1)

    fig_cat = px.pie(
        df_category_summary,
        values="Total_GWh",
        names="Category",
        title="Germany Battery Storage by Category (MaStR)",
        hole=0.4
    )
    fig_cat.show()

    df_category_summary
    return


@app.cell
def _(mastr, pd):
    query = """
    SELECT *
    FROM storage_extended
    LIMIT 5
    """

    df_storage_ext_sample = pd.read_sql_query(query, con=mastr.engine)

    df_storage_ext_sample.columns
    return


@app.cell
def _(df_installed):
    df_installed["source"].drop_duplicates().sort_values().tolist()
    return


@app.cell
def _(pd, requests):
    url = "https://api.energy-charts.info/installed_power"
    params = {"country": "de", "time_step": "yearly"}

    data = requests.get(url, params=params).json()

    years = data["time"]

    rows = []
    for pt in data["production_types"]:
        for i, year in enumerate(years):
            rows.append({
                "year": year,
                "source": pt["name"],
                "capacity_GW": pt["data"][i]
            })

    df_installed = pd.DataFrame(rows)

    storage_sources = [
        "Battery storage (power)",
        "Battery storage (capacity)",
        "Hydro pumped storage",
    ]

    df_storage_now = df_installed[
        (df_installed["source"].isin(storage_sources)) &
        (df_installed["year"] == "2026") &
        (df_installed["capacity_GW"].notna())
    ]

    df_storage_now
    return (df_installed,)


@app.cell
def _(df_smard_trade, pd):
    df_real_opt2 = df_smard_trade[["Start date", "Total_Export_MWh", "Total_Import_MWh"]].copy()
    df_real_opt2["Start date"] = pd.to_datetime(df_real_opt2["Start date"])

    # Use NET trade per hour - positive = net export, negative = net import
    df_real_opt2["Net_Trade_MWh"] = (
        df_real_opt2["Total_Export_MWh"] - df_real_opt2["Total_Import_MWh"]
    )

    print(f"Hours Germany was net exporter: {(df_real_opt2['Net_Trade_MWh'] > 0).sum()}")
    print(f"Hours Germany was net importer: {(df_real_opt2['Net_Trade_MWh'] < 0).sum()}")
    print(f"Total net export hours [TWh]: {df_real_opt2['Net_Trade_MWh'].clip(lower=0).sum()/1e6:.2f}")
    print(f"Total net import hours [TWh]: {df_real_opt2['Net_Trade_MWh'].clip(upper=0).abs().sum()/1e6:.2f}")
    return (df_real_opt2,)


@app.cell
def _(df_real_opt2, pd):
    net_export_total_mwh = df_real_opt2["Net_Trade_MWh"].clip(lower=0).sum()

    opt_results5 = []

    for add_gwh in [0, 10, 20, 30, 50, 75, 100, 150, 200, 300]:
        add_mwh = add_gwh * 1000
        soc5 = 0.0
        remaining_net_export = 0.0
        remaining_net_import = 0.0

        for net in df_real_opt2["Net_Trade_MWh"]:
            if net > 0:
                # Net export hour — charge storage first
                space = add_mwh - soc5
                charge = min(net, space)
                soc5 += charge * 0.85
                remaining_net_export += (net - charge)
            else:
                # Net import hour — discharge storage first
                deficit = abs(net)
                discharge = min(deficit, soc5)
                soc5 -= discharge
                remaining_net_import += (deficit - discharge)

        export_reduction_pct = (1 - remaining_net_export / net_export_total_mwh) * 100

        opt_results5.append({
            "Additional Storage [GWh]": add_gwh,
            "Total Storage [GWh]": 68 + add_gwh,
            "Remaining Net Export [TWh]": round(remaining_net_export / 1e6, 2),
            "Remaining Net Import [TWh]": round(remaining_net_import / 1e6, 2),
            "Export Reduction [%]": round(export_reduction_pct, 1),
        })

    df_results5 = pd.DataFrame(opt_results5)
    df_results5
    return (df_results5,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Germany currently has approximately **68 GWh** of total electricity storage
    capacity (28.4 GWh battery + ~40 GWh pumped hydro) against a real 2025 net
    exportable surplus of **12.17 TWh** across 2,634 hours.

    The optimisation analysis shows that adding just +75 to +100 GWh of
    additional storage would reduce net electricity exports by **59–65%**,
    consistent with Fraunhofer ISE's official target of +75 to +145 GWh by 2030.
    Beyond 300 GWh, returns diminish significantly as remaining exports stem from
    multi-day surplus events that no practical storage can fully absorb.
    """)
    return


@app.cell
def _(df_results5, px):
    fig_opt_final = px.line(
        df_results5,
        x="Additional Storage [GWh]",
        y=["Remaining Net Export [TWh]", "Remaining Net Import [TWh]"],
        markers=True,
        title="Additional Storage vs Net Exports & Imports — Germany 2025 ",
        labels={
            "value": "Energy [TWh]",
            "variable": "Type",
            "Additional Storage [GWh]": "Additional Storage on top of current 68 GWh [GWh]"
        }
    )

    fig_opt_final.add_vline(
        x=75,
        line_dash="dash",
        line_color="green",
        annotation_text="Optimal: +75 GWh (59% reduction)",
        annotation_position="top right"
    )

    fig_opt_final.add_vline(
        x=0,
        line_dash="dash",
        line_color="red",
        annotation_text="Current: 68 GWh total",
        annotation_position="top right"
    )

    fig_opt_final.update_layout(height=500)
    fig_opt_final.show()
    return


@app.cell
def _(avg_price_countrywise, df_results5):
    df_storage_economics = df_results5.copy()

    df_storage_economics["Estimated Import Cost [Billion €]"] = (
        df_storage_economics["Remaining Net Import [TWh]"]
        * 1_000_000
        * avg_price_countrywise
        / 1e9
    )

    baseline_cost = (
        df_storage_economics[
            "Estimated Import Cost [Billion €]"
        ].iloc[0]
    )

    df_storage_economics["Estimated Savings [Billion €]"] = (
        baseline_cost
        - df_storage_economics["Estimated Import Cost [Billion €]"]
    )

    df_storage_economics.round(3)
    return (df_storage_economics,)


@app.cell
def _(df_storage_economics, go):


    df_plot_eco = df_storage_economics[
        df_storage_economics["Additional Storage [GWh]"] > 0
    ].copy()

    x_labels = ["+" + str(int(v)) for v in df_plot_eco["Additional Storage [GWh]"]]

    fig_eco = go.Figure()

    fig_eco.add_trace(go.Bar(
        x=x_labels,
        y=df_plot_eco["Estimated Import Cost [Billion €]"],
        name="Estimated import cost",
        marker_color="rgba(100, 149, 210, 0.85)",
        marker_line_width=0,
    ))

    fig_eco.add_trace(go.Bar(
        x=x_labels,
        y=df_plot_eco["Estimated Savings [Billion €]"],
        name="Estimated savings vs baseline",
        marker_color="rgba(80, 180, 140, 0.85)",
        marker_line_width=0,
    ))

    fig_eco.update_layout(
        barmode="group",
        bargap=0.20,
        bargroupgap=0.05,
        title=dict(
            text="ESTIMATED IMPORT COST & SAVINGS BY STORAGE SIZE",
            font=dict(size=14, color="#222"),
            x=0, xanchor="left",
        ),
        legend=dict(
            orientation="h",
            x=0, y=1.10,
            font=dict(size=12),
            bgcolor="rgba(0,0,0,0)",
            itemsizing="constant",
        ),
        xaxis=dict(
            title="Additional storage on top of current 68 GWh (GWh)",
            title_font=dict(size=13, color="#555"),
            tickfont=dict(size=13, color="#444"),
            showgrid=False,
            zeroline=False,
            linecolor="#ccc",
        ),
        yaxis=dict(
            title="Billion €/year",
            title_font=dict(size=13, color="#555"),
            tickfont=dict(size=13, color="#444"),
            tickprefix="€",
            ticksuffix="B",
            gridcolor="#e8e8e8",
            gridwidth=1,
            zeroline=True,
            zerolinecolor="#bbb",
            zerolinewidth=1,
        ),
        plot_bgcolor="#f7f7f5",
        paper_bgcolor="white",
        height=550,
        margin=dict(t=100, b=70, l=80, r=40),
    )

    # baseline reference line (0 additional storage = full import cost)
    baseline = df_storage_economics["Estimated Import Cost [Billion €]"].iloc[0]

    fig_eco.add_hline(
        y=baseline,
        line_dash="dash",
        line_color="#E24B4A",
        line_width=1.5,
        annotation_text=f"Baseline import cost (0 extra storage): €{baseline:.2f}B",
        annotation_font_color="#E24B4A",
        annotation_font_size=11,
        annotation_position="top right",
    )

    fig_eco.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The analysis shows that Germany currently relies on electricity imports despite having a large renewable energy share. Based on the hourly trade and price data for 2025, the total electricity import expenditure was approximately €7.78 billion, while electricity exports generated approximately €4.13 billion in revenue. This resulted in a net electricity trade cost of €3.65 billion.

    To evaluate the impact of additional storage capacity, several storage expansion scenarios were simulated. The current storage capacity of approximately 68 GWh serves as the baseline. Under this scenario, Germany still requires around 34.09 TWh of net imports per year and exports approximately 12.17 TWh of surplus electricity.

    The results indicate that increasing storage capacity significantly reduces both exports and imports. With an additional 75 GWh of storage (total storage capacity of 143 GWh), net exports decrease from 12.17 TWh to 4.92 TWh, corresponding to an export reduction of 59.5%. At the same time, net imports decrease from 34.09 TWh to 28.01 TWh.

    From an economic perspective, the estimated annual import expenditure decreases from approximately €3.05 billion to €2.50 billion, resulting in annual savings of approximately €543 million. Further storage expansion continues to reduce import dependence; however, the savings per additional GWh gradually decrease, indicating diminishing economic returns.
    """)
    return


@app.cell
def _(df_storage_economics, px):
    fig_cost = px.line(
        df_storage_economics,
        x="Total Storage [GWh]",
        y=[
            "Estimated Import Cost [Billion €]",
            "Estimated Savings [Billion €]"
        ],
        markers=True,
        title="Economic Impact of Additional Storage Capacity (Without Storage Investment Costs)"
    )

    fig_cost.update_layout(
        xaxis_title="Total Storage Capacity [GWh]",
        yaxis_title="Billion €",
        height=500
    )

    fig_cost.show()
    return


@app.cell
def _(df_storage_economics):
    import plotly.graph_objects as go

    fig_storage_benefit = go.Figure()

    fig_storage_benefit.add_trace(
        go.Scatter(
            x=df_storage_economics["Total Storage [GWh]"],
            y=df_storage_economics["Remaining Net Import [TWh]"],
            mode="lines+markers",
            name="Remaining Net Import [TWh]"
        )
    )

    fig_storage_benefit.add_trace(
        go.Scatter(
            x=df_storage_economics["Total Storage [GWh]"],
            y=df_storage_economics["Estimated Savings [Billion €]"],
            mode="lines+markers",
            name="Estimated Savings [Billion €]",
            yaxis="y2"
        )
    )

    fig_storage_benefit.update_layout(
        title="Storage Expansion: Technical and Economic Benefits (Without Storage Investment Costs)",
        xaxis_title="Total Storage Capacity [GWh]",
        yaxis=dict(
            title="Remaining Net Import [TWh]"
        ),
        yaxis2=dict(
            title="Estimated Savings [Billion €]",
            overlaying="y",
            side="right"
        ),
        height=550
    )

    fig_storage_benefit.show()
    return (go,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Impact of additional storage capacity on Germany's net electricity imports and estimated annual savings. Savings are calculated from avoided import expenditure using average day-ahead electricity prices. Storage investment costs (CAPEX), operation and maintenance costs (OPEX), battery degradation, financing costs, and grid connection costs are not included.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Wider deployment and the commercialisation of new battery storage technologies has led to rapid cost reductions, notably for lithium-ion batteries, but also for high-temperature sodium-sulphur (“NAS”) and so-called “flow” batteries. Small-scale lithium-ion residential battery systems in the German market suggest that between 2014 and 2020, battery energy storage systems (BESS) prices fell by 71%, to USD 776/kWh. With their rapid cost declines, the role of BESS for stationary and transport applications is gaining prominence, but other technologies exist, including pumped hydro, flywheels, and thermal energy stores.
    https://www.irena.org/Energy-Transition/Technology/Energy-storage-costs
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Storage Cost Analysis — LCOS Calculation

       **Source: IRENA Electricity Storage Cost-of-Service Tool v2.0 (2025)**
       International Renewable Energy Agency (168 member states)
       https://www.irena.org/Energy-Transition/Technology/Energy-storage-costs

       **Technology: Li-Ion LFP — 2025 Reference Case (directly from tool)**

       For this analysis, **Lithium-ion LFP (Lithium Iron Phosphate)** is selected
       as the storage technology. This is consistent with current utility-scale
       battery deployments in Germany and the dominant technology in new installations.

       | Parameter | Best | Reference | Worst | Unit |
       |---|---|---|---|---|
       | Energy installation cost | 67.4 | **195.0** | 283.6 | USD/kWh |
       | Calendar lifetime | 28.3 | **17.0** | 7.1 | years |
       | Cycle life | 20,000 | **5,000** | 2,000 | equiv. full cycles |
       | Round-trip efficiency | 96.3% | **92.0%** | 86.7% | % |
       | Depth of discharge | 100% | **90%** | 84% | % |
       | Self-discharge | 0.09% | **0.10%** | 0.36% | % per day |
       | Maintenance (storage) | 1.5% | **1.5%** | 1.5% | % of invest/yr |
       | Maintenance (inverter) | 1.5% | **1.5%** | 1.5% | % of invest/yr |
       | Interest rate | 3% | **3%** | 3% | % |
       | Grid connection (HV incl. transformer) | 15+15 | **15+15** | 15+15 | USD/kW |

       **Application: Spot Market Trading (arbitrage) — EPEX SPOT**
       Closest match to energy shifting use case (storing surplus solar/wind)
       Cycles/day: 2, Depth of discharge: 80%

         > **Note:** The IRENA tool assumes 2 cycles/day for arbitrage applications.
       > Our simulation shows Germany's current (2025) renewable surplus produces only
       > **0.08 – 0.5 equivalent cycles/day** depending on storage size.
       > This low utilization is the primary reason LCOS exceeds import prices in 2025,
       > and directly motivates the renewable expansion.

       **Note:** All parameters taken directly from IRENA tool cells.
       No external estimates used.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Who owns the IRENA Cost-of-Service Tool
    The organisation: IRENA — International Renewable Energy Agency

    Intergovernmental body with 168 member states, headquartered in Abu Dhabi
    The tool is maintained by its Innovation and Technology Centre (IITC), based in Bonn, Germany

    The people directly responsible
    Original tool authors (v1.0 & v2.0):
    Contributing authors were Pablo Ralon, Michael Taylor, and Andrei Ilas (IRENA), with Harald Diaz-Bone (Green Budget Germany) and Kai-Philipp Kairies (Institute for Power Electronics and Electrical Drives, RWTH Aachen University). For feedback the contact is publications@irena.org
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    What the IRENA Cost-of-Service Tool v2.0 actually is
    It's a spreadsheet-based tool that provides a quick analysis of the approximate annual cost of energy storage systems to help identify potentially cost-effective options. It's not a detailed simulation for investment decisions, but allows those interested in specific applications to access more detailed analysis to further evaluate suitability and performance under real-world conditions. IRENA
    It enables users to undertake a rapid but robust analysis of the relative economic suitability of 13 different electricity storage technologies across 12 stationary storage applications. By modifying various parameters, users can account for a diverse range of project- and location-specific variables, from number of daily cycles to local financing costs.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    LFP specifically — why it's the right technology choice
    LFP (Lithium Iron Phosphate) is the dominant grid-scale chemistry today for good reason:

    Cycle life: Your Best Case assumes 20,000 cycles — industry sources confirm LFP can realistically deliver 15–20 years of service, far above other Li-ion chemistries
    Safety: LFP has superior thermal and chemical stability vs. NMC (no cobalt, no nickel)
    Cost: Battery storage project costs dropped 90% between 2010 and 2023, from $2,511/kWh to $273/kWh, driven by scaling up manufacturing, improving material efficiency, and refining industrial processes
    """)
    return


@app.cell
def _(avg_price_countrywise, df_results5, pd, px):
    # ═══════════════════════════════════════════════════════════════════
    # IRENA Cost-of-Service Tool v2.0 (2025) — Li-Ion LFP — Best Case Only
    # ALL values taken directly from tool's Cost-of-Service sheet
    # Source: https://www.irena.org/Energy-Transition/Technology/Energy-storage-costs
    # ═══════════════════════════════════════════════════════════════════

    irena_scenarios = {
        "Best": {"capex_usd_kwh": 67.364, "lifetime": 28.333, "efficiency_rt": 0.96279, "dod": 0.90},
    }

    # Fixed parameters — same across all scenarios (from IRENA tool)
    irena_maintenance_storage  = 0.015
    irena_maintenance_inverter = 0.015
    irena_maintenance_grid     = 0.010
    irena_interest_rate        = 0.03
    irena_self_discharge_day   = 0.001
    irena_inverter_cost_usd_kw = 70.0
    irena_grid_usd_kw          = 30.0
    irena_usd_to_eur           = 0.924
    irena_ep_ratio             = 0.667
    irena_inverter_life        = 27.0
    irena_grid_life            = 50.0

    irena_baseline_twh = df_results5["Remaining Net Import [TWh]"].iloc[0]

    irena_results = []

    for irena_scenario_name, irena_p in irena_scenarios.items():

        irena_capex_eur_kwh = irena_p["capex_usd_kwh"] * irena_usd_to_eur
        irena_life          = irena_p["lifetime"]
        irena_eff           = irena_p["efficiency_rt"]

        irena_crf = (
            irena_interest_rate * (1 + irena_interest_rate) ** irena_life
            / ((1 + irena_interest_rate) ** irena_life - 1)
        )

        irena_crf_inv = (
            irena_interest_rate * (1 + irena_interest_rate) ** irena_inverter_life
            / ((1 + irena_interest_rate) ** irena_inverter_life - 1)
        )

        irena_crf_grid = (
            irena_interest_rate * (1 + irena_interest_rate) ** irena_grid_life
            / ((1 + irena_interest_rate) ** irena_grid_life - 1)
        )

        for _, irena_row in df_results5.iterrows():
            irena_gwh = irena_row["Additional Storage [GWh]"]
            irena_mwh = irena_gwh * 1_000
            irena_kwh = irena_gwh * 1_000_000

            irena_reduction_twh = irena_baseline_twh - irena_row["Remaining Net Import [TWh]"]
            irena_mwh_out       = irena_reduction_twh * 1_000_000

            if irena_gwh == 0 or irena_mwh_out <= 0:
                irena_results.append({
                    "Scenario":                         irena_scenario_name,
                    "Additional Storage [GWh]":         0,
                    "Equiv. Full Cycles/yr":            0,
                    "LCOS [€/MWh]":                    None,
                    "Annual Storage Cost [Billion €]":  0,
                    "Annual Import Saving [Billion €]": 0,
                    "Net Annual Benefit [Billion €]":   0,
                })
                continue

            irena_cycles_yr = irena_mwh_out / irena_mwh

            irena_invest_storage  = irena_kwh * irena_capex_eur_kwh
            irena_annuity_storage = irena_invest_storage * irena_crf

            irena_power_kw    = irena_mwh * 1000 / irena_ep_ratio
            irena_invest_inv  = irena_power_kw * (irena_inverter_cost_usd_kw * irena_usd_to_eur)
            irena_annuity_inv = irena_invest_inv * irena_crf_inv

            irena_invest_grid  = irena_power_kw * (irena_grid_usd_kw * irena_usd_to_eur)
            irena_annuity_grid = irena_invest_grid * irena_crf_grid

            irena_maint = (
                irena_invest_storage * irena_maintenance_storage
                + irena_invest_inv   * irena_maintenance_inverter
                + irena_invest_grid  * irena_maintenance_grid
            )

            irena_eff_loss_eur = (
                irena_mwh_out * (1 - irena_eff) / irena_eff * avg_price_countrywise
            )

            irena_selfdis_eur = (
                irena_mwh * irena_self_discharge_day * 365 * avg_price_countrywise
            )

            irena_total_cost = (
                irena_annuity_storage
                + irena_annuity_inv
                + irena_annuity_grid
                + irena_maint
                + irena_eff_loss_eur
                + irena_selfdis_eur
            )

            irena_lcos        = irena_total_cost / irena_mwh_out
            irena_saving      = irena_mwh_out * avg_price_countrywise
            irena_net_benefit = irena_saving - irena_total_cost

            irena_results.append({
                "Scenario":                         irena_scenario_name,
                "Additional Storage [GWh]":         irena_gwh,
                "Equiv. Full Cycles/yr":            round(irena_cycles_yr, 1),
                "LCOS [€/MWh]":                    round(irena_lcos, 1),
                "Annual Storage Cost [Billion €]":  round(irena_total_cost / 1e9, 3),
                "Annual Import Saving [Billion €]": round(irena_saving / 1e9, 3),
                "Net Annual Benefit [Billion €]":   round(irena_net_benefit / 1e9, 3),
            })

    df_irena_lcos = pd.DataFrame(irena_results)

    fig_lcos = px.line(
        df_irena_lcos[df_irena_lcos["LCOS [€/MWh]"].notna()],
        x="Additional Storage [GWh]",
        y="LCOS [€/MWh]",
        title="LCOS by Storage Size — IRENA Li-Ion LFP 2025 (Best Case)",
        labels={
            "Additional Storage [GWh]": "Additional Storage on top of current 68 GWh [GWh]",
            "LCOS [€/MWh]": "LCOS [€/MWh]",
        },
        markers=True,
    )
    fig_lcos.add_hline(
        y=avg_price_countrywise,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Avg German import price: €{avg_price_countrywise:.1f}/MWh",
        annotation_position="top right"
    )
    fig_lcos.update_layout(height=500)
    fig_lcos.show()

    df_irena_lcos
    return (df_irena_lcos,)


@app.cell
def _():
    return


@app.cell
def _(df_irena_lcos):
    def _():
        import plotly.graph_objects as go

        df_plot = df_irena_lcos[
            (df_irena_lcos["Scenario"] == "Best") &
            (df_irena_lcos["LCOS [€/MWh]"].notna()) &
            (df_irena_lcos["Additional Storage [GWh]"] > 0)
        ].copy()

        df_plot["Net Loss [Billion €]"] = (
            df_plot["Annual Storage Cost [Billion €]"]
            - df_plot["Annual Import Saving [Billion €]"]
        )

        x_labels = ["+" + str(int(v)) for v in df_plot["Additional Storage [GWh]"]]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=x_labels,
            y=df_plot["Annual Storage Cost [Billion €]"],
            name="Annual storage cost",
            marker_color="rgba(100, 149, 210, 0.85)",
            marker_line_width=0,
        ))

        fig.add_trace(go.Bar(
            x=x_labels,
            y=df_plot["Annual Import Saving [Billion €]"],
            name="Annual import saving",
            marker_color="rgba(80, 180, 140, 0.85)",
            marker_line_width=0,
        ))

        fig.add_trace(go.Bar(
            x=x_labels,
            y=df_plot["Net Loss [Billion €]"],
            name="Net loss (cost − saving)",
            marker_color=[
                "rgba(80,180,140,0.85)" if v <= 0 else "rgba(220,120,120,0.85)"
                for v in df_plot["Net Loss [Billion €]"]
            ],
            marker_line_width=0,
        ))

        fig.update_layout(
            barmode="group",
            bargap=0.20,
            bargroupgap=0.05,
            title=dict(
                text="ANNUAL COST VS SAVINGS — DOES MORE STORAGE PAY OFF?",
                font=dict(size=14, color="#222"),
                x=0, xanchor="left",
            ),
            legend=dict(
                orientation="h",
                x=0, y=1.10,
                font=dict(size=12),
                bgcolor="rgba(0,0,0,0)",
                itemsizing="constant",
            ),
            xaxis=dict(
                title="Additional storage (GWh)",
                title_font=dict(size=13, color="#555"),
                tickfont=dict(size=13, color="#444"),
                showgrid=False,
                zeroline=False,
                linecolor="#ccc",
            ),
            yaxis=dict(
                title="Billion €/year",
                title_font=dict(size=13, color="#555"),
                tickfont=dict(size=13, color="#444"),
                tickprefix="€",
                ticksuffix="B",
                gridcolor="#e8e8e8",
                gridwidth=1,
                zeroline=True,
                zerolinecolor="#bbb",
                zerolinewidth=1,
                range=[-0.1, 4.2],
            ),
            plot_bgcolor="#f7f7f5",
            paper_bgcolor="white",
            height=550,           # taller = bars easier to read
            margin=dict(t=100, b=70, l=80, r=40),
        )
        return fig.show()


    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Storage alone cannot fix Germany's import dependency. Only +10 GWh is economically viable today with 2025 renewable surplus levels. Making larger storage profitable requires a much bigger renewable fleet — enough to generate the surplus cycles that spread fixed capital costs.
    """)
    return


@app.cell
def _(
    df_price_all,
    df_smard_consumption,
    df_smard_generation,
    pd,
    px,
    renewable_cols,
):
    df_surplus_price = df_smard_generation.copy()

    df_surplus_price["Renewable Generation"] = (
        df_surplus_price[renewable_cols].sum(axis=1)
    )

    df_surplus_price = df_surplus_price[
        ["Start date", "Renewable Generation"]
    ].merge(
        df_smard_consumption[["Start date", "Consumption"]],
        on="Start date",
        how="inner"
    ).merge(
        df_price_all[
            [
                "Start date",
                "Germany/Luxembourg [€/MWh] Calculated resolutions"
            ]
        ],
        on="Start date",
        how="inner"
    ).rename(columns={
        "Germany/Luxembourg [€/MWh] Calculated resolutions": "Price [€/MWh]"
    })

    df_surplus_price["Net [MWh]"] = (
        df_surplus_price["Renewable Generation"]
        - df_surplus_price["Consumption"]
    )

    df_surplus_price["Type"] = df_surplus_price["Net [MWh]"].apply(
        lambda x: "Renewable Surplus" if x > 0 else "Renewable Deficit"
    )

    threshold_negative = -1
    threshold_near_zero = 10

    sp_surplus_hours = (df_surplus_price["Net [MWh]"] > 0).sum()
    sp_negative_real = (df_surplus_price["Price [€/MWh]"] < threshold_negative).sum()
    sp_near_zero = (df_surplus_price["Price [€/MWh]"] < threshold_near_zero).sum()

    sp_surplus_negative = (
        (df_surplus_price["Net [MWh]"] > 0)
        & (df_surplus_price["Price [€/MWh]"] < threshold_negative)
    ).sum()

    sp_surplus_near_zero = (
        (df_surplus_price["Net [MWh]"] > 0)
        & (df_surplus_price["Price [€/MWh]"] < threshold_near_zero)
    ).sum()

    print(f"Renewable surplus hours 2025:                      {sp_surplus_hours}")
    print(f"Hours with real negative prices (<-1 €/MWh):       {sp_negative_real}")
    print(f"Hours with near-zero prices (<10 €/MWh):           {sp_near_zero}")
    print(f"Renewable surplus + real negative price:           {sp_surplus_negative}")
    print(f"Renewable surplus + near-zero (<10 €/MWh):         {sp_surplus_near_zero}")

    if sp_negative_real > 0:
        print(
            f"% of real negative price hours = renewable surplus: "
            f"{sp_surplus_negative / sp_negative_real * 100:.1f}%"
        )

    print("\nPrice distribution:")
    print(f"  Below -50 €/MWh:   {(df_surplus_price['Price [€/MWh]'] < -50).sum()} hours")
    print(f"  -50 to -1 €/MWh:   {((df_surplus_price['Price [€/MWh]'] >= -50) & (df_surplus_price['Price [€/MWh]'] < -1)).sum()} hours")
    print(f"  -1 to 0 €/MWh:     {((df_surplus_price['Price [€/MWh]'] >= -1) & (df_surplus_price['Price [€/MWh]'] < 0)).sum()} hours")
    print(f"  0 to 10 €/MWh:     {((df_surplus_price['Price [€/MWh]'] >= 0) & (df_surplus_price['Price [€/MWh]'] < 10)).sum()} hours")


    # --------------------------------------------------
    # Monthly grouped bar chart
    # --------------------------------------------------

    df_surplus_price["Month"] = df_surplus_price["Start date"].dt.strftime("%b")
    df_surplus_price["Month_num"] = df_surplus_price["Start date"].dt.month

    monthly_surplus_price = (
        df_surplus_price
        .groupby(["Month", "Month_num"])
        .agg(
            Renewable_Surplus_Hours=("Net [MWh]", lambda x: (x > 0).sum()),
            Negative_Price_Hours=("Price [€/MWh]", lambda x: (x < threshold_negative).sum()),
            Near_Zero_Price_Hours=("Price [€/MWh]", lambda x: (x < threshold_near_zero).sum()),
            Average_Price_EUR_MWh=("Price [€/MWh]", "mean")
        )
        .reset_index()
        .sort_values("Month_num")
    )

    fig_monthly_simple = px.bar(
        monthly_surplus_price,
        x="Month",
        y=[
            "Renewable_Surplus_Hours",
            "Negative_Price_Hours"
        ],
        barmode="group",
        title="Monthly Renewable Surplus and Negative Price Hours — Germany 2025",
        labels={
            "value": "Number of Hours",
            "variable": "Category",
            "Month": "Month"
        }
    )

    fig_monthly_simple.update_layout(
        height=500,
        yaxis_title="Number of Hours",
        xaxis_title="Month"
    )

    fig_monthly_simple.show()


    # --------------------------------------------------
    # Summary stacked bar
    # --------------------------------------------------

    summary_counts = pd.DataFrame({
        "Category": [
            "Renewable Surplus + Negative Price",
            "Renewable Surplus + Non-negative Price",
            "Renewable Deficit"
        ],
        "Hours": [
            sp_surplus_negative,
            sp_surplus_hours - sp_surplus_negative,
            len(df_surplus_price) - sp_surplus_hours
        ]
    })

    fig_summary_surplus = px.bar(
        summary_counts,
        x="Hours",
        y=["2025"] * len(summary_counts),
        color="Category",
        orientation="h",
        text="Hours",
        title="2025 Hourly Renewable Balance and Negative Price Summary"
    )

    fig_summary_surplus.update_traces(
        textposition="inside"
    )

    fig_summary_surplus.update_layout(
        xaxis_title="Number of Hours",
        yaxis_title="Year",
        height=350
    )

    fig_summary_surplus.show()

    monthly_surplus_price
    return (df_surplus_price,)


@app.cell
def _(df_surplus_price):
    total_renewable_surplus_mwh = (
        df_surplus_price["Net [MWh]"]
        .clip(lower=0)
        .sum()
    )

    total_renewable_deficit_mwh = (
        df_surplus_price["Net [MWh]"]
        .clip(upper=0)
        .abs()
        .sum()
    )

    total_renewable_surplus_twh = total_renewable_surplus_mwh / 1_000_000
    total_renewable_deficit_twh = total_renewable_deficit_mwh / 1_000_000

    print(f"Total renewable surplus in 2025: {total_renewable_surplus_twh:.2f} TWh")
    print(f"Total renewable deficit in 2025: {total_renewable_deficit_twh:.2f} TWh")
    return


@app.cell
def _(df_surplus_price):
    surplus_hours = df_surplus_price[df_surplus_price["Net [MWh]"] > 0]

    print("Number of surplus hours:", len(surplus_hours))

    print(
        "Average surplus during surplus hours [MWh]:",
        surplus_hours["Net [MWh]"].mean()
    )

    print(
        "Maximum surplus hour [MWh]:",
        surplus_hours["Net [MWh]"].max()
    )

    print(
        "Total surplus [TWh]:",
        surplus_hours["Net [MWh]"].sum() / 1_000_000
    )
    return


@app.cell
def _(df_surplus_price):
    # Manual verification — rows with renewable surplus AND negative price
    df_verify_sp = df_surplus_price[
        (df_surplus_price["Net [MWh]"] > 0) &
        (df_surplus_price["Price [€/MWh]"] < 0)
    ].copy()

    print(f"Rows with renewable surplus + negative price: {len(df_verify_sp)}")
    print(f"\nSample of these hours:")
    print(df_verify_sp[[
        "Start date",
        "Renewable Generation",
        "Consumption",
        "Net [MWh]",
        "Price [€/MWh]"
    ]].head(20).to_string())

    print(f"\nMonth breakdown:")
    df_verify_sp["Month"] = df_verify_sp["Start date"].dt.month
    print(df_verify_sp.groupby("Month")["Net [MWh]"].count())

    print(f"\nHour of day breakdown:")
    df_verify_sp["Hour"] = df_verify_sp["Start date"].dt.hour
    print(df_verify_sp.groupby("Hour")["Net [MWh]"].count())
    return


@app.cell
def _(df_real_opt2, pd, px):
    df_seasonal = df_real_opt2.copy()
    df_seasonal["Month"] = df_seasonal["Start date"].dt.strftime("%b")
    df_seasonal["Month_num"] = df_seasonal["Start date"].dt.month

    seasonal_month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    df_seasonal_grouped = df_seasonal.groupby(
        ["Month", "Month_num"]
    ).agg(
        Net_Export_TWh=("Net_Trade_MWh", lambda x: x.clip(lower=0).sum() / 1e6),
        Net_Import_TWh=("Net_Trade_MWh", lambda x: x.clip(upper=0).abs().sum() / 1e6),
        Net_Export_Hours=("Net_Trade_MWh", lambda x: (x > 0).sum()),
        Net_Import_Hours=("Net_Trade_MWh", lambda x: (x < 0).sum()),
    ).reset_index().sort_values("Month_num")

    df_seasonal_grouped["Month"] = pd.Categorical(
        df_seasonal_grouped["Month"],
        categories=seasonal_month_order,
        ordered=True
    )

    fig_seasonal = px.bar(
        df_seasonal_grouped,
        x="Month",
        y=["Net_Export_TWh", "Net_Import_TWh"],
        barmode="group",
        title="Monthly Net Export vs Import — Germany 2025",
        labels={"value": "Energy [TWh]", "variable": "Type"}
    )

    fig_seasonal.update_layout(height=500)
    fig_seasonal.show()

    df_seasonal_grouped[["Month", "Net_Export_TWh", "Net_Import_TWh",
                          "Net_Export_Hours", "Net_Import_Hours"]]
    return


@app.cell
def _(df_real_opt2, px):
    df_hourly = df_real_opt2.copy()
    df_hourly["Hour"] = df_real_opt2["Start date"].dt.hour

    df_hourly_grouped = df_hourly.groupby("Hour").agg(
        Avg_Net_Export_MWh=("Net_Trade_MWh", lambda x: x.clip(lower=0).mean()),
        Avg_Net_Import_MWh=("Net_Trade_MWh", lambda x: x.clip(upper=0).abs().mean()),
        Net_Export_Hours=("Net_Trade_MWh", lambda x: (x > 0).sum()),
    ).reset_index()

    fig_hourly = px.bar(
        df_hourly_grouped,
        x="Hour",
        y=["Avg_Net_Export_MWh", "Avg_Net_Import_MWh"],
        barmode="group",
        title="Average Hourly Net Export vs Import Pattern — Germany 2025",
        labels={
            "value": "Average Energy [MWh]",
            "variable": "Type",
            "Hour": "Hour of Day"
        }
    )

    fig_hourly.update_layout(
        height=500,
        xaxis=dict(tickmode="linear", tick0=0, dtick=1)
    )

    fig_hourly.show()

    df_hourly_grouped
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Loading DWD Solar Radiation and Sunshine Duration Data
    """)
    return


@app.cell
def _(io, pd, requests, zipfile):
    def load_dwd_solar_data(station_id, start_date, end_date):
        solar_url = (
            "https://opendata.dwd.de/climate_environment/CDC/"
            "observations_germany/climate/hourly/solar/"
            f"stundenwerte_ST_{station_id}_row.zip"
        )

        response = requests.get(solar_url, timeout=30)
        response.raise_for_status()

        zip_file = zipfile.ZipFile(
            io.BytesIO(response.content)
        )

        csv_filename = [
            name for name in zip_file.namelist()
            if "produkt_st_stunde" in name
        ][0]

        df_solar = pd.read_csv(
            zip_file.open(csv_filename),
            sep=";",
            na_values=["-999"],
        )

        df_solar.columns = df_solar.columns.str.strip()

        df_solar["MESS_DATUM"] = (
            df_solar["MESS_DATUM"]
            .astype(str)
            .str.strip()
            .str.replace(":", "", regex=False)
        )

        df_solar["Start date"] = pd.to_datetime(
            df_solar["MESS_DATUM"],
            format="%Y%m%d%H%M",
            errors="coerce"
        )

        df_solar = df_solar.dropna(subset=["Start date"])

        df_solar["Start date"] = df_solar["Start date"].dt.round("h")

        df_solar = df_solar.rename(
            columns={
                "FG_LBERG": "Solar Radiation [W/m²]",
                "SD_LBERG": "Sunshine Duration [min]",
            }
        )

        df_solar = df_solar.groupby(
            "Start date",
            as_index=False
        ).mean(numeric_only=True)

        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        df_solar = df_solar[
            (df_solar["Start date"] >= start_dt)
            &
            (df_solar["Start date"] < end_dt)
        ]

        return df_solar[
            [
                "Start date",
                "Solar Radiation [W/m²]",
                "Sunshine Duration [min]",
            ]
        ]

    return (load_dwd_solar_data,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Accessing DWD Solar Radiation Data

    This section accesses the DWD Open Data directory containing hourly solar radiation observations for Germany.

    The directory listing is used to:
    - Identify available solar measurement stations
    - Explore available solar datasets
    - Verify data accessibility from the DWD platform
    """)
    return


@app.cell
def _(re, requests):

    solar_base_url = (
        "https://opendata.dwd.de/climate_environment/CDC/"
        "observations_germany/climate/hourly/solar/"
    )

    solar_index_html = requests.get(solar_base_url, timeout=30).text

    # Extract all station IDs from filenames like "stundenwerte_ST_00183_row.zip"
    station_ids = re.findall(r'stundenwerte_ST_(\d{5})_row\.zip', solar_index_html)

    print(f"Found {len(station_ids)} solar stations:")
    print(station_ids)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Visualization of Solar Radiation at a DWD Weather Station
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Multi-Station Solar Radiation Analysis Across Germany
    """)
    return


@app.cell
def _(end_date, load_dwd_solar_data, start_date):
    solar_station_ids = [
        "00183",
        "00656",
        "00662",
        "00691",
        "00853",
        "00867",
        "01048",
        "01303",
        "01346",
        "01358",
    ]

    solar_dfs = []

    for solar_station_id in solar_station_ids:

        print(f"Loading solar station {solar_station_id}...")

        df_station_solar = load_dwd_solar_data(
            station_id=solar_station_id,
            start_date=start_date,
            end_date=end_date,
        )

        df_station_solar = df_station_solar.rename(
            columns={
                "Solar Radiation [W/m²]":
                f"Solar Radiation {solar_station_id} [W/m²]",

                "Sunshine Duration [min]":
                f"Sunshine Duration {solar_station_id} [min]",
            }
        )

        solar_dfs.append(df_station_solar)

    df_dwd_solar_all = solar_dfs[0]

    for df_solar_source in solar_dfs[1:]:

        df_dwd_solar_all = df_dwd_solar_all.merge(
            df_solar_source,
            on="Start date",
            how="outer",
        )

    df_dwd_solar_all = df_dwd_solar_all.sort_values(
        "Start date"
    )

    solar_radiation_cols = [
        col for col in df_dwd_solar_all.columns
        if "Solar Radiation" in col
    ]

    sunshine_duration_cols = [
        col for col in df_dwd_solar_all.columns
        if "Sunshine Duration" in col
    ]

    df_dwd_solar_all["Average Solar Radiation [W/m²]"] = (
        df_dwd_solar_all[solar_radiation_cols]
        .mean(axis=1, skipna=True)
    )

    df_dwd_solar_all["Average Sunshine Duration [min]"] = (
        df_dwd_solar_all[sunshine_duration_cols]
        .mean(axis=1, skipna=True)
    )

    df_dwd_solar_all.head()
    return (df_dwd_solar_all,)


@app.cell
def _(df_dwd_solar_all):
    plot_solar_cols = [
        col for col in df_dwd_solar_all.columns
        if "Solar Radiation" in col
        and "Average" not in col
    ]
    return (plot_solar_cols,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Interactive Comparison of Solar Radiation Across DWD Stations

    This section visualizes hourly solar radiation from all selected DWD solar stations using an interactive time-series plot.
    """)
    return


@app.cell
def _(df_dwd_solar_all, plot_solar_cols, px):
    df_solar_all_long = df_dwd_solar_all.melt(
        id_vars="Start date",
        value_vars=plot_solar_cols,
        var_name="Station",
        value_name="Solar Radiation [W/m²]",
    )

    df_solar_all_long["Station"] = (
        df_solar_all_long["Station"]
        .str.replace("Solar Radiation ", "")
        .str.replace(" [W/m²]", "")
    )

    fig_solar_all = px.line(
        df_solar_all_long,
        x="Start date",
        y="Solar Radiation [W/m²]",
        color="Station",
        title="Interactive Solar Radiation from All DWD Solar Stations"
    )

    fig_solar_all.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date"
        ),
        height=600
    )

    fig_solar_all.update_traces(
        hovertemplate=
        "<b>Station %{fullData.name}</b><br>" +
        "Date=%{x}<br>" +
        "Solar Radiation=%{y:,.2f} W/m²"
    )

    fig_solar_all.show()
    return


@app.cell
def _(df_dwd_solar_all, plot_solar_cols):
    df_dwd_solar_all["Average Solar Radiation [W/m²]"] = (
        df_dwd_solar_all[plot_solar_cols]
        .mean(axis=1, skipna=True)
    )

    df_dwd_solar_avg = df_dwd_solar_all[
        ["Start date", "Average Solar Radiation [W/m²]"]
    ]

    df_dwd_solar_avg.head()
    return (df_dwd_solar_avg,)


@app.cell
def _(df_dwd_solar_avg, df_smard_generation):
    df_solar_compare = df_smard_generation.merge(
        df_dwd_solar_avg,
        on="Start date",
        how="inner"
    )

    df_solar_compare[[
        "Start date",
        "Solar",
        "Average Solar Radiation [W/m²]"
    ]].head()
    return (df_solar_compare,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Normalized Comparison of Solar Generation and Solar Radiation
    Both solar generation and solar radiation were normalized to values between 0 and 1 in order to overcome differences in units and magnitude. This allows direct comparison of their temporal patterns and trends.
    """)
    return


@app.cell
def _(df_solar_compare, px):
    df_solar_compare["Solar Normalized"] = (
        df_solar_compare["Solar"]
        / df_solar_compare["Solar"].max()
    )

    df_solar_compare["Radiation Normalized"] = (
        df_solar_compare["Average Solar Radiation [W/m²]"]
        / df_solar_compare["Average Solar Radiation [W/m²]"].max()
    )

    fig_normalized = px.line(
        df_solar_compare,
        x="Start date",
        y=[
            "Solar Normalized",
            "Radiation Normalized"
        ],
        title="Normalized Solar Generation vs Solar Radiation"
    )

    fig_normalized.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date"
        ),
        height=550
    )

    fig_normalized.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Loading DWD Hourly Weather Data

    This section defines a reusable function for downloading hourly weather observations from the DWD Open Data platform.

    The function is used to load weather variables such as:
    - Temperature
    - Relative humidity
    - Wind speed
    - Cloud cover
    """)
    return


@app.cell
def _(io, pd, re, requests, zipfile):
    def load_dwd_hourly_data(
        category,
        station_id,
        start_date,
        end_date,
        file_prefix,
        data_prefix,
        rename_columns,
    ):

        base_url = (
            "https://opendata.dwd.de/climate_environment/CDC/"
            f"observations_germany/climate/hourly/{category}/recent/"
        )

        station_id = str(station_id).zfill(5)

        index_html = requests.get(base_url, timeout=30).text

        pattern = rf'href="({file_prefix}_{station_id}_akt\.zip)"'
        matches = re.findall(pattern, index_html)

        if not matches:
            raise ValueError(f"No recent file found for station {station_id}")

        zip_url = base_url + matches[0]

        response = requests.get(zip_url, timeout=30)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            data_file = [
                filename for filename in z.namelist()
                if filename.startswith(data_prefix)
            ][0]

            with z.open(data_file) as f:
                df_weather = pd.read_csv(
                    f,
                    sep=";",
                    encoding="latin1"
                )

        # important cleaning
        df_weather.columns = df_weather.columns.str.strip()

        print("Available columns:", df_weather.columns.tolist())

        df_weather["Start date"] = pd.to_datetime(
            df_weather["MESS_DATUM"],
            format="%Y%m%d%H",
            errors="coerce"
        )
        df_weather = df_weather.dropna(subset=["Start date"])
        df_weather = df_weather.rename(columns=rename_columns)

        df_weather = df_weather[
            (df_weather["Start date"] >= pd.to_datetime(start_date)) &
            (df_weather["Start date"] < pd.to_datetime(end_date))
        ]

        selected_cols = ["Start date"]

        for old_name, new_name in rename_columns.items():
            if new_name in df_weather.columns:
                selected_cols.append(new_name)

        return df_weather[selected_cols]

    return (load_dwd_hourly_data,)


@app.cell
def _(end_date, load_dwd_hourly_data, start_date):
    wind_station_ids = [
        "01048",  # Berlin
        "00433",  # North / coastal area example
        "02667",  # Central Germany example
        "05715",  # West / NRW example
        "01975",  # South Germany example
    ]

    wind_dfs = []

    for wind_station_id in wind_station_ids:
        print(f"Loading wind station {wind_station_id}...")

        df_station_wind = load_dwd_hourly_data(
            category="wind",
            station_id=wind_station_id,
            start_date=start_date,
            end_date=end_date,
            file_prefix="stundenwerte_FF",
            data_prefix="produkt_ff_stunde",
            rename_columns={
                "F": f"Wind Speed Station {wind_station_id} [m/s]",
            },
        )

        wind_dfs.append(df_station_wind)

    df_dwd_wind_avg = wind_dfs[0]

    for df_station_wind_source in wind_dfs[1:]:
        df_dwd_wind_avg = df_dwd_wind_avg.merge(
            df_station_wind_source,
            on="Start date",
            how="inner",
        )

    wind_speed_cols = [
        col for col in df_dwd_wind_avg.columns
        if "Wind Speed Station" in col
    ]

    df_dwd_wind_avg["Average Wind Speed [m/s]"] = (
        df_dwd_wind_avg[wind_speed_cols].mean(axis=1)
    )

    df_dwd_wind_avg.head()
    return (df_dwd_wind_avg,)


@app.cell
def _(df_dwd_wind_avg, df_smard_generation):
    df_wind_compare = df_smard_generation.merge(
        df_dwd_wind_avg[["Start date", "Average Wind Speed [m/s]"]],
        on="Start date",
        how="inner",
    )

    df_wind_compare["Total Wind Generation"] = (
        df_wind_compare["Wind Onshore"]
        + df_wind_compare["Wind Offshore"]
    )

    df_wind_compare.head()
    return


@app.cell
def _(re, requests):
    temp_base_url = (
        "https://opendata.dwd.de/climate_environment/CDC/"
        "observations_germany/climate/hourly/air_temperature/recent/"
    )

    temp_index_html = requests.get(temp_base_url, timeout=30).text

    _temperature_station_ids = re.findall(
        r'stundenwerte_TU_(\d{5})_akt\.zip',
        temp_index_html
    )

    print(f"Found {len(_temperature_station_ids)} temperature stations:")
    print(_temperature_station_ids)
    return


@app.cell
def _(end_date, load_dwd_hourly_data, start_date):
    temperature_station_ids = [
        "00044",
        "00073",
        "00078",
        "00091",
        "00096",
        "00102",
        "00125",
        "00131",
        "00142",
        "00150",
        "00151",
        "00154",
    ]

    temperature_dfs = []

    for temp_station_id in temperature_station_ids:
        print(f"Loading temperature station {temp_station_id}...")
        df_station_temp = load_dwd_hourly_data(
            category="air_temperature",
            station_id=temp_station_id,
            start_date=start_date,
            end_date=end_date,
            file_prefix="stundenwerte_TU",
            data_prefix="produkt_tu_stunde",
            rename_columns={
                "TT_TU": f"Temperature {temp_station_id} [°C]",
                "RF_TU": f"Humidity {temp_station_id} [%]",
            },
        )
        temperature_dfs.append(df_station_temp)

    df_dwd_temperature_all = temperature_dfs[0]

    for df_temp_source in temperature_dfs[1:]:
        df_dwd_temperature_all = df_dwd_temperature_all.merge(
            df_temp_source,
            on="Start date",
            how="outer",
        )

    df_dwd_temperature_all = df_dwd_temperature_all.sort_values("Start date")

    temperature_cols = [
        col for col in df_dwd_temperature_all.columns
        if "Temperature" in col
    ]

    humidity_cols = [
        col for col in df_dwd_temperature_all.columns
        if "Humidity" in col
    ]

    # Clean -999 sentinel values before averaging
    df_dwd_temperature_all[temperature_cols] = df_dwd_temperature_all[temperature_cols].replace(-999, float("nan"))
    df_dwd_temperature_all[humidity_cols] = df_dwd_temperature_all[humidity_cols].replace(-999, float("nan"))

    df_dwd_temperature_all["Average Temperature [°C]"] = (
        df_dwd_temperature_all[temperature_cols].mean(axis=1, skipna=True)
    )

    df_dwd_temperature_all["Average Humidity [%]"] = (
        df_dwd_temperature_all[humidity_cols].mean(axis=1, skipna=True)
    )

    df_dwd_temperature_all.head()
    return (df_dwd_temperature_all,)


@app.cell
def _(df_dwd_temperature_all, px):
    fig_temp = px.line(
        df_dwd_temperature_all,
        x="Start date",
        y="Average Temperature [°C]",
        title="Average Temperature Across Germany"
    )

    fig_temp.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date"
        ),
        height=500
    )

    fig_temp.show()
    return


@app.cell
def _(df_dwd_temperature_all, px):
    fig_humidity = px.line(
        df_dwd_temperature_all,
        x="Start date",
        y="Average Humidity [%]",
        title="Average Relative Humidity Across Germany"
    )

    fig_humidity.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date"
        ),
        height=500
    )

    fig_humidity.show()
    return


@app.cell
def _(df_dwd_temperature_all, df_solar_compare):
    df_master = df_solar_compare.merge(
        df_dwd_temperature_all[
            [
                "Start date",
                "Average Temperature [°C]",
                "Average Humidity [%]",
            ]
        ],
        on="Start date",
        how="inner",
    )

    df_master.head()
    return (df_master,)


@app.cell
def _(df_master):
    df_solar_weather = df_master[
        [
            "Start date",
            "Solar",
            "Average Solar Radiation [W/m²]",
            "Solar Normalized",
            "Radiation Normalized",
            "Average Temperature [°C]",
            "Average Humidity [%]",
        ]
    ]

    df_solar_weather.head()
    return (df_solar_weather,)


@app.cell
def _(df_solar_weather):
    corr_matrix = df_solar_weather[
        [
            "Solar",
            "Average Solar Radiation [W/m²]",
            "Average Temperature [°C]",
            "Average Humidity [%]",
        ]
    ].corr()

    corr_matrix
    return


if __name__ == "__main__":
    app.run()
