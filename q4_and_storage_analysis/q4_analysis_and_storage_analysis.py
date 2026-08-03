import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import pandas as pd
    import requests
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    import matplotlib.dates as mdates
    import plotly.express as px
    import zipfile
    import io
    import re
    import marimo as mo
    from pathlib import Path
    import os
    from utils import load_smard_series
    from utils import load_smard_market_trade
    from sqlalchemy import create_engine, inspect


    return (
        Path,
        create_engine,
        inspect,
        io,
        load_smard_market_trade,
        load_smard_series,
        mo,
        np,
        pd,
        plt,
        px,
        re,
        requests,
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
    return conventional_cols, renewable_cols


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

    # Keep only Oct-Dec 2025
    df_interactive = df_interactive[
        (df_interactive["Start date"] >= "2025-10-01") &
        (df_interactive["Start date"] <= "2025-12-31")
    ].copy()

    df_renewables_interactive = df_interactive.melt(
        id_vars="Start date",
        value_vars=renewable_cols,
        var_name="Source",
        value_name="Production [MWh]",
    )

    df_renewables_interactive["Production [MWh]"] = pd.to_numeric(
        df_renewables_interactive["Production [MWh]"],
        errors="coerce",
    )

    df_renewables_interactive = df_renewables_interactive.dropna(
        subset=["Production [MWh]"]
    )

    fig_renewable = px.line(
        df_renewables_interactive,
        x="Start date",
        y="Production [MWh]",
        color="Source",
        render_mode="svg",   # Prevents WebGL issues
        title="Renewable Energy Sources – Oct to Dec 2025",
    )

    fig_renewable.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date",
        ),
        height=500,
    )

    fig_renewable.update_traces(
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            "Date: %{x|%d-%b-%Y}<br>"
            "Energy: %{y:,.0f} MWh"
            "<extra></extra>"
        )
    )

    fig_renewable.show()
    return


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
def _(conventional_cols, df_smard_generation, pd, px):
    def _():
        df_interactive = df_smard_generation.copy()
        df_interactive["Start date"] = pd.to_datetime(df_interactive["Start date"])

        # Keep only Oct-Dec 2025
        df_interactive = df_interactive[
            (df_interactive["Start date"] >= "2025-10-01") &
            (df_interactive["Start date"] <= "2025-12-31")
        ].copy()

        df_conventional_interactive = df_interactive.melt(
            id_vars="Start date",
            value_vars=conventional_cols,
            var_name="Source",
            value_name="Production [MWh]",
        )

        # Ensure correct data types
        df_conventional_interactive["Start date"] = pd.to_datetime(
            df_conventional_interactive["Start date"]
        )

        df_conventional_interactive["Production [MWh]"] = pd.to_numeric(
            df_conventional_interactive["Production [MWh]"],
            errors="coerce",
        )

        df_conventional_interactive = df_conventional_interactive.dropna(
            subset=["Production [MWh]"]
        )

        fig_conventional = px.line(
            df_conventional_interactive,
            x="Start date",
            y="Production [MWh]",
            color="Source",
            render_mode="svg",   # Prevents WebGL
            title="Conventional Energy Sources – Oct to Dec 2025",
        )

        fig_conventional.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
                type="date",
            ),
            height=500,
        )

        fig_conventional.update_traces(
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "Date: %{x|%d-%b-%Y}<br>"
                "Energy: %{y:,.0f} MWh"
                "<extra></extra>"
            )
        )
        return fig_conventional.show()


    _()
    return


@app.cell
def _(df_smard_consumption, df_smard_generation):
    df_generation_q4 = df_smard_generation[
        df_smard_generation["Start date"].dt.month.isin([10, 11, 12])
    ]

    df_consumption_q4 = df_smard_consumption[
        df_smard_consumption["Start date"].dt.month.isin([10, 11, 12])
    ]
    return df_consumption_q4, df_generation_q4


@app.cell
def _(df_generation_q4):
    total_generation_q4_twh = (
        df_generation_q4
        .drop(columns=["Start date"])
        .sum()
        .sum()
        / 1_000_000
    )

    print(total_generation_q4_twh)
    return (total_generation_q4_twh,)


@app.cell
def _(df_generation_q4, renewable_cols):
    total_renewable_q4_twh = (
        df_generation_q4[renewable_cols]
        .sum()
        .sum()
        / 1_000_000
    )

    print(total_renewable_q4_twh)
    return (total_renewable_q4_twh,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Why conventional energy(lignite and fossil fuel) contribution is less on winter?
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
def _(conventional_cols, df_generation_q4):
    total_conventional_q4_twh = (
        df_generation_q4[conventional_cols]
        .sum()
        .sum()
        / 1_000_000
    )

    print(total_conventional_q4_twh)
    return (total_conventional_q4_twh,)


@app.cell
def _(df_consumption_q4):
    total_consumption_q4_twh = (
        df_consumption_q4["Consumption"]
        .sum()
        / 1_000_000
    )

    print(total_consumption_q4_twh)
    return


@app.cell
def _(total_generation_q4_twh, total_renewable_q4_twh):
    renewable_share_q4 = (
        total_renewable_q4_twh
        / total_generation_q4_twh
        * 100
    )

    print(renewable_share_q4)
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
        df_compare_interactive["Start date"],
        errors="coerce",
    )

    # Keep only Oct-Dec 2025
    df_compare_interactive = df_compare_interactive[
        (df_compare_interactive["Start date"] >= "2025-10-01")
        & (df_compare_interactive["Start date"] < "2026-01-01")
    ].copy()

    # Ensure generation columns are numeric
    for column in renewable_cols + conventional_cols:
        df_compare_interactive[column] = pd.to_numeric(
            df_compare_interactive[column],
            errors="coerce",
        )

    df_compare_interactive["Total Renewable Generation"] = (
        df_compare_interactive[renewable_cols]
        .sum(axis=1, min_count=1)
    )

    df_compare_interactive["Total Conventional Generation"] = (
        df_compare_interactive[conventional_cols]
        .sum(axis=1, min_count=1)
    )

    # Prepare consumption data
    df_consumption_compare = df_smard_consumption[
        ["Start date", "Consumption"]
    ].copy()

    df_consumption_compare["Start date"] = pd.to_datetime(
        df_consumption_compare["Start date"],
        errors="coerce",
    )

    df_consumption_compare["Consumption"] = pd.to_numeric(
        df_consumption_compare["Consumption"],
        errors="coerce",
    )

    df_consumption_compare = df_consumption_compare[
        (df_consumption_compare["Start date"] >= "2025-10-01")
        & (df_consumption_compare["Start date"] < "2026-01-01")
    ].copy()

    # Merge generation and consumption
    df_compare_interactive = df_compare_interactive.merge(
        df_consumption_compare,
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

    df_compare_long = df_compare_long.dropna(
        subset=[
            "Start date",
            "Energy [MWh]",
        ]
    )

    fig_compare = px.line(
        df_compare_long,
        x="Start date",
        y="Energy [MWh]",
        color="Category",
        render_mode="svg",
        title=(
            "Renewable vs Conventional Generation vs "
            "Electricity Demand — Oct to Dec 2025"
        ),
    )

    fig_compare.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date",
        ),
        height=550,
    )

    fig_compare.update_traces(
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            "Date: %{x|%d-%b-%Y %H:%M}<br>"
            "Energy: %{y:,.0f} MWh"
            "<extra></extra>"
        )
    )

    fig_compare.show()
    return (df_compare_interactive,)


@app.cell
def _(
    conventional_cols,
    df_smard_consumption,
    df_smard_generation,
    pd,
    plt,
    renewable_cols,
):
    def _():
        # ============================================================
        # Prepare hourly comparison data
        # ============================================================

        df_q4_comparison = df_smard_generation.copy()

        df_q4_comparison["Start date"] = pd.to_datetime(
            df_q4_comparison["Start date"]
        )

        df_q4_comparison["Total Renewable Generation"] = (
            df_q4_comparison[renewable_cols].sum(axis=1)
        )

        df_q4_comparison["Total Conventional Generation"] = (
            df_q4_comparison[conventional_cols].sum(axis=1)
        )

        df_q4_comparison = df_q4_comparison.merge(
            df_smard_consumption[
                ["Start date", "Consumption"]
            ],
            on="Start date",
            how="inner",
        )

        # Filter Q4 2025
        df_q4_comparison = df_q4_comparison[
            (df_q4_comparison["Start date"] >= "2025-10-01")
            & (df_q4_comparison["Start date"] < "2026-01-01")
        ].copy()

        # ============================================================
        # Daily average values for a readable thesis figure
        # ============================================================

        df_daily_q4_comparison = (
            df_q4_comparison
            .set_index("Start date")
            [
                [
                    "Total Renewable Generation",
                    "Total Conventional Generation",
                    "Consumption",
                ]
            ]
            .resample("D")
            .mean()
            .reset_index()
        )

        dates = df_daily_q4_comparison["Start date"]

        # ============================================================
        # Plot
        # ============================================================

        fig_q4_comparison, ax = plt.subplots(
            figsize=(7.2, 4.2)
        )

        ax.plot(
            dates,
            df_daily_q4_comparison[
                "Total Renewable Generation"
            ],
            label="Renewable Generation",
            color="#636EFA",
            linewidth=1.6,
        )

        ax.plot(
            dates,
            df_daily_q4_comparison[
                "Total Conventional Generation"
            ],
            label="Conventional Generation",
            color="#EF553B",
            linewidth=1.6,
        )

        ax.plot(
            dates,
            df_daily_q4_comparison["Consumption"],
            label="Electricity Demand",
            color="#00A88F",
            linewidth=1.6,
        )

        # ============================================================
        # Title and axis labels
        # ============================================================

        ax.set_title(
            "Renewable and Conventional Generation vs Electricity Demand -- Germany, Q4 2025",
            fontsize=10,
            pad=18,
        )

        ax.set_xlabel(
            "Date",
            fontsize=8.5,
            labelpad=8,
        )

        ax.set_ylabel(
            "Average energy per hour [MWh/h]",
            fontsize=8.5,
            labelpad=8,
        )

        # ============================================================
        # Fixed Q4 date ticks
        # ============================================================

        tick_dates = [
            pd.Timestamp("2025-10-05"),
            pd.Timestamp("2025-10-19"),
            pd.Timestamp("2025-11-02"),
            pd.Timestamp("2025-11-16"),
            pd.Timestamp("2025-11-30"),
            pd.Timestamp("2025-12-14"),
            pd.Timestamp("2025-12-28"),
        ]

        tick_labels = [
            "Oct 5",
            "Oct 19",
            "Nov 2",
            "Nov 16",
            "Nov 30",
            "Dec 14",
            "Dec 28",
        ]

        ax.set_xticks(tick_dates)

        ax.set_xticklabels(
            tick_labels,
            rotation=0,
            ha="center",
        )

        ax.set_xlim(
            pd.Timestamp("2025-10-01"),
            pd.Timestamp("2025-12-31"),
        )

        # ============================================================
        # Styling
        # ============================================================

        ax.yaxis.grid(
            True,
            color="#D9D9D9",
            linewidth=0.5,
        )

        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.spines["left"].set_color("#BBBBBB")
        ax.spines["bottom"].set_color("#BBBBBB")

        ax.spines["left"].set_linewidth(0.5)
        ax.spines["bottom"].set_linewidth(0.5)

        ax.tick_params(
            axis="both",
            labelsize=7,
            width=0.4,
            length=3,
        )

        ax.legend(
            frameon=False,
            loc="upper right",
            fontsize=7.5,
        )

        fig_q4_comparison.subplots_adjust(
            left=0.12,
            right=0.98,
            bottom=0.17,
            top=0.86,
        )

        # ============================================================
        # Save PGF and PDF
        # ============================================================

        from pathlib import Path

        output_dir = Path("figures")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_pgf = output_dir / "q4_comparison.pgf"
        output_pdf = output_dir / "q4_comparison.pdf"

        fig_q4_comparison.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
            pad_inches=0.04,
        )

        fig_q4_comparison.savefig(
            output_pdf,
            bbox_inches="tight",
            pad_inches=0.04,
        )

        plt.close(fig_q4_comparison)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)

        return df_daily_q4_comparison


    _()
    return


@app.cell
def _(pd, px, total_conventional_q4_twh, total_renewable_q4_twh):


    df_q4_mix = pd.DataFrame({
        "Source": ["Renewable", "Conventional"],
        "Generation [TWh]": [
            total_renewable_q4_twh,
            total_conventional_q4_twh
        ]
    })

    fig_q4_mix = px.pie(
        df_q4_mix,
        names="Source",
        values="Generation [TWh]",
        title="German Electricity Generation Mix (Q4 2025)"
    )

    fig_q4_mix.show()
    return


@app.cell
def _(plt, total_conventional_q4_twh, total_renewable_q4_twh):
    def _():
        from pathlib import Path

        labels = ["Renewable", "Conventional"]

        values = [
            total_renewable_q4_twh,
            total_conventional_q4_twh,
        ]

        colors = [
            "#2A9D8F",
            "#6C757D",
        ]

        fig_q4_mix, ax = plt.subplots(
            figsize=(5.8, 4.8)
        )

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            startangle=90,
            counterclock=False,
            autopct=lambda pct: rf"{pct:.1f}\%",
            pctdistance=0.78,
            wedgeprops={
                "width": 0.45,
                "edgecolor": "white",
                "linewidth": 0.8,
            },
            textprops={
                "fontsize": 8,
            },
        )

        # Improve percentage-label visibility
        for text in autotexts:
            text.set_color("white")
            text.set_fontsize(8)

        ax.set_title(
            "Electricity Generation Mix -- Germany, Q4 2025",
            fontsize=10,
            pad=12,
        )

        ax.set_aspect("equal")

        # ============================================================
        # Save PGF and PDF inside the project repository
        # ============================================================

        Path("figures").mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pgf = "figures/q4_mix.pgf"
        output_pdf = "figures/q4_mix.pdf"

        fig_q4_mix.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
            pad_inches=0.04,
        )

        fig_q4_mix.savefig(
            output_pdf,
            bbox_inches="tight",
            pad_inches=0.04,
        )

        plt.close(fig_q4_mix)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)


    _()
    return


@app.cell
def _(df_generation_q4, px, renewable_cols):
    df_q4_renewable_monthly = df_generation_q4.copy()

    df_q4_renewable_monthly["Month"] = (
        df_q4_renewable_monthly["Start date"].dt.strftime("%b 2025")
    )

    renewable_monthly_q4 = (
        df_q4_renewable_monthly
        .groupby("Month")[renewable_cols]
        .sum()
        .reindex(["Oct 2025", "Nov 2025", "Dec 2025"])
        / 1_000_000
    )

    renewable_monthly_q4_long = (
        renewable_monthly_q4
        .reset_index()
        .melt(
            id_vars="Month",
            var_name="Renewable Source",
            value_name="Generation [TWh]"
        )
    )

    fig_q4_renewable_bar = px.bar(
        renewable_monthly_q4_long,
        x="Month",
        y="Generation [TWh]",
        color="Renewable Source",
        barmode="stack",
        title="Monthly Renewable Electricity Generation by Source — Oct to Dec 2025",
    )

    fig_q4_renewable_bar.update_layout(
        template="plotly_white",
        height=520,
        width=950,
        xaxis_title="Month",
        yaxis_title="Generation [TWh]",
        legend_title="Renewable source",
    )

    fig_q4_renewable_bar.show()

    renewable_monthly_q4.round(2)
    return


@app.cell
def _(conventional_cols, df_generation_q4, renewable_cols):
    df_q4_mix_monthly = df_generation_q4.copy()

    df_q4_mix_monthly["Month"] = (
        df_q4_mix_monthly["Start date"].dt.strftime("%b")
    )

    month_order_q4 = ["Oct", "Nov", "Dec"]

    all_generation_cols = renewable_cols + conventional_cols

    monthly_generation_mix_q4 = (
        df_q4_mix_monthly
        .groupby("Month")[all_generation_cols]
        .sum()
        .reindex(month_order_q4)
        / 1_000_000
    )

    monthly_generation_mix_q4.round(2)
    return all_generation_cols, monthly_generation_mix_q4


@app.cell
def _(conventional_cols, df_generation_q4, px, renewable_cols):
    def _():
        df_q4_mix_monthly = df_generation_q4.copy()

        df_q4_mix_monthly["Month"] = (
            df_q4_mix_monthly["Start date"].dt.strftime("%b")
        )

        month_order = ["Oct", "Nov", "Dec"]

        all_generation_cols = renewable_cols + conventional_cols

        monthly_generation_mix_q4 = (
            df_q4_mix_monthly
            .groupby("Month")[all_generation_cols]
            .sum()
            .reindex(month_order)
            / 1_000_000
        )

        monthly_generation_mix_q4_long = (
            monthly_generation_mix_q4
            .reset_index()
            .melt(
                id_vars="Month",
                var_name="Source",
                value_name="Generation [TWh]"
            )
        )

        color_map = {
            "Wind Onshore": "#4E79A7",
            "Wind Offshore": "#A0CBE8",
            "Solar": "#F6C85F",
            "Hydropower": "#86BCB6",
            "Biomass": "#8CD17D",
            "Other Renewable": "#D9D9D9",
            "Lignite": "#9C755F",
            "Hard Coal": "#595959",
            "Fossil Gas": "#E07B39",
            "Hydro Pumped Storage": "#B699D2",
            "Other Conventional": "#BAB0AC",
        }

        fig_mix = px.bar(
            monthly_generation_mix_q4_long,
            x="Month",
            y="Generation [TWh]",
            color="Source",
            barmode="stack",
            title="Monthly Electricity Generation Mix by Source (Q4 2025)",
            color_discrete_map=color_map,
        )

        fig_mix.update_layout(
            template="plotly_white",
            width=1000,
            height=550,
            xaxis_title="Month",
            yaxis_title="Generation [TWh]",
            legend_title="Generation source",
            legend=dict(
                orientation="v",
                y=1,
                x=1.02,
            ),
            margin=dict(l=70, r=170, t=80, b=70),
        )

        fig_mix.update_yaxes(
            gridcolor="lightgray",
            zeroline=False,
        )
        fig_mix.update_traces(
        width=0.4
        )

        fig_mix.show()
        return monthly_generation_mix_q4.round(2)


    _()
    return


@app.cell
def _(all_generation_cols, monthly_generation_mix_q4, np):
    def _():
        from pathlib import Path

        import matplotlib
        matplotlib.use("pgf")

        import matplotlib.pyplot as plt

        source_colors = {
            "Wind Onshore": "#2E86AB",
            "Wind Offshore": "#7EC8E3",
            "Solar": "#F6C85F",
            "Hydropower": "#88CC88",
            "Biomass": "#6BA368",
            "Other Renewable": "#D9D9D9",
            "Lignite": "#8C6D62",
            "Hard Coal": "#5B5B5B",
            "Fossil Gas": "#C97C5D",
            "Hydro Pumped Storage": "#A7A1E8",
            "Other Conventional": "#BDBDBD",
        }

        fig, ax = plt.subplots(figsize=(8, 5))

        bottom = np.zeros(len(monthly_generation_mix_q4))

        for source in all_generation_cols:
            ax.bar(
                monthly_generation_mix_q4.index,
                monthly_generation_mix_q4[source],
                bottom=bottom,
                color=source_colors[source],
                label=source,
                width=0.55,
            )
            bottom += monthly_generation_mix_q4[source].values

        ax.set_title("Monthly Electricity Generation Mix by Source (Q4 2025)")
        ax.set_xlabel("Month")
        ax.set_ylabel("Generation [TWh]")

        ax.grid(axis="y", alpha=0.3)
        ax.set_axisbelow(True)

        ax.legend(
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            fontsize=8,
            frameon=False,
        )

        plt.tight_layout()

        # ============================================================
        # Save PGF and PDF inside the project repository
        # ============================================================

        Path("figures").mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pgf = "figures/generation_mix_q4.pgf"
        output_pdf = "figures/generation_mix_q4.pdf"

        fig.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
        )

        fig.savefig(
            output_pdf,
            bbox_inches="tight",
        )

        plt.close(fig)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)


    _()
    return


@app.cell
def _(df_generation_q4, px, renewable_cols):
    df_q4_renewable_totals = df_generation_q4.copy()

    renewable_totals_q4 = (
        df_q4_renewable_totals[renewable_cols]
        .sum()
        .sort_values(ascending=True)   # important for Plotly horizontal bar
        / 1_000_000
    )

    renewable_total_colors = {
        "Wind Onshore": "#2E86AB",
        "Solar": "#F6C85F",
        "Biomass": "#6BA368",
        "Wind Offshore": "#7EC8E3",
        "Hydropower": "#5DADE2",
        "Other Renewable": "#9ACD32",
    }

    fig_q4_renewable_totals = px.bar(
        renewable_totals_q4.reset_index(),
        x=0,
        y="index",
        orientation="h",
        color="index",
        color_discrete_map=renewable_total_colors,
        text=0,
        title="Renewable Generation by Source (Q4 2025)",
    )

    fig_q4_renewable_totals.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
        marker_line_width=0,
    )

    fig_q4_renewable_totals.update_layout(
        template="plotly_white",
        width=850,
        height=450,
        showlegend=False,
        xaxis_title="Generation [TWh]",
        yaxis_title="",
    )

    fig_q4_renewable_totals.update_yaxes(
        autorange="reversed"
    )

    fig_q4_renewable_totals.show()

    renewable_totals_q4.sort_values(ascending=False).round(2)
    return


@app.cell
def _(df_generation_q4, plt, renewable_cols):
    def save_q4_renewable_totals_pgf():
        from pathlib import Path

        renewable_totals = (
            df_generation_q4[renewable_cols]
            .sum()
            .sort_values(ascending=True)
            / 1_000_000
        )

        colors = {
            "Wind Onshore": "#2E86AB",
            "Solar": "#F6C85F",
            "Biomass": "#6BA368",
            "Wind Offshore": "#7EC8E3",
            "Hydropower": "#5DADE2",
            "Other Renewable": "#9ACD32",
        }

        fig, ax = plt.subplots(figsize=(6.5, 3.8))

        bars = ax.barh(
            renewable_totals.index,
            renewable_totals.values,
            color=[colors[s] for s in renewable_totals.index],
            height=0.7,
        )

        # Highest source at the top
        ax.invert_yaxis()

        # Labels
        for bar in bars:
            width = bar.get_width()

            ax.text(
                width + 0.2,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.2f}",
                va="center",
                fontsize=9,
            )

        ax.set_title("Renewable Generation by Source (Q4 2025)")
        ax.set_xlabel("Generation [TWh]")
        ax.set_ylabel("")

        ax.grid(axis="x", alpha=0.3)
        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout()

        # ============================================================
        # Save PGF and PDF inside the project repository
        # ============================================================

        Path("figures").mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pgf = "figures/renewable_generation_q4.pgf"
        output_pdf = "figures/renewable_generation_q4.pdf"

        fig.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
        )

        fig.savefig(
            output_pdf,
            bbox_inches="tight",
        )

        plt.close(fig)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)


    save_q4_renewable_totals_pgf()
    return


@app.cell
def _(
    conventional_cols,
    df_smard_consumption,
    df_smard_generation,
    pd,
    renewable_cols,
):
    def _():
        df_q4_metrics = (
            df_smard_generation.copy()
            .merge(
                df_smard_consumption[
                    ["Start date", "Consumption", "Residual Load"]
                ],
                on="Start date",
                how="inner",
            )
        )

        df_q4_metrics["Month"] = df_q4_metrics["Start date"].dt.strftime("%b")

        df_q4_metrics["Renewable Generation"] = (
            df_q4_metrics[renewable_cols].sum(axis=1)
        )

        df_q4_metrics["Conventional Generation"] = (
            df_q4_metrics[conventional_cols].sum(axis=1)
        )

        df_q4_metrics["Domestic Generation"] = (
            df_q4_metrics["Renewable Generation"]
            + df_q4_metrics["Conventional Generation"]
        )

        df_q4_metrics["Generation Balance"] = (
            df_q4_metrics["Domestic Generation"]
            - df_q4_metrics["Consumption"]
        )

        df_q4_metrics["Renewable Balance"] = (
            df_q4_metrics["Renewable Generation"]
            - df_q4_metrics["Consumption"]
        )

        df_q4_metrics["Net Import Proxy"] = (
            df_q4_metrics["Generation Balance"].clip(upper=0).abs()
        )

        df_q4_metrics["Net Export Proxy"] = (
            df_q4_metrics["Generation Balance"].clip(lower=0)
        )

        month_order_q4 = ["Oct", "Nov", "Dec"]

        headline_metrics_q4 = (
            df_q4_metrics
            .groupby("Month")
            .agg(
                Total_electricity_demand_TWh=("Consumption", lambda x: x.sum() / 1_000_000),
                Total_domestic_generation_TWh=("Domestic Generation", lambda x: x.sum() / 1_000_000),
                Renewable_generation_TWh=("Renewable Generation", lambda x: x.sum() / 1_000_000),
                Conventional_and_balancing_generation_TWh=("Conventional Generation", lambda x: x.sum() / 1_000_000),
                Average_residual_load_MWh_h=("Residual Load", "mean"),
                Maximum_hourly_residual_load_MWh_h=("Residual Load", "max"),

                # Renewables alone are enough
                Hours_when_renewables_met_demand=("Renewable Balance", lambda x: (x >= 0).sum()),

                Net_import_hours_proxy=("Generation Balance", lambda x: (x < 0).sum()),
                Net_export_hours_proxy=("Generation Balance", lambda x: (x > 0).sum()),
                Net_import_energy_proxy_TWh=("Net Import Proxy", lambda x: x.sum() / 1_000_000),
                Exportable_surplus_proxy_TWh=("Net Export Proxy", lambda x: x.sum() / 1_000_000),
            )
            .reindex(month_order_q4)
        )

        headline_metrics_q4["Renewable share of domestic generation [%]"] = (
            headline_metrics_q4["Renewable_generation_TWh"]
            / headline_metrics_q4["Total_domestic_generation_TWh"]
            * 100
        )

        headline_metrics_q4["Renewable share of electricity demand [%]"] = (
            headline_metrics_q4["Renewable_generation_TWh"]
            / headline_metrics_q4["Total_electricity_demand_TWh"]
            * 100
        )

        headline_metrics_q4 = headline_metrics_q4[
            [
                "Total_electricity_demand_TWh",
                "Total_domestic_generation_TWh",
                "Renewable_generation_TWh",
                "Conventional_and_balancing_generation_TWh",
                "Renewable share of domestic generation [%]",
                "Renewable share of electricity demand [%]",
                "Average_residual_load_MWh_h",
                "Maximum_hourly_residual_load_MWh_h",
                "Hours_when_renewables_met_demand",
                "Net_import_hours_proxy",
                "Net_export_hours_proxy",
                "Net_import_energy_proxy_TWh",
                "Exportable_surplus_proxy_TWh",
            ]
        ]

        q4_total = pd.Series(name="Q4 Total", dtype="float64")

        q4_total["Total_electricity_demand_TWh"] = headline_metrics_q4["Total_electricity_demand_TWh"].sum()
        q4_total["Total_domestic_generation_TWh"] = headline_metrics_q4["Total_domestic_generation_TWh"].sum()
        q4_total["Renewable_generation_TWh"] = headline_metrics_q4["Renewable_generation_TWh"].sum()
        q4_total["Conventional_and_balancing_generation_TWh"] = headline_metrics_q4["Conventional_and_balancing_generation_TWh"].sum()

        q4_total["Renewable share of domestic generation [%]"] = (
            q4_total["Renewable_generation_TWh"]
            / q4_total["Total_domestic_generation_TWh"]
            * 100
        )

        q4_total["Renewable share of electricity demand [%]"] = (
            q4_total["Renewable_generation_TWh"]
            / q4_total["Total_electricity_demand_TWh"]
            * 100
        )

        q4_total["Average_residual_load_MWh_h"] = df_q4_metrics["Residual Load"].mean()
        q4_total["Maximum_hourly_residual_load_MWh_h"] = df_q4_metrics["Residual Load"].max()

        q4_total["Hours_when_renewables_met_demand"] = (
            df_q4_metrics["Renewable Balance"] >= 0
        ).sum()

        q4_total["Net_import_hours_proxy"] = headline_metrics_q4["Net_import_hours_proxy"].sum()
        q4_total["Net_export_hours_proxy"] = headline_metrics_q4["Net_export_hours_proxy"].sum()
        q4_total["Net_import_energy_proxy_TWh"] = headline_metrics_q4["Net_import_energy_proxy_TWh"].sum()
        q4_total["Exportable_surplus_proxy_TWh"] = headline_metrics_q4["Exportable_surplus_proxy_TWh"].sum()

        headline_metrics_q4 = pd.concat(
            [headline_metrics_q4, q4_total.to_frame().T]
        )

        return headline_metrics_q4.round(2)


    _()
    return


@app.cell
def _(df_generation_q4, plt, renewable_cols):
    def _():
        from pathlib import Path

        renewable_totals_q4 = (
            df_generation_q4[renewable_cols]
            .sum()
            .sort_values(ascending=True)
            / 1_000_000
        )

        renewable_total_colors = {
            "Wind Onshore": "#2E86AB",
            "Solar": "#F6C85F",
            "Biomass": "#6BA368",
            "Wind Offshore": "#7EC8E3",
            "Hydropower": "#5DADE2",
            "Other Renewable": "#9ACD32",
        }

        sources = renewable_totals_q4.index.tolist()
        values = renewable_totals_q4.values

        fig_renewable_generation_q4, ax = plt.subplots(
            figsize=(7.0, 4.2)
        )

        bars = ax.barh(
            sources,
            values,
            height=0.65,
            color=[
                renewable_total_colors[source]
                for source in sources
            ],
            edgecolor="none",
        )

        # Largest bar at the top
        ax.invert_yaxis()

        # Value labels
        for bar, value in zip(bars, values):
            ax.text(
                value + 0.25,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.2f}",
                ha="left",
                va="center",
                fontsize=8,
            )

        ax.set_title(
            "Renewable Generation by Source — Germany, Q4 2025",
            fontsize=10,
            pad=14,
        )

        ax.set_xlabel(
            "Generation [TWh]",
            fontsize=8.5,
            labelpad=7,
        )

        ax.set_ylabel("")

        ax.set_xlim(
            0,
            values.max() * 1.15,
        )

        # Remove grid lines
        ax.grid(False)

        # Clean publication style
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.spines["left"].set_color("#BBBBBB")
        ax.spines["bottom"].set_color("#BBBBBB")

        ax.spines["left"].set_linewidth(0.5)
        ax.spines["bottom"].set_linewidth(0.5)

        ax.tick_params(
            axis="both",
            labelsize=8,
            width=0.5,
            length=3,
        )

        fig_renewable_generation_q4.subplots_adjust(
            left=0.23,
            right=0.96,
            bottom=0.18,
            top=0.88,
        )

        # ============================================================
        # Save PGF and PDF inside the project repository
        # ============================================================

        Path("figures").mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pgf = "figures/renewable_generation_q4.pgf"
        output_pdf = "figures/renewable_generation_q4.pdf"

        fig_renewable_generation_q4.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
            pad_inches=0.04,
        )

        fig_renewable_generation_q4.savefig(
            output_pdf,
            bbox_inches="tight",
            pad_inches=0.04,
        )

        plt.close(fig_renewable_generation_q4)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)

        return renewable_totals_q4.sort_values(
            ascending=False
        ).round(2)


    _()
    return


@app.cell
def _(
    conventional_cols,
    df_smard_consumption,
    df_smard_generation,
    renewable_cols,
):
    def _():
        df_balance = (
            df_smard_generation.copy()
            .merge(
                df_smard_consumption[["Start date", "Consumption"]],
                on="Start date",
                how="inner",
            )
        )

        df_balance["Month"] = df_balance["Start date"].dt.strftime("%b")

        df_balance["Renewables"] = df_balance[renewable_cols].sum(axis=1)
        df_balance["Conventional"] = df_balance[conventional_cols].sum(axis=1)

        df_balance["Generation"] = (
            df_balance["Renewables"]
            + df_balance["Conventional"]
        )

        df_balance["Net import proxy"] = (
            df_balance["Consumption"]
            - df_balance["Generation"]
        ).clip(lower=0)

        month_order_q4 = ["Oct", "Nov", "Dec"]

        monthly_balance_q4 = (
            df_balance
            .groupby("Month")
            .agg(
                Demand_TWh=("Consumption", lambda x: x.sum() / 1_000_000),
                Generation_TWh=("Generation", lambda x: x.sum() / 1_000_000),
                Renewables_TWh=("Renewables", lambda x: x.sum() / 1_000_000),
                Conventional_TWh=("Conventional", lambda x: x.sum() / 1_000_000),
                Net_import_proxy_TWh=("Net import proxy", lambda x: x.sum() / 1_000_000),
            )
            .reindex(month_order_q4)
        )

        monthly_balance_q4["Renewable share of demand [%]"] = (
            monthly_balance_q4["Renewables_TWh"]
            / monthly_balance_q4["Demand_TWh"]
            * 100
        )

        monthly_balance_q4 = monthly_balance_q4[
            [
                "Demand_TWh",
                "Generation_TWh",
                "Renewables_TWh",
                "Conventional_TWh",
                "Renewable share of demand [%]",
                "Net_import_proxy_TWh",
            ]
        ]

        return monthly_balance_q4.round(2)


    _()
    return


@app.cell
def _(df_smard_generation, go, pd):
    def _():
        df_wind = df_smard_generation.copy()

        df_wind["Start date"] = pd.to_datetime(df_wind["Start date"])

        # Total wind generation
        df_wind["Wind Total"] = (
            df_wind["Wind Onshore"] +
            df_wind["Wind Offshore"]
        )

        # -----------------------------
        # Q4 2025
        # -----------------------------
        df_q4 = df_wind[
            (df_wind["Start date"] >= "2025-10-01") &
            (df_wind["Start date"] < "2026-01-01")
        ]

        # -----------------------------
        # Daily averages
        # -----------------------------
        daily = (
            df_q4
            .set_index("Start date")
            [["Wind Total", "Wind Onshore", "Wind Offshore"]]
            .resample("D")
            .mean()
            .reset_index()
        )

        # -----------------------------
        # Interactive Plot
        # -----------------------------
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=daily["Start date"],
                y=daily["Wind Total"],
                mode="lines",
                name="Total Wind",
                line=dict(width=3)
            )
        )

        fig.add_trace(
            go.Scatter(
                x=daily["Start date"],
                y=daily["Wind Onshore"],
                mode="lines",
                name="Wind Onshore",
                line=dict(width=2)
            )
        )

        fig.add_trace(
            go.Scatter(
                x=daily["Start date"],
                y=daily["Wind Offshore"],
                mode="lines",
                name="Wind Offshore",
                line=dict(width=2)
            )
        )

        fig.update_layout(
            title="Daily Average Wind Generation (Q4 2025)",
            xaxis_title="Date",
            yaxis_title="Average MWh per Hour",
            template="plotly_white",
            hovermode="x unified",
            width=1100,
            height=500,
            legend=dict(
                x=0.01,
                y=0.99,
                bgcolor="rgba(255,255,255,0.7)"
            )
        )
        return fig.show()


    _()
    return


@app.cell
def _(df_smard_generation, pd, plt):
    def _():
        from pathlib import Path

        df_wind = df_smard_generation.copy()

        df_wind["Start date"] = pd.to_datetime(
            df_wind["Start date"]
        )

        # Total wind generation
        df_wind["Wind Total"] = (
            df_wind["Wind Onshore"]
            + df_wind["Wind Offshore"]
        )

        # Q4 2025
        df_q4 = df_wind[
            (df_wind["Start date"] >= "2025-10-01")
            & (df_wind["Start date"] < "2026-01-01")
        ].copy()

        # Daily averages
        daily = (
            df_q4
            .set_index("Start date")
            [
                [
                    "Wind Total",
                    "Wind Onshore",
                    "Wind Offshore",
                ]
            ]
            .resample("D")
            .mean()
            .reset_index()
        )

        dates = daily["Start date"]

        fig_wind_generation_q4, ax = plt.subplots(
            figsize=(7.2, 4.2)
        )

        ax.plot(
            dates,
            daily["Wind Total"],
            label="Total Wind",
            linewidth=1.8,
            color="#636EFA",
        )

        ax.plot(
            dates,
            daily["Wind Onshore"],
            label="Wind Onshore",
            linewidth=1.5,
            color="#EF553B",
        )

        ax.plot(
            dates,
            daily["Wind Offshore"],
            label="Wind Offshore",
            linewidth=1.5,
            color="#00A88F",
        )

        ax.set_title(
            "Daily Average Wind Generation -- Germany, Q4 2025",
            fontsize=10,
            pad=18,
        )

        ax.set_xlabel(
            "Date",
            fontsize=8.5,
            labelpad=8,
        )

        ax.set_ylabel(
            "Average MWh per Hour",
            fontsize=8.5,
            labelpad=8,
        )

        tick_dates = [
            pd.Timestamp("2025-10-05"),
            pd.Timestamp("2025-10-19"),
            pd.Timestamp("2025-11-02"),
            pd.Timestamp("2025-11-16"),
            pd.Timestamp("2025-11-30"),
            pd.Timestamp("2025-12-14"),
            pd.Timestamp("2025-12-28"),
        ]

        tick_labels = [
            "Oct 5",
            "Oct 19",
            "Nov 2",
            "Nov 16",
            "Nov 30",
            "Dec 14",
            "Dec 28",
        ]

        ax.set_xticks(tick_dates)

        ax.set_xticklabels(
            tick_labels,
            rotation=0,
            ha="center",
        )

        ax.set_xlim(
            pd.Timestamp("2025-10-01"),
            pd.Timestamp("2025-12-31"),
        )

        ax.yaxis.grid(
            True,
            color="#D9D9D9",
            linewidth=0.5,
        )

        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.spines["left"].set_color("#BBBBBB")
        ax.spines["bottom"].set_color("#BBBBBB")

        ax.spines["left"].set_linewidth(0.5)
        ax.spines["bottom"].set_linewidth(0.5)

        ax.tick_params(
            axis="both",
            labelsize=7,
            width=0.4,
            length=3,
        )

        ax.legend(
            frameon=False,
            loc="upper left",
            fontsize=7.5,
        )

        fig_wind_generation_q4.subplots_adjust(
            left=0.12,
            right=0.98,
            bottom=0.17,
            top=0.86,
        )

        # Save inside the Git project
        Path("figures").mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pgf = "figures/wind_generation_q4.pgf"
        output_pdf = "figures/wind_generation_q4.pdf"

        fig_wind_generation_q4.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
            pad_inches=0.04,
        )

        fig_wind_generation_q4.savefig(
            output_pdf,
            bbox_inches="tight",
            pad_inches=0.04,
        )

        plt.close(fig_wind_generation_q4)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)

        return daily


    _()
    return


@app.cell
def _(df_smard_generation, go, pd):
    def _():
        df_solar = df_smard_generation.copy()
        df_solar["Start date"] = pd.to_datetime(df_solar["Start date"])

        # Filter Q4
        df_q4 = df_solar[
            (df_solar["Start date"] >= "2025-10-01") &
            (df_solar["Start date"] < "2026-01-01")
        ].copy()

        df_q4["Month"] = df_q4["Start date"].dt.strftime("%b")
        df_q4["Hour"] = df_q4["Start date"].dt.hour

        month_order = ["Oct", "Nov", "Dec"]

        hourly = (
            df_q4
            .groupby(["Month", "Hour"], as_index=False)["Solar"]
            .mean()
        )

        fig = go.Figure()

        colors = {
            "Oct": "#1f77b4",
            "Nov": "#ff7f0e",
            "Dec": "#2ca02c"
        }

        for month in month_order:

            data = hourly[hourly["Month"] == month]

            fig.add_trace(
                go.Scatter(
                    x=data["Hour"],
                    y=data["Solar"],
                    mode="lines+markers",
                    name=month,
                    line=dict(width=3, color=colors[month])
                )
            )

        fig.update_layout(
            title="Average Hourly Solar Profile by Month (Q4 2025)",
            xaxis_title="Hour of Day",
            yaxis_title="Average MWh per Hour",
            template="plotly_white",
            width=1000,
            height=500,
            hovermode="x unified"
        )

        fig.update_xaxes(dtick=2)
        return fig


    _()
    return


@app.cell
def _(df_smard_generation, pd, plt):
    def _():
        from pathlib import Path

        df_solar = df_smard_generation.copy()

        df_solar["Start date"] = pd.to_datetime(
            df_solar["Start date"]
        )

        # Filter Q4
        df_q4 = df_solar[
            (df_solar["Start date"] >= "2025-10-01")
            & (df_solar["Start date"] < "2026-01-01")
        ].copy()

        df_q4["Month"] = (
            df_q4["Start date"].dt.strftime("%b")
        )

        df_q4["Hour"] = (
            df_q4["Start date"].dt.hour
        )

        month_order = ["Oct", "Nov", "Dec"]

        hourly = (
            df_q4
            .groupby(
                ["Month", "Hour"],
                as_index=False,
            )["Solar"]
            .mean()
        )

        colors = {
            "Oct": "#1f77b4",
            "Nov": "#ff7f0e",
            "Dec": "#2ca02c",
        }

        fig, ax = plt.subplots(
            figsize=(7.2, 4.2)
        )

        for month in month_order:
            data = hourly[
                hourly["Month"] == month
            ]

            ax.plot(
                data["Hour"],
                data["Solar"],
                marker="o",
                markersize=3.5,
                linewidth=1.8,
                color=colors[month],
                label=month,
            )

        ax.set_title(
            "Average Hourly Solar Profile -- Q4 2025",
            fontsize=10,
            pad=16,
        )

        ax.set_xlabel(
            "Hour of Day",
            fontsize=8.5,
        )

        ax.set_ylabel(
            "Average MWh per Hour",
            fontsize=8.5,
        )

        ax.set_xticks(range(0, 25, 2))
        ax.set_xlim(0, 23)

        ax.grid(
            axis="y",
            color="#D9D9D9",
            linewidth=0.5,
        )

        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.spines["left"].set_color("#BBBBBB")
        ax.spines["bottom"].set_color("#BBBBBB")

        ax.spines["left"].set_linewidth(0.5)
        ax.spines["bottom"].set_linewidth(0.5)

        ax.tick_params(
            axis="both",
            labelsize=8,
            width=0.4,
            length=3,
        )

        ax.legend(
            frameon=False,
            fontsize=8,
            loc="upper right",
        )

        fig.subplots_adjust(
            left=0.12,
            right=0.98,
            bottom=0.17,
            top=0.88,
        )

        # Save inside the Git project
        Path("figures").mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pgf = (
            "figures/hourly_solar_generation_q4.pgf"
        )

        output_pdf = (
            "figures/hourly_solar_generation_q4.pdf"
        )

        fig.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
            pad_inches=0.04,
        )

        fig.savefig(
            output_pdf,
            bbox_inches="tight",
            pad_inches=0.04,
        )

        plt.close(fig)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)

        return hourly


    _()
    return


@app.cell
def _(df_generation_q4, px):
    def _():
        df_solar_monthly_q4 = df_generation_q4.copy()

        df_solar_monthly_q4["Month"] = (
            df_solar_monthly_q4["Start date"].dt.strftime("%b")
        )

        month_order_q4 = ["Oct", "Nov", "Dec"]

        monthly_solar_q4 = (
            df_solar_monthly_q4
            .groupby("Month")["Solar"]
            .sum()
            .reindex(month_order_q4)
            .reset_index()
        )

        monthly_solar_q4["Generation [TWh]"] = (
            monthly_solar_q4["Solar"] / 1_000_000
        )

        fig_solar_monthly_q4 = px.bar(
            monthly_solar_q4,
            x="Month",
            y="Generation [TWh]",
            text="Generation [TWh]",
            title="Monthly Solar Generation (Q4 2025)",
            color_discrete_sequence=["#F6C85F"],
        )

        fig_solar_monthly_q4.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside",
        )

        fig_solar_monthly_q4.update_layout(
            template="plotly_white",
            width=850,
            height=500,
            xaxis_title="Month",
            yaxis_title="Generation [TWh]",
            showlegend=False,
        )

        fig_solar_monthly_q4.show()
        return monthly_solar_q4[["Month", "Generation [TWh]"]].round(2)


    _()
    return


@app.cell
def _(df_generation_q4, plt):
    def _():
        from pathlib import Path

        df_solar_monthly_q4 = df_generation_q4.copy()

        df_solar_monthly_q4["Month"] = (
            df_solar_monthly_q4["Start date"].dt.strftime("%b")
        )

        month_order_q4 = ["Oct", "Nov", "Dec"]

        monthly_solar_q4 = (
            df_solar_monthly_q4
            .groupby("Month")["Solar"]
            .sum()
            .reindex(month_order_q4)
            .reset_index()
        )

        monthly_solar_q4["Generation [TWh]"] = (
            monthly_solar_q4["Solar"] / 1_000_000
        )

        fig, ax = plt.subplots(figsize=(6.6, 4.2))

        bars = ax.bar(
            monthly_solar_q4["Month"],
            monthly_solar_q4["Generation [TWh]"],
            color="#F6C85F",
            width=0.55,
        )

        # Value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + 0.08,
                f"{height:.2f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

        ax.set_title(
            "Monthly Solar Generation -- Q4 2025",
            fontsize=10,
            pad=16,
        )

        ax.set_xlabel(
            "Month",
            fontsize=8.5,
        )

        ax.set_ylabel(
            "Generation [TWh]",
            fontsize=8.5,
        )

        ax.grid(
            axis="y",
            color="#D9D9D9",
            linewidth=0.5,
        )

        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.spines["left"].set_color("#BBBBBB")
        ax.spines["bottom"].set_color("#BBBBBB")

        ax.spines["left"].set_linewidth(0.5)
        ax.spines["bottom"].set_linewidth(0.5)

        ax.tick_params(
            axis="both",
            labelsize=8,
            width=0.4,
            length=3,
        )

        ax.set_ylim(
            0,
            monthly_solar_q4["Generation [TWh]"].max() * 1.18,
        )

        fig.subplots_adjust(
            left=0.13,
            right=0.97,
            bottom=0.18,
            top=0.88,
        )

        # ============================================================
        # Save PGF and PDF inside the project repository
        # ============================================================

        Path("figures").mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pgf = "figures/solar_generation_q4.pgf"
        output_pdf = "figures/solar_generation_q4.pdf"

        fig.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
            pad_inches=0.04,
        )

        fig.savefig(
            output_pdf,
            bbox_inches="tight",
            pad_inches=0.04,
        )

        plt.close(fig)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)

        return monthly_solar_q4[
            ["Month", "Generation [TWh]"]
        ].round(2)


    _()
    return


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


@app.cell
def _():
    return


@app.cell
def _(df_smard_consumption, df_smard_generation, pd, px, renewable_cols):
    def _():
        # ============================================================
        # Q4 2025: Renewable share of electricity demand
        # ============================================================

        # Merge hourly renewable generation and electricity demand
        df_q4_renewable_share = (
            df_smard_generation[
                ["Start date"] + renewable_cols
            ]
            .merge(
                df_smard_consumption[
                    ["Start date", "Consumption"]
                ],
                on="Start date",
                how="inner",
            )
            .copy()
        )

        # Ensure datetime format
        df_q4_renewable_share["Start date"] = pd.to_datetime(
            df_q4_renewable_share["Start date"]
        )

        # Filter Q4 2025
        df_q4_renewable_share = df_q4_renewable_share[
            (df_q4_renewable_share["Start date"] >= "2025-10-01")
            & (df_q4_renewable_share["Start date"] < "2026-01-01")
        ].copy()

        # Remove invalid demand values
        df_q4_renewable_share = df_q4_renewable_share[
            df_q4_renewable_share["Consumption"] > 0
        ].copy()

        # ------------------------------------------------------------
        # Calculate total hourly renewable generation
        # ------------------------------------------------------------

        df_q4_renewable_share["Renewable Generation [MWh]"] = (
            df_q4_renewable_share[renewable_cols].sum(axis=1)
        )

        # Hourly renewable share of demand
        df_q4_renewable_share["Renewable Share [%]"] = (
            df_q4_renewable_share["Renewable Generation [MWh]"]
            / df_q4_renewable_share["Consumption"]
            * 100
        )

        # Difference between renewable generation and demand
        df_q4_renewable_share["Renewable Balance [MWh]"] = (
            df_q4_renewable_share["Renewable Generation [MWh]"]
            - df_q4_renewable_share["Consumption"]
        )

        # Boolean indicator
        df_q4_renewable_share["Renewables Met Demand"] = (
            df_q4_renewable_share["Renewable Share [%]"] >= 100
        )

        # ------------------------------------------------------------
        # Q4 summary statistics
        # ------------------------------------------------------------

        total_hours_q4 = len(df_q4_renewable_share)

        hours_renewables_met_demand = int(
            df_q4_renewable_share["Renewables Met Demand"].sum()
        )

        percentage_hours_met = (
            hours_renewables_met_demand
            / total_hours_q4
            * 100
        )

        total_renewable_q4_twh = (
            df_q4_renewable_share["Renewable Generation [MWh]"].sum()
            / 1_000_000
        )

        total_demand_q4_twh = (
            df_q4_renewable_share["Consumption"].sum()
            / 1_000_000
        )

        # Energy-weighted renewable share for the whole quarter
        renewable_share_q4_percent = (
            total_renewable_q4_twh
            / total_demand_q4_twh
            * 100
        )

        maximum_hourly_share = (
            df_q4_renewable_share["Renewable Share [%]"].max()
        )

        minimum_hourly_share = (
            df_q4_renewable_share["Renewable Share [%]"].min()
        )

        print("Q4 2025 RENEWABLE SHARE OF DEMAND")
        print("----------------------------------")
        print(f"Total Q4 hours analysed: {total_hours_q4:,}")
        print(
            "Hours when renewables met or exceeded demand: "
            f"{hours_renewables_met_demand:,}"
        )
        print(
            "Share of Q4 hours when renewables met demand: "
            f"{percentage_hours_met:.2f}%"
        )
        print(
            f"Total renewable generation: "
            f"{total_renewable_q4_twh:.2f} TWh"
        )
        print(
            f"Total electricity demand: "
            f"{total_demand_q4_twh:.2f} TWh"
        )
        print(
            f"Renewable share of Q4 demand: "
            f"{renewable_share_q4_percent:.2f}%"
        )
        print(
            f"Maximum hourly renewable share: "
            f"{maximum_hourly_share:.1f}%"
        )
        print(
            f"Minimum hourly renewable share: "
            f"{minimum_hourly_share:.1f}%"
        )

        # ------------------------------------------------------------
        # Identify dominant renewable source in every hour
        # ------------------------------------------------------------

        df_q4_renewable_share["Dominant Renewable Source"] = (
            df_q4_renewable_share[renewable_cols].idxmax(axis=1)
        )

        # ------------------------------------------------------------
        # Five highest renewable-share hours
        # ------------------------------------------------------------

        df_top_renewable_hours_q4 = (
            df_q4_renewable_share
            .nlargest(5, "Renewable Share [%]")
            [
                [
                    "Start date",
                    "Consumption",
                    "Renewable Generation [MWh]",
                    "Renewable Share [%]",
                    "Renewable Balance [MWh]",
                    "Dominant Renewable Source",
                ]
            ]
            .copy()
        )

        df_top_renewable_hours_q4 = (
            df_top_renewable_hours_q4.rename(
                columns={
                    "Start date": "Hour",
                    "Consumption": "Load [MWh]",
                    "Dominant Renewable Source": "Main Driver",
                }
            )
        )

        df_top_renewable_hours_q4["Hour"] = (
            df_top_renewable_hours_q4["Hour"]
            .dt.strftime("%d %b %Y, %H:%M")
        )

        numeric_columns = [
            "Load [MWh]",
            "Renewable Generation [MWh]",
            "Renewable Share [%]",
            "Renewable Balance [MWh]",
        ]

        df_top_renewable_hours_q4[numeric_columns] = (
            df_top_renewable_hours_q4[numeric_columns].round(1)
        )

        print("\nFIVE HIGHEST RENEWABLE-SHARE HOURS")
        print("----------------------------------")
        print(df_top_renewable_hours_q4.to_string(index=False))

        # ------------------------------------------------------------
        # Daily average renewable share
        # ------------------------------------------------------------

        df_daily_renewable_share_q4 = (
            df_q4_renewable_share
            .set_index("Start date")
            .resample("D")
            .agg(
                Daily_Renewable_Generation_MWh=(
                    "Renewable Generation [MWh]",
                    "sum",
                ),
                Daily_Demand_MWh=(
                    "Consumption",
                    "sum",
                ),
            )
            .reset_index()
        )

        # Calculate daily share from daily energy totals
        df_daily_renewable_share_q4[
            "Daily Renewable Share [%]"
        ] = (
            df_daily_renewable_share_q4[
                "Daily_Renewable_Generation_MWh"
            ]
            / df_daily_renewable_share_q4["Daily_Demand_MWh"]
            * 100
        )

        # ------------------------------------------------------------
        # Plot daily renewable share
        # ------------------------------------------------------------

        fig_q4_renewable_share = px.line(
            df_daily_renewable_share_q4,
            x="Start date",
            y="Daily Renewable Share [%]",
            title="Daily Renewable Share of Electricity Demand — Germany, Q4 2025",
            markers=False,
        )

        fig_q4_renewable_share.add_hline(
            y=100,
            line_dash="dash",
            line_color="black",
            line_width=1.2,
            annotation_text="100% of daily demand",
            annotation_position="top left",
        )

        fig_q4_renewable_share.update_traces(
            line=dict(
                width=2.2,
                color="#2A9D8F",
            ),
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b><br>"
                "Renewable share: %{y:.1f}%"
                "<extra></extra>"
            ),
        )

        y_axis_maximum = max(
            110,
            df_daily_renewable_share_q4[
                "Daily Renewable Share [%]"
            ].max() * 1.10,
        )

        fig_q4_renewable_share.update_layout(
            template="plotly_white",
            width=1000,
            height=500,
            title=dict(
                x=0.5,
                xanchor="center",
                font=dict(size=18),
            ),
            xaxis_title="Date",
            yaxis_title="Renewable Share of Demand [%]",
            yaxis=dict(
                range=[0, y_axis_maximum],
                gridcolor="lightgray",
                zeroline=False,
            ),
            xaxis=dict(
                showgrid=False,
            ),
            margin=dict(
                l=80,
                r=40,
                t=90,
                b=70,
            ),
        )
        return fig_q4_renewable_share.show()


    _()
    return


@app.cell
def _(df_smard_consumption, df_smard_generation, pd, px, renewable_cols):
    def _():
        # ============================================================
        # Q4 2025: Renewable share of electricity demand
        # ============================================================

        df_q4_renewable_share = (
            df_smard_generation[
                ["Start date"] + renewable_cols
            ]
            .merge(
                df_smard_consumption[
                    ["Start date", "Consumption"]
                ],
                on="Start date",
                how="inner",
            )
            .copy()
        )

        df_q4_renewable_share["Start date"] = pd.to_datetime(
            df_q4_renewable_share["Start date"]
        )

        # Filter Q4 2025
        df_q4_renewable_share = df_q4_renewable_share[
            (df_q4_renewable_share["Start date"] >= "2025-10-01")
            & (df_q4_renewable_share["Start date"] < "2026-01-01")
        ].copy()

        # Remove invalid demand values
        df_q4_renewable_share = df_q4_renewable_share[
            df_q4_renewable_share["Consumption"] > 0
        ].copy()

        # ============================================================
        # Hourly renewable metrics
        # ============================================================

        df_q4_renewable_share["Renewable Generation [MWh]"] = (
            df_q4_renewable_share[renewable_cols].sum(axis=1)
        )

        df_q4_renewable_share["Renewable Share [%]"] = (
            df_q4_renewable_share["Renewable Generation [MWh]"]
            / df_q4_renewable_share["Consumption"]
            * 100
        )

        df_q4_renewable_share["Renewable Balance [MWh]"] = (
            df_q4_renewable_share["Renewable Generation [MWh]"]
            - df_q4_renewable_share["Consumption"]
        )

        df_q4_renewable_share["Renewables Met Demand"] = (
            df_q4_renewable_share["Renewable Share [%]"] >= 100
        )

        df_q4_renewable_share["Dominant Renewable Source"] = (
            df_q4_renewable_share[renewable_cols].idxmax(axis=1)
        )

        # ============================================================
        # Summary statistics
        # ============================================================

        total_hours_q4 = len(df_q4_renewable_share)

        hours_renewables_met_demand = int(
            df_q4_renewable_share["Renewables Met Demand"].sum()
        )

        percentage_hours_met = (
            hours_renewables_met_demand
            / total_hours_q4
            * 100
        )

        total_renewable_q4_twh = (
            df_q4_renewable_share[
                "Renewable Generation [MWh]"
            ].sum()
            / 1_000_000
        )

        total_demand_q4_twh = (
            df_q4_renewable_share["Consumption"].sum()
            / 1_000_000
        )

        renewable_share_q4_percent = (
            total_renewable_q4_twh
            / total_demand_q4_twh
            * 100
        )

        maximum_hourly_share = (
            df_q4_renewable_share["Renewable Share [%]"].max()
        )

        minimum_hourly_share = (
            df_q4_renewable_share["Renewable Share [%]"].min()
        )

        print("Q4 2025 RENEWABLE SHARE OF DEMAND")
        print("----------------------------------")
        print(f"Total Q4 hours analysed: {total_hours_q4:,}")
        print(
            "Hours when renewables met or exceeded demand: "
            f"{hours_renewables_met_demand:,}"
        )
        print(
            "Share of Q4 hours when renewables met demand: "
            f"{percentage_hours_met:.2f}%"
        )
        print(
            f"Total renewable generation: "
            f"{total_renewable_q4_twh:.2f} TWh"
        )
        print(
            f"Total electricity demand: "
            f"{total_demand_q4_twh:.2f} TWh"
        )
        print(
            f"Renewable share of Q4 demand: "
            f"{renewable_share_q4_percent:.2f}%"
        )
        print(
            f"Maximum hourly renewable share: "
            f"{maximum_hourly_share:.1f}%"
        )
        print(
            f"Minimum hourly renewable share: "
            f"{minimum_hourly_share:.1f}%"
        )

        # ============================================================
        # Five highest renewable-share hours
        # ============================================================

        df_top_renewable_hours_q4 = (
            df_q4_renewable_share
            .nlargest(5, "Renewable Share [%]")
            [
                [
                    "Start date",
                    "Consumption",
                    "Renewable Generation [MWh]",
                    "Renewable Share [%]",
                    "Renewable Balance [MWh]",
                    "Dominant Renewable Source",
                ]
            ]
            .copy()
        )

        df_top_renewable_hours_q4 = (
            df_top_renewable_hours_q4.rename(
                columns={
                    "Start date": "Hour",
                    "Consumption": "Load [MWh]",
                    "Dominant Renewable Source": "Main Driver",
                }
            )
        )

        df_top_renewable_hours_q4["Hour"] = (
            df_top_renewable_hours_q4["Hour"]
            .dt.strftime("%d %b %Y, %H:%M")
        )

        numeric_columns = [
            "Load [MWh]",
            "Renewable Generation [MWh]",
            "Renewable Share [%]",
            "Renewable Balance [MWh]",
        ]

        df_top_renewable_hours_q4[numeric_columns] = (
            df_top_renewable_hours_q4[numeric_columns]
            .round(1)
        )

        print("\nFIVE HIGHEST RENEWABLE-SHARE HOURS")
        print("----------------------------------")
        print(df_top_renewable_hours_q4.to_string(index=False))

        # ============================================================
        # Daily renewable share
        # ============================================================

        df_daily_renewable_share_q4 = (
            df_q4_renewable_share
            .set_index("Start date")
            .resample("D")
            .agg(
                Daily_Renewable_Generation_MWh=(
                    "Renewable Generation [MWh]",
                    "sum",
                ),
                Daily_Demand_MWh=(
                    "Consumption",
                    "sum",
                ),
            )
            .reset_index()
        )

        df_daily_renewable_share_q4[
            "Daily Renewable Share [%]"
        ] = (
            df_daily_renewable_share_q4[
                "Daily_Renewable_Generation_MWh"
            ]
            / df_daily_renewable_share_q4[
                "Daily_Demand_MWh"
            ]
            * 100
        )

        # ============================================================
        # Interactive Plotly figure
        # ============================================================

        fig_q4_renewable_share = px.line(
            df_daily_renewable_share_q4,
            x="Start date",
            y="Daily Renewable Share [%]",
            title=(
                "Daily Renewable Share of Electricity Demand "
                "— Germany, Q4 2025"
            ),
        )

        fig_q4_renewable_share.add_hline(
            y=100,
            line_dash="dash",
            line_color="black",
            line_width=1.2,
            annotation_text="100% of daily demand",
            annotation_position="top left",
        )

        fig_q4_renewable_share.update_traces(
            line=dict(
                width=2.2,
                color="#2A9D8F",
            )
        )

        y_axis_maximum = max(
            110,
            df_daily_renewable_share_q4[
                "Daily Renewable Share [%]"
            ].max() * 1.10,
        )

        fig_q4_renewable_share.update_layout(
            template="plotly_white",
            width=1000,
            height=500,
            title=dict(
                x=0.5,
                xanchor="center",
                font=dict(size=18),
            ),
            xaxis_title="Date",
            yaxis_title="Renewable Share of Demand [%]",
            yaxis=dict(
                range=[0, y_axis_maximum],
                gridcolor="lightgray",
                zeroline=False,
            ),
            xaxis=dict(
                showgrid=False,
            ),
            margin=dict(
                l=80,
                r=40,
                t=90,
                b=70,
            ),
        )

        fig_q4_renewable_share.show()

        return (
            df_q4_renewable_share,
            df_daily_renewable_share_q4,
            df_top_renewable_hours_q4,
            fig_q4_renewable_share,
        )


    (
        df_q4_renewable_share,
        df_daily_renewable_share_q4,
        df_top_renewable_hours_q4,
        fig_q4_renewable_share,
    ) = _()
    return (df_daily_renewable_share_q4,)


@app.cell
def _(df_daily_renewable_share_q4, np, pd, plt):
    def _():
        from pathlib import Path

        daily_share = df_daily_renewable_share_q4[
            "Daily Renewable Share [%]"
        ]

        dates = df_daily_renewable_share_q4["Start date"]

        y_axis_maximum = max(
            120,
            daily_share.max() * 1.08,
        )

        fig_daily_renewable_share_q4, ax = plt.subplots(
            figsize=(7.2, 4.2)
        )

        # ============================================================
        # Daily renewable-share line
        # ============================================================

        ax.plot(
            dates,
            daily_share,
            color="#2A9D8F",
            linewidth=1.6,
        )

        # ============================================================
        # 100% reference line
        # ============================================================

        ax.axhline(
            y=100,
            color="#333333",
            linestyle=(0, (5, 5)),
            linewidth=0.9,
        )

        ax.text(
            pd.Timestamp("2025-10-02"),
            101.2,
            r"100\% of daily demand",
            ha="left",
            va="bottom",
            fontsize=7,
            color="#333333",
        )

        # ============================================================
        # Title and axis labels
        # ============================================================

        ax.set_title(
            "Daily Renewable Share of Electricity Demand -- Germany, Q4 2025",
            fontsize=10,
            pad=18,
        )

        ax.set_xlabel(
            "Date",
            fontsize=8.5,
            labelpad=8,
        )

        ax.set_ylabel(
            r"Renewable Share of Demand [\%]",
            fontsize=8.5,
            labelpad=8,
        )

        # ============================================================
        # X-axis ticks
        # ============================================================

        tick_dates = [
            pd.Timestamp("2025-10-05"),
            pd.Timestamp("2025-10-19"),
            pd.Timestamp("2025-11-02"),
            pd.Timestamp("2025-11-16"),
            pd.Timestamp("2025-11-30"),
            pd.Timestamp("2025-12-14"),
            pd.Timestamp("2025-12-28"),
        ]

        tick_labels = [
            "Oct 5",
            "Oct 19",
            "Nov 2",
            "Nov 16",
            "Nov 30",
            "Dec 14",
            "Dec 28",
        ]

        ax.set_xticks(tick_dates)

        ax.set_xticklabels(
            tick_labels,
            rotation=0,
            ha="center",
        )

        ax.set_xlim(
            pd.Timestamp("2025-10-01"),
            pd.Timestamp("2025-12-31"),
        )

        # ============================================================
        # Y-axis
        # ============================================================

        ax.set_ylim(
            0,
            y_axis_maximum,
        )

        ax.set_yticks(
            np.arange(
                0,
                y_axis_maximum + 1,
                20,
            )
        )

        # ============================================================
        # Styling
        # ============================================================

        ax.yaxis.grid(
            True,
            color="#D9D9D9",
            linewidth=0.5,
        )

        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.spines["left"].set_color("#BBBBBB")
        ax.spines["bottom"].set_color("#BBBBBB")

        ax.spines["left"].set_linewidth(0.5)
        ax.spines["bottom"].set_linewidth(0.5)

        ax.tick_params(
            axis="both",
            labelsize=7,
            width=0.4,
            length=3,
        )

        fig_daily_renewable_share_q4.subplots_adjust(
            left=0.12,
            right=0.98,
            bottom=0.17,
            top=0.86,
        )

        # ============================================================
        # Save PGF and PDF inside the project repository
        # ============================================================

        Path("figures").mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pgf = "figures/daily_renewable_share_q4.pgf"
        output_pdf = "figures/daily_renewable_share_q4.pdf"

        fig_daily_renewable_share_q4.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
            pad_inches=0.04,
        )

        fig_daily_renewable_share_q4.savefig(
            output_pdf,
            bbox_inches="tight",
            pad_inches=0.04,
        )

        plt.close(fig_daily_renewable_share_q4)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)

        return df_daily_renewable_share_q4


    _()
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
    def _():
        # ============================================================
        # Q4 2025: Residual load and import exposure
        # ============================================================

        # Merge generation and demand data
        df_q4_residual = (
            df_smard_generation.copy()
            .merge(
                df_smard_consumption[
                    ["Start date", "Consumption"]
                ],
                on="Start date",
                how="inner",
            )
        )

        # Ensure datetime format
        df_q4_residual["Start date"] = pd.to_datetime(
            df_q4_residual["Start date"]
        )

        # Filter Q4 2025
        df_q4_residual = df_q4_residual[
            (df_q4_residual["Start date"] >= "2025-10-01")
            & (df_q4_residual["Start date"] < "2026-01-01")
        ].copy()

        # Remove invalid demand observations
        df_q4_residual = df_q4_residual[
            df_q4_residual["Consumption"] > 0
        ].copy()

        # ============================================================
        # Calculate generation metrics
        # ============================================================

        df_q4_residual["Renewable Generation"] = (
            df_q4_residual[renewable_cols].sum(axis=1)
        )

        df_q4_residual["Conventional Generation"] = (
            df_q4_residual[conventional_cols].sum(axis=1)
        )

        df_q4_residual["Domestic Generation"] = (
            df_q4_residual["Renewable Generation"]
            + df_q4_residual["Conventional Generation"]
        )

        # Residual load:
        # electricity demand remaining after renewable generation
        df_q4_residual["Residual Load"] = (
            df_q4_residual["Consumption"]
            - df_q4_residual["Renewable Generation"]
        )

        # Net-trade proxy:
        # positive = domestic generation exceeds demand
        # negative = domestic generation is below demand
        df_q4_residual["Net Trade Proxy"] = (
            df_q4_residual["Domestic Generation"]
            - df_q4_residual["Consumption"]
        )

        # Total wind generation
        wind_columns = [
            col for col in renewable_cols
            if "wind" in col.lower()
        ]

        df_q4_residual["Wind Generation"] = (
            df_q4_residual[wind_columns].sum(axis=1)
        )

        # ============================================================
        # Summary statistics
        # ============================================================

        average_residual_load = (
            df_q4_residual["Residual Load"].mean()
        )

        maximum_residual_load = (
            df_q4_residual["Residual Load"].max()
        )

        minimum_residual_load = (
            df_q4_residual["Residual Load"].min()
        )

        net_import_hours = int(
            (df_q4_residual["Net Trade Proxy"] < 0).sum()
        )

        net_export_hours = int(
            (df_q4_residual["Net Trade Proxy"] > 0).sum()
        )

        balanced_hours = int(
            (df_q4_residual["Net Trade Proxy"] == 0).sum()
        )

        total_hours = len(df_q4_residual)

        print("Q4 2025 RESIDUAL LOAD AND IMPORT EXPOSURE")
        print("-----------------------------------------")
        print(
            f"Average residual load: "
            f"{average_residual_load:,.0f} MWh/h"
        )
        print(
            f"Maximum residual load: "
            f"{maximum_residual_load:,.0f} MWh/h"
        )
        print(
            f"Minimum residual load: "
            f"{minimum_residual_load:,.0f} MWh/h"
        )
        print(
            f"Net-import proxy hours: "
            f"{net_import_hours:,}"
        )
        print(
            f"Net-export proxy hours: "
            f"{net_export_hours:,}"
        )
        print(
            f"Balanced hours: "
            f"{balanced_hours:,}"
        )
        print(
            f"Total hours analysed: "
            f"{total_hours:,}"
        )

        # ============================================================
        # Five highest residual-load hours
        # ============================================================

        df_high_residual_q4 = (
            df_q4_residual
            .nlargest(5, "Residual Load")
            [
                [
                    "Start date",
                    "Consumption",
                    "Renewable Generation",
                    "Residual Load",
                    "Wind Generation",
                    "Net Trade Proxy",
                ]
            ]
            .copy()
        )

        df_high_residual_q4 = df_high_residual_q4.rename(
            columns={
                "Start date": "Hour",
                "Consumption": "Load [MWh]",
                "Renewable Generation": "Renewables [MWh]",
                "Residual Load": "Residual Load [MWh]",
                "Wind Generation": "Wind [MWh]",
                "Net Trade Proxy": "Net Trade Proxy [MWh]",
            }
        )

        # Format hour
        df_high_residual_q4["Hour"] = (
            df_high_residual_q4["Hour"]
            .dt.strftime("%d %b %Y, %H:%M")
        )

        # Round numerical columns
        numerical_columns = [
            "Load [MWh]",
            "Renewables [MWh]",
            "Residual Load [MWh]",
            "Wind [MWh]",
            "Net Trade Proxy [MWh]",
        ]

        df_high_residual_q4[numerical_columns] = (
            df_high_residual_q4[numerical_columns]
            .round(0)
            .astype(int)
        )

        print("\nFIVE HIGHEST RESIDUAL-LOAD HOURS")
        print("--------------------------------")
        print(df_high_residual_q4.to_string(index=False))

        # ============================================================
        # Daily-average data for the figure
        # ============================================================

        df_daily_residual_q4 = (
            df_q4_residual
            .set_index("Start date")
            [
                [
                    "Residual Load",
                    "Net Trade Proxy",
                ]
            ]
            .resample("D")
            .mean()
            .reset_index()
        )

        # Convert to long format for Plotly
        df_daily_residual_long_q4 = (
            df_daily_residual_q4.melt(
                id_vars="Start date",
                value_vars=[
                    "Residual Load",
                    "Net Trade Proxy",
                ],
                var_name="Metric",
                value_name="Average MWh per Hour",
            )
        )

        # ============================================================
        # Plot
        # ============================================================

        fig_residual_q4 = px.line(
            df_daily_residual_long_q4,
            x="Start date",
            y="Average MWh per Hour",
            color="Metric",
            title=(
                "Residual Load and Net-Trade Proxy — "
                "Germany, Q4 2025"
            ),
            color_discrete_map={
                "Residual Load": "#75617D",
                "Net Trade Proxy": "#345B6D",
            },
        )

        fig_residual_q4.add_hline(
            y=0,
            line_dash="dot",
            line_color="black",
            line_width=1,
        )

        fig_residual_q4.update_traces(
            line=dict(width=2),
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b><br>"
                "%{fullData.name}: %{y:,.0f} MWh/h"
                "<extra></extra>"
            ),
        )

        fig_residual_q4.update_layout(
            template="plotly_white",
            width=1000,
            height=500,

            title=dict(
                x=0.5,
                xanchor="center",
                font=dict(size=18),
            ),

            xaxis_title="Date",
            yaxis_title="Average MWh per Hour",

            legend=dict(
                title="",
                orientation="v",
                x=1.01,
                y=1,
            ),

            xaxis=dict(
                showgrid=False,
            ),

            yaxis=dict(
                gridcolor="lightgray",
                zeroline=False,
            ),

            margin=dict(
                l=85,
                r=150,
                t=90,
                b=70,
            ),
        )

        fig_residual_q4.show()

        return (
            df_q4_residual,
            df_daily_residual_q4,
            df_high_residual_q4,
            fig_residual_q4,
        )


    (
        df_q4_residual,
        df_daily_residual_q4,
        df_high_residual_q4,
        fig_residual_q4,
    ) = _()
    return (df_daily_residual_q4,)


@app.cell
def _(df_daily_residual_q4, pd, plt):
    def _():
        from pathlib import Path

        dates = df_daily_residual_q4["Start date"]

        fig_residual_q4_pgf, ax = plt.subplots(
            figsize=(7.2, 4.2)
        )

        # Residual-load line
        ax.plot(
            dates,
            df_daily_residual_q4["Residual Load"],
            label="Residual Load",
            linewidth=1.6,
            color="#75617D",
        )

        # Net-trade proxy line
        ax.plot(
            dates,
            df_daily_residual_q4["Net Trade Proxy"],
            label="Net-Trade Proxy",
            linewidth=1.6,
            color="#345B6D",
        )

        # Zero-reference line
        ax.axhline(
            y=0,
            color="#333333",
            linestyle=(0, (5, 5)),
            linewidth=0.9,
        )

        # Title and axis labels
        ax.set_title(
            "Residual Load and Net-Trade Proxy -- Germany, Q4 2025",
            fontsize=10,
            pad=18,
        )

        ax.set_xlabel(
            "Date",
            fontsize=8.5,
            labelpad=8,
        )

        ax.set_ylabel(
            "Average energy per hour [MWh/h]",
            fontsize=8.5,
            labelpad=8,
        )

        # X-axis ticks
        tick_dates = [
            pd.Timestamp("2025-10-05"),
            pd.Timestamp("2025-10-19"),
            pd.Timestamp("2025-11-02"),
            pd.Timestamp("2025-11-16"),
            pd.Timestamp("2025-11-30"),
            pd.Timestamp("2025-12-14"),
            pd.Timestamp("2025-12-28"),
        ]

        tick_labels = [
            "Oct 5",
            "Oct 19",
            "Nov 2",
            "Nov 16",
            "Nov 30",
            "Dec 14",
            "Dec 28",
        ]

        ax.set_xticks(tick_dates)

        ax.set_xticklabels(
            tick_labels,
            rotation=0,
            ha="center",
        )

        ax.set_xlim(
            pd.Timestamp("2025-10-01"),
            pd.Timestamp("2025-12-31"),
        )

        # Horizontal grid only
        ax.yaxis.grid(
            True,
            color="#D9D9D9",
            linewidth=0.5,
        )

        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        # Clean borders
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.spines["left"].set_color("#BBBBBB")
        ax.spines["bottom"].set_color("#BBBBBB")

        ax.spines["left"].set_linewidth(0.5)
        ax.spines["bottom"].set_linewidth(0.5)

        ax.tick_params(
            axis="both",
            labelsize=7,
            width=0.4,
            length=3,
        )

        # Legend
        ax.legend(
            frameon=False,
            loc="upper right",
            fontsize=7.5,
        )

        fig_residual_q4_pgf.subplots_adjust(
            left=0.12,
            right=0.98,
            bottom=0.17,
            top=0.86,
        )

        # ============================================================
        # Save PGF and PDF inside the project repository
        # ============================================================

        Path("figures").mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pgf = "figures/residual_load_net_proxy.pgf"
        output_pdf = "figures/residual_load_net_proxy.pdf"

        fig_residual_q4_pgf.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
            pad_inches=0.04,
        )

        fig_residual_q4_pgf.savefig(
            output_pdf,
            bbox_inches="tight",
            pad_inches=0.04,
        )

        plt.close(fig_residual_q4_pgf)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)

        return df_daily_residual_q4


    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Monthly Electricity Generation by Energy Source
    """)
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


    plt.savefig(
        "monthly_trade.png",
        dpi=300,
        bbox_inches="tight"
    )



    plt.show()

    monthly_check
    return (month_order,)


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
    plt.savefig(
        "country_trade.png",
        dpi=300,
        bbox_inches="tight"
    )



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
    return (storage_efficiency,)


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
def _(Path, create_engine, inspect):
    database_path = (
        Path(__file__).resolve().parent
        / "data"
        / "mastr_storage_aggregated.db"
    )

    if not database_path.exists():
        raise FileNotFoundError(
            f"Database not found: {database_path}"
        )

    mastr_engine = create_engine(
        f"sqlite:///{database_path.as_posix()}"
    )

    mastr_inspector = inspect(mastr_engine)
    mastr_table_names = mastr_inspector.get_table_names()

    mastr_table_names
    return (mastr_engine,)


@app.cell
def _(mastr_engine, pd):
    df_battery_summary = pd.read_sql_table(
        "battery_summary",
        con=mastr_engine
    )

    df_battery_summary
    return


@app.cell
def _(mastr_engine, pd, px):
    def _():
        df_battery_by_state = pd.read_sql_table(
            "battery_by_state",
            con=mastr_engine
        )

        df_battery_by_state = (
            df_battery_by_state
            .sort_values(
                "Total_Capacity_GWh",
                ascending=False
            )
            .reset_index(drop=True)
        )

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

        fig_state.update_traces(
            texttemplate="%{text} systems",
            textposition="outside"
        )

        fig_state.update_layout(
            height=500,
            coloraxis_showscale=False,
            xaxis_tickangle=-45
        )

        fig_state.show()
        return df_battery_by_state


    _()
    return


@app.cell
def _(Path, mastr_engine, np, pd):
    def save_battery_state_figure(pd, mastr_engine, np, Path):
        import matplotlib as mpl
        import matplotlib.pyplot as local_plt

        # ------------------------------------------------------------
        # PGF / LaTeX configuration
        # ------------------------------------------------------------
        mpl.rcParams.update({
            "pgf.texsystem": "pdflatex",
            "font.family": "serif",
            "text.usetex": True,
            "pgf.rcfonts": False,
            "axes.unicode_minus": False,

            "pgf.preamble": "\n".join([
                r"\usepackage[utf8]{inputenc}",
                r"\usepackage[T1]{fontenc}",
                r"\usepackage{lmodern}",
                r"\providecommand{\mathdefault}[1]{#1}",
            ]),

            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 8.5,
        })

        # ------------------------------------------------------------
        # Read directly from the small database
        # ------------------------------------------------------------
        state_data = pd.read_sql_table(
            "battery_by_state",
            con=mastr_engine,
        )

        state_data = (
            state_data[
                [
                    "Bundesland",
                    "Total_Capacity_GWh",
                    "Total_Systems",
                ]
            ]
            .dropna(
                subset=[
                    "Bundesland",
                    "Total_Capacity_GWh",
                ]
            )
            .sort_values(
                "Total_Capacity_GWh",
                ascending=False,
            )
            .reset_index(drop=True)
            .copy()
        )

        if state_data.empty:
            raise ValueError(
                "The battery_by_state table contains no usable data."
            )

        states = state_data["Bundesland"].tolist()

        capacities = (
            state_data["Total_Capacity_GWh"]
            .astype(float)
            .to_numpy()
        )

        systems = (
            state_data["Total_Systems"]
            .astype(int)
            .to_numpy()
        )

        x_positions = np.arange(len(state_data))

        bar_colors = local_plt.cm.Blues(
            np.linspace(
                0.95,
                0.15,
                len(state_data),
            )
        )

        # ------------------------------------------------------------
        # Create figure
        # ------------------------------------------------------------
        figure, axis = local_plt.subplots(
            figsize=(7.9, 4.8)
        )

        bars = axis.bar(
            x_positions,
            capacities,
            width=0.82,
            color=bar_colors,
            edgecolor="none",
        )

        label_offset = capacities.max() * 0.018

        for bar, system_count in zip(bars, systems):
            height = bar.get_height()

            axis.text(
                bar.get_x() + bar.get_width() / 2,
                height + label_offset,
                f"{system_count:,} systems",
                ha="center",
                va="bottom",
                fontsize=4.8,
            )

        # ------------------------------------------------------------
        # Titles and axes
        # ------------------------------------------------------------
        axis.set_title(
            "Battery Storage Capacity by Federal State -- Germany (MaStR)",
            pad=12,
        )

        axis.set_xlabel(
            "Federal State",
            labelpad=8,
        )

        axis.set_ylabel(
            "Total Battery Capacity [GWh]"
        )

        axis.set_xticks(x_positions)

        axis.set_xticklabels(
            states,
            rotation=45,
            ha="right",
            rotation_mode="anchor",
        )

        axis.set_ylim(
            0,
            capacities.max() * 1.18,
        )

        # ------------------------------------------------------------
        # Styling
        # ------------------------------------------------------------
        axis.yaxis.grid(
            True,
            linewidth=0.45,
            alpha=0.35,
        )

        axis.set_axisbelow(True)

        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_linewidth(0.6)
        axis.spines["bottom"].set_linewidth(0.6)

        axis.tick_params(
            axis="both",
            width=0.6,
        )

        axis.margins(x=0.01)

        figure.tight_layout()

        # ------------------------------------------------------------
        # Save inside the Git repository
        # ------------------------------------------------------------
        figures_directory = (
            Path(__file__).resolve().parent
            / "figures"
        )

        figures_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        pgf_file = (
            figures_directory
            / "battery_capacity_by_state.pgf"
        )

        pdf_file = (
            figures_directory
            / "battery_capacity_by_state.pdf"
        )

        figure.savefig(
            pgf_file,
            backend="pgf",
            bbox_inches="tight",
        )

        figure.savefig(
            pdf_file,
            bbox_inches="tight",
        )

        local_plt.close(figure)

        print(f"PGF saved: {pgf_file}")
        print(f"PDF saved: {pdf_file}")

        return pgf_file, pdf_file


    saved_state_figure_files = save_battery_state_figure(
        pd=pd,
        mastr_engine=mastr_engine,
        np=np,
        Path=Path,
    )

    saved_state_figure_files
    return


@app.cell
def _(mastr_engine, np, pd):
    def export_battery_state_figure(
        pd_module,
        np_module,
        database_engine,
    ):
        import matplotlib as mpl
        import matplotlib.pyplot as local_plt
        from pathlib import Path as LocalPath

        # ------------------------------------------------------------
        # Portable Matplotlib configuration
        # ------------------------------------------------------------
        mpl.rcParams.update({
            "font.family": "serif",
            "text.usetex": False,
            "axes.unicode_minus": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 8.5,
        })

        # ------------------------------------------------------------
        # Read directly from the small aggregated database
        # ------------------------------------------------------------
        state_data = pd_module.read_sql_table(
            "battery_by_state",
            con=database_engine,
        )

        state_data = (
            state_data[
                [
                    "Bundesland",
                    "Total_Capacity_GWh",
                    "Total_Systems",
                ]
            ]
            .dropna(
                subset=[
                    "Bundesland",
                    "Total_Capacity_GWh",
                ]
            )
            .sort_values(
                "Total_Capacity_GWh",
                ascending=False,
            )
            .reset_index(drop=True)
            .copy()
        )

        if state_data.empty:
            raise ValueError(
                "No usable data was found in the battery_by_state table."
            )

        state_label_map = {
            "Nordrhein-Westfalen": "North Rhine-\nWestphalia",
            "Baden-Württemberg": "Baden-\nWürttemberg",
            "Rheinland-Pfalz": "Rhineland-\nPalatinate",
            "Schleswig-Holstein": "Schleswig-\nHolstein",
            "Sachsen-Anhalt": "Saxony-\nAnhalt",
            "Mecklenburg-Vorpommern": "Mecklenburg-\nVorpommern",
        }

        state_data["State_Label"] = (
            state_data["Bundesland"]
            .replace(state_label_map)
        )

        states = state_data["State_Label"].tolist()

        capacities = (
            state_data["Total_Capacity_GWh"]
            .astype(float)
            .to_numpy()
        )

        systems = (
            state_data["Total_Systems"]
            .astype(int)
            .to_numpy()
        )

        x_positions = np_module.arange(len(state_data))

        bar_colors = local_plt.cm.Blues(
            np_module.linspace(
                0.95,
                0.25,
                len(state_data),
            )
        )

        # ------------------------------------------------------------
        # Create figure
        # ------------------------------------------------------------
        figure, axis = local_plt.subplots(
            figsize=(9.2, 5.1)
        )

        bars = axis.bar(
            x_positions,
            capacities,
            width=0.76,
            color=bar_colors,
            edgecolor="white",
            linewidth=0.35,
        )

        maximum_capacity = capacities.max()

        for bar, capacity, system_count in zip(
            bars,
            capacities,
            systems,
        ):
            x_position = (
                bar.get_x()
                + bar.get_width() / 2
            )

            if capacity >= 1.0:
                axis.text(
                    x_position,
                    capacity - maximum_capacity * 0.055,
                    f"{system_count:,}",
                    ha="center",
                    va="top",
                    rotation=90,
                    fontsize=5.8,
                    color="white",
                )
            else:
                axis.text(
                    x_position,
                    capacity + maximum_capacity * 0.025,
                    f"{system_count:,}",
                    ha="center",
                    va="bottom",
                    rotation=90,
                    fontsize=5.4,
                    color="black",
                )

        axis.text(
            0.995,
            0.97,
            "Bar labels indicate number of systems",
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=7,
        )

        axis.set_title(
            "Battery Storage Capacity by Federal State -- Germany (MaStR)",
            pad=14,
        )

        axis.set_xlabel(
            "Federal State",
            labelpad=12,
        )

        axis.set_ylabel(
            "Installed Battery Storage Capacity [GWh]"
        )

        axis.set_xticks(x_positions)

        axis.set_xticklabels(
            states,
            rotation=38,
            ha="right",
            rotation_mode="anchor",
        )

        axis.set_ylim(
            0,
            maximum_capacity * 1.18,
        )

        axis.set_xlim(
            -0.6,
            len(state_data) - 0.4,
        )

        axis.yaxis.grid(
            True,
            color="#D9D9D9",
            linewidth=0.5,
            linestyle="-",
        )

        axis.xaxis.grid(False)
        axis.set_axisbelow(True)

        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

        axis.spines["left"].set_color("#777777")
        axis.spines["bottom"].set_color("#777777")

        axis.spines["left"].set_linewidth(0.6)
        axis.spines["bottom"].set_linewidth(0.6)

        axis.tick_params(
            axis="both",
            width=0.5,
        )

        figure.subplots_adjust(
            left=0.09,
            right=0.99,
            top=0.90,
            bottom=0.29,
        )

        # ------------------------------------------------------------
        # Save inside the Git repository
        # ------------------------------------------------------------
        figures_directory = (
            LocalPath(__file__).resolve().parent
            / "figures"
        )

        figures_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        pdf_file = (
            figures_directory
            / "battery_capacity_by_state.pdf"
        )

        png_file = (
            figures_directory
            / "battery_capacity_by_state.png"
        )

        figure.savefig(
            pdf_file,
            bbox_inches="tight",
            pad_inches=0.05,
        )

        figure.savefig(
            png_file,
            dpi=300,
            bbox_inches="tight",
            pad_inches=0.05,
        )

        local_plt.close(figure)

        print("PDF saved:", pdf_file)
        print("PNG saved:", png_file)

        return pdf_file, png_file


    battery_state_figure_files = export_battery_state_figure(
        pd_module=pd,
        np_module=np,
        database_engine=mastr_engine,
    )

    battery_state_figure_files
    return


@app.cell
def _(mastr_engine, pd):
    battery_by_state = pd.read_sql_table(
        "battery_by_state",
        con=mastr_engine,
    )

    print(f"Total systems: {battery_by_state['Total_Systems'].sum():,}")
    print(f"Total battery capacity: {battery_by_state['Total_Capacity_GWh'].sum():.2f} GWh")
    return


@app.cell
def _(mastr_engine, pd):
    df_battery_class = pd.read_sql_table(
        "battery_by_technology",
        con=mastr_engine,
    )

    df_battery_class["Total_GWh"] = (
        df_battery_class["Total_GWh"]
        .astype(float)
        .round(3)
    )

    df_battery_class
    return (df_battery_class,)


@app.cell
def _(df_battery_class, go, pd):
    def _():
        df_plot = (
            df_battery_class
            .dropna(subset=["Batterietechnologie"])
            .copy()
        )

        lithium_capacity = df_plot.loc[
            df_plot["Batterietechnologie"] == "Lithium-Batterie",
            "Total_GWh"
        ].sum()

        other_capacity = df_plot.loc[
            df_plot["Batterietechnologie"] != "Lithium-Batterie",
            "Total_GWh"
        ].sum()

        total_capacity = lithium_capacity + other_capacity

        if total_capacity <= 0:
            raise ValueError(
                "No battery-capacity data was found in battery_by_technology."
            )

        lithium_share = (
            lithium_capacity
            / total_capacity
            * 100
        )

        df_summary = pd.DataFrame({
            "Technology": [
                "Lithium batteries",
                "Other battery technologies"
            ],
            "Capacity [GWh]": [
                lithium_capacity,
                other_capacity
            ]
        })

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=df_summary["Technology"],
                    values=df_summary["Capacity [GWh]"],
                    hole=0.62,
                    sort=False,
                    direction="clockwise",
                    marker=dict(
                        colors=["#176B87", "#D9D9D9"],
                        line=dict(
                            color="white",
                            width=2
                        )
                    ),
                    textinfo="none",
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Capacity: %{value:.2f} GWh<br>"
                        "Share: %{percent}"
                        "<extra></extra>"
                    )
                )
            ]
        )

        fig.add_annotation(
            text=(
                f"<b>{lithium_share:.1f}%</b>"
                "<br>"
                "<span style='font-size:15px'>"
                "Lithium batteries"
                "</span>"
            ),
            x=0.5,
            y=0.5,
            showarrow=False,
            align="center",
            font=dict(
                size=23,
                color="#17365D"
            )
        )

        fig.update_layout(
            title=dict(
                text=(
                    "Installed Battery Storage Capacity "
                    "by Technology in Germany"
                ),
                x=0.5,
                xanchor="center",
                font=dict(
                    size=21,
                    color="#17365D"
                )
            ),
            template="plotly_white",
            width=850,
            height=520,
            legend=dict(
                orientation="h",
                x=0.5,
                xanchor="center",
                y=-0.05,
                yanchor="top",
                font=dict(size=14)
            ),
            margin=dict(
                l=50,
                r=50,
                t=90,
                b=90
            ),
            paper_bgcolor="white"
        )

        fig.show()

        return df_summary


    _()
    return


@app.cell
def _(mastr_engine, pd, px):
    def _():
        df_category_summary = pd.read_sql_table(
            "battery_by_category",
            con=mastr_engine
        )

        df_category_summary = df_category_summary.rename(
            columns={
                "Share_percent": "Share_%"
            }
        )

        df_category_summary["Total_GWh"] = (
            df_category_summary["Total_GWh"]
            .round(3)
        )

        df_category_summary["Share_%"] = (
            df_category_summary["Share_%"]
            .round(1)
        )

        fig_cat = px.pie(
            df_category_summary,
            values="Total_GWh",
            names="Category",
            title="Germany Battery Storage by Category (MaStR)",
            hole=0.4
        )

        fig_cat.show()
        return df_category_summary


    _()
    return


@app.cell
def _(Path, mastr_engine, pd, plt):
    def _():
        # Keep a fixed order so the colors and legend remain consistent
        category_order = [
            "Home Storage",
            "Large Scale Storage",
            "Commercial Storage",
        ]

        # Read from the small aggregated database
        df_category_summary = pd.read_sql_table(
            "battery_by_category",
            con=mastr_engine,
        )

        # Match the column name used elsewhere in the notebook
        if "Share_percent" in df_category_summary.columns:
            df_category_summary = df_category_summary.rename(
                columns={"Share_percent": "Share_%"}
            )

        df_battery_category = (
            df_category_summary
            .set_index("Category")
            .reindex(category_order)
            .dropna(subset=["Total_GWh"])
            .reset_index()
            .copy()
        )

        values = df_battery_category["Total_GWh"].to_numpy()
        categories = df_battery_category["Category"].tolist()

        colors = [
            "#636EFA",  # Home Storage
            "#EF553B",  # Large Scale Storage
            "#00CC96",  # Commercial Storage
        ]

        fig_battery_category, ax = plt.subplots(
            figsize=(7.0, 4.8)
        )

        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,
            colors=colors,
            startangle=180,
            counterclock=True,
            autopct=lambda pct: f"{pct:.1f}%",
            pctdistance=0.72,
            wedgeprops={
                "width": 0.55,
                "edgecolor": "white",
                "linewidth": 0.8,
            },
            textprops={
                "fontsize": 9,
            },
        )

        # Improve percentage-label contrast
        for wedge, autotext in zip(wedges, autotexts):
            r, g, b, _ = wedge.get_facecolor()

            brightness = (
                0.299 * r
                + 0.587 * g
                + 0.114 * b
            )

            autotext.set_color(
                "black" if brightness > 0.65 else "white"
            )
            autotext.set_fontsize(9)

        ax.legend(
            wedges,
            categories,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
            fontsize=9,
            title="Category",
            title_fontsize=9,
        )

        ax.set_aspect("equal")

        fig_battery_category.subplots_adjust(
            left=0.02,
            right=0.78,
            bottom=0.04,
            top=0.96,
        )

        # Save figures inside the Git project
        figures_dir = (
            Path(__file__).resolve().parent
            / "figures"
        )

        figures_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pgf = figures_dir / "battery_category.pgf"
        output_pdf = figures_dir / "battery_category.pdf"

        fig_battery_category.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
            pad_inches=0.04,
        )

        fig_battery_category.savefig(
            output_pdf,
            bbox_inches="tight",
            pad_inches=0.04,
        )

        plt.close(fig_battery_category)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)


    _()
    return


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
def _(df_results5, plt):
    def _():
        from pathlib import Path

        fig, ax = plt.subplots(figsize=(10.5, 5.4))

        # Remaining net exports
        ax.plot(
            df_results5["Additional Storage [GWh]"],
            df_results5["Remaining Net Export [TWh]"],
            color="#636EFA",
            marker="o",
            markersize=5,
            linewidth=2.2,
            label="Remaining Net Export",
        )

        # Remaining net imports
        ax.plot(
            df_results5["Additional Storage [GWh]"],
            df_results5["Remaining Net Import [TWh]"],
            color="#EF553B",
            marker="o",
            markersize=5,
            linewidth=2.2,
            label="Remaining Net Import",
        )

        # Current storage reference
        ax.axvline(
            x=0,
            color="red",
            linestyle="--",
            linewidth=1.4,
        )

        # Selected storage reference
        ax.axvline(
            x=75,
            color="green",
            linestyle="--",
            linewidth=1.4,
        )

        # Annotations
        ax.text(
            4,
            34.5,
            "Current: 68 GWh total",
            fontsize=10,
            color="red",
            ha="left",
            va="center",
        )

        ax.text(
            79,
            34.5,
            "Selected: +75 GWh (59% reduction)",
            fontsize=10,
            color="green",
            ha="left",
            va="center",
        )

        # Axis labels
        ax.set_xlabel(
            "Additional storage on top of current 68 GWh [GWh]",
            fontsize=12,
            labelpad=8,
        )

        ax.set_ylabel(
            "Energy [TWh]",
            fontsize=12,
            labelpad=8,
        )

        ax.set_xlim(-5, 310)
        ax.set_ylim(0, 36)

        ax.tick_params(
            axis="both",
            labelsize=10,
        )

        ax.grid(
            True,
            linewidth=0.5,
            alpha=0.30,
        )

        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.legend(
            title="Type",
            frameon=False,
            loc="center left",
            bbox_to_anchor=(1.01, 0.82),
            fontsize=9,
            title_fontsize=10,
        )

        fig.subplots_adjust(
            left=0.10,
            right=0.78,
            bottom=0.16,
            top=0.94,
        )

        # ============================================================
        # Save PDF inside the project repository
        # ============================================================

        Path("figures").mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pdf = "figures/storage_import_reduction.pdf"

        fig.savefig(
            output_pdf,
            format="pdf",
            bbox_inches="tight",
        )

        plt.close(fig)

        print("PDF saved:", output_pdf)


    _()
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
def _(df_storage_economics):
    def _():
        import plotly.graph_objects as go

        # Exclude the zero-storage baseline from the bars
        df_plot = df_storage_economics[
            df_storage_economics["Additional Storage [GWh]"] > 0
        ].copy()

        # Baseline import cost: no additional storage
        baseline_cost = df_storage_economics.loc[
            df_storage_economics["Additional Storage [GWh]"] == 0,
            "Estimated Import Cost [Billion €]"
        ].iloc[0]

        # Labels such as +10, +20, +30, ...
        x_labels = [
            f"+{int(value)}"
            for value in df_plot["Additional Storage [GWh]"]
        ]

        # Labels showing savings above each bar
        savings_labels = [
            f"Saving: €{value:.2f} bn"
            for value in df_plot["Estimated Savings [Billion €]"]
        ]

        fig_import_cost = go.Figure()

        # Remaining import-cost bars
        fig_import_cost.add_trace(
            go.Bar(
                x=x_labels,
                y=df_plot["Estimated Import Cost [Billion €]"],
                name="Remaining annual import cost",
                text=savings_labels,
                textposition="outside",
                cliponaxis=False,
                marker=dict(
                    color="#6F9ED4",
                    line=dict(width=0)
                ),
                hovertemplate=(
                    "<b>Additional storage: %{x} GWh</b><br>"
                    "Remaining import cost: €%{y:.2f} billion/year<br>"
                    "%{text}"
                    "<extra></extra>"
                ),
            )
        )

        # Baseline reference line
        fig_import_cost.add_hline(
            y=baseline_cost,
            line_dash="dash",
            line_color="#D9534F",
            line_width=1.6,
            annotation_text=(
                f"Baseline import cost without additional storage: "
                f"€{baseline_cost:.2f} billion/year"
            ),
            annotation_position="top right",
            annotation_font=dict(
                size=11,
                color="#D9534F"
            ),
        )

        fig_import_cost.update_layout(
            title=dict(
                text=(
                    "Estimated Annual Electricity Import Cost "
                    "under Storage Expansion Scenarios"
                ),
                x=0.5,
                xanchor="center",
                font=dict(size=18, color="#1F365C"),
            ),

            xaxis=dict(
                title="Additional battery storage capacity [GWh]",
                showgrid=False,
                zeroline=False,
                linecolor="#BFBFBF",
                tickfont=dict(size=12),
            ),

            yaxis=dict(
                title="Estimated annual import cost [billion €/year]",
                range=[0, baseline_cost * 1.14],
                tickprefix="€",
                ticksuffix=" bn",
                tickformat=".1f",
                gridcolor="#E6E6E6",
                zeroline=True,
                zerolinecolor="#BFBFBF",
            ),

            template="plotly_white",
            showlegend=False,
            width=1050,
            height=570,

            margin=dict(
                l=90,
                r=45,
                t=110,
                b=80,
            ),

            plot_bgcolor="#FAFAFA",
            paper_bgcolor="white",
            font=dict(
                family="Arial",
                size=12,
                color="#222222",
            ),
        )
        return fig_import_cost.show()


    _()
    return


@app.cell
def _(df_storage_economics, np, plt):
    def _():
        from pathlib import Path

        df_storage_savings = df_storage_economics[
            df_storage_economics["Additional Storage [GWh]"] > 0
        ].copy()

        baseline_cost = df_storage_economics.loc[
            df_storage_economics["Additional Storage [GWh]"] == 0,
            "Estimated Import Cost [Billion €]",
        ].iloc[0]

        labels = [
            f"+{int(value)}"
            for value in df_storage_savings["Additional Storage [GWh]"]
        ]

        import_costs = (
            df_storage_savings["Estimated Import Cost [Billion €]"]
            .to_numpy()
        )

        savings = (
            df_storage_savings["Estimated Savings [Billion €]"]
            .to_numpy()
        )

        x = np.arange(len(labels))

        fig_storage_savings, ax = plt.subplots(
            figsize=(7.2, 4.6)
        )

        # ------------------------------------------------------------
        # Bars
        # ------------------------------------------------------------

        bars = ax.bar(
            x,
            import_costs,
            width=0.65,
            color="#6F9ED4",
            edgecolor="none",
        )

        # ------------------------------------------------------------
        # Savings labels
        # ------------------------------------------------------------

        for bar, saving in zip(bars, savings):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.035,
                f"Savings: €{saving:.2f} bn",
                ha="center",
                va="bottom",
                fontsize=5.5,
            )

        # ------------------------------------------------------------
        # Baseline reference line
        # ------------------------------------------------------------

        ax.axhline(
            y=baseline_cost,
            color="#D9534F",
            linestyle=(0, (6, 5)),
            linewidth=1.2,
        )

        ax.text(
            len(labels) - 0.05,
            baseline_cost + 0.04,
            f"Baseline: €{baseline_cost:.2f} bn/year",
            ha="right",
            va="bottom",
            fontsize=7.2,
            color="#D9534F",
        )

        # ------------------------------------------------------------
        # Axes
        # ------------------------------------------------------------

        ax.set_xlabel(
            "Additional battery storage capacity [GWh]",
            fontsize=10,
        )

        ax.set_ylabel(
            "Estimated annual import cost [billion €/year]",
            fontsize=10,
        )

        ax.set_xticks(x)
        ax.set_xticklabels(labels)

        ax.set_ylim(
            0,
            baseline_cost * 1.18,
        )

        yticks = np.arange(0, 3.1, 0.5)

        ax.set_yticks(yticks)

        ax.set_yticklabels(
            [f"€{value:.1f} bn" for value in yticks]
        )

        # ------------------------------------------------------------
        # Style
        # ------------------------------------------------------------

        ax.grid(
            axis="y",
            alpha=0.30,
            linewidth=0.45,
        )

        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.spines["left"].set_linewidth(0.6)
        ax.spines["bottom"].set_linewidth(0.6)

        ax.tick_params(
            axis="both",
            width=0.5,
        )

        fig_storage_savings.subplots_adjust(
            left=0.13,
            right=0.90,
            bottom=0.18,
            top=0.92,
        )

        # ------------------------------------------------------------
        # Save inside the project repository
        # ------------------------------------------------------------

        Path("figures").mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pgf = "figures/storage_savings.pgf"
        output_pdf = "figures/storage_savings.pdf"

        fig_storage_savings.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
            pad_inches=0.04,
        )

        fig_storage_savings.savefig(
            output_pdf,
            bbox_inches="tight",
            pad_inches=0.04,
        )

        plt.close(fig_storage_savings)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)


    _()
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
    # IRENA Cost-of-Service Tool v2.0 (2025) — Li-Ion LFP — Best Case Only

    # ALL values taken directly from tool's Cost-of-Service sheet

    # Source: https://www.irena.org/Energy-Transition/Technology/Energy-storage-costs

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
                text="ANNUAL COST VS SAVINGS",
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


@app.cell
def _():
    return


@app.cell
def _(df_irena_lcos, np, plt):
    def _():
        from pathlib import Path

        df_plot = df_irena_lcos[
            (df_irena_lcos["Scenario"] == "Best")
            & (df_irena_lcos["LCOS [€/MWh]"].notna())
            & (df_irena_lcos["Additional Storage [GWh]"] > 0)
        ].copy()

        df_plot["Net Loss [Billion €]"] = (
            df_plot["Annual Storage Cost [Billion €]"]
            - df_plot["Annual Import Saving [Billion €]"]
        )

        labels = [
            f"+{int(value)}"
            for value in df_plot["Additional Storage [GWh]"]
        ]

        x = np.arange(len(labels))
        width = 0.26

        # Smaller width so the PGF fits inside the thesis text area
        fig, ax = plt.subplots(figsize=(7.2, 4.4))

        # Annual storage cost
        ax.bar(
            x - width,
            df_plot["Annual Storage Cost [Billion €]"],
            width,
            label="Annual storage cost",
            color="#6495D2",
            edgecolor="none",
        )

        # Annual import saving
        ax.bar(
            x,
            df_plot["Annual Import Saving [Billion €]"],
            width,
            label="Annual import saving",
            color="#50B48C",
            edgecolor="none",
        )

        # Net loss: green for non-positive values, red for losses
        net_loss_colors = [
            "#50B48C" if value <= 0 else "#DC7878"
            for value in df_plot["Net Loss [Billion €]"]
        ]

        ax.bar(
            x + width,
            df_plot["Net Loss [Billion €]"],
            width,
            label="Net loss (cost - saving)",
            color=net_loss_colors,
            edgecolor="none",
        )

        # ------------------------------------------------------------
        # Titles and axes
        # ------------------------------------------------------------

        ax.set_title(
            "Annual Cost vs Savings",
            fontsize=11,
            pad=28,
        )

        ax.set_xlabel(
            "Additional storage (GWh)",
            labelpad=8,
        )

        ax.set_ylabel(
            "Billion €/year",
            labelpad=7,
        )

        ax.set_xticks(x)
        ax.set_xticklabels(labels)

        ax.set_ylim(-0.1, 4.2)

        yticks = np.arange(0, 4.5, 0.5)
        ax.set_yticks(yticks)

        ax.set_yticklabels(
            [
                f"€{int(value)}B"
                if float(value).is_integer()
                else f"€{value:.1f}B"
                for value in yticks
            ]
        )

        # ------------------------------------------------------------
        # Styling
        # ------------------------------------------------------------

        ax.grid(
            axis="y",
            linewidth=0.5,
            alpha=0.3,
        )

        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.spines["left"].set_linewidth(0.6)
        ax.spines["bottom"].set_linewidth(0.6)

        ax.tick_params(
            axis="both",
            width=0.5,
        )

        # Legend placed above the plotting area
        ax.legend(
            loc="lower center",
            bbox_to_anchor=(0.5, 1.01),
            ncol=3,
            frameon=False,
            fontsize=8,
            columnspacing=1.4,
            handlelength=1.6,
        )

        # Manual margins are more reliable than tight_layout for PGF
        fig.subplots_adjust(
            left=0.11,
            right=0.85,
            bottom=0.16,
            top=0.80,
        )

        # ------------------------------------------------------------
        # Save inside the project repository
        # ------------------------------------------------------------

        Path("figures").mkdir(
            parents=True,
            exist_ok=True,
        )

        output_pgf = "figures/storage_cost_vs_savings.pgf"
        output_pdf = "figures/storage_cost_vs_savings.pdf"

        fig.savefig(
            output_pgf,
            backend="pgf",
            bbox_inches="tight",
            pad_inches=0.05,
        )

        fig.savefig(
            output_pdf,
            bbox_inches="tight",
            pad_inches=0.05,
        )

        plt.close(fig)

        print("PGF saved:", output_pgf)
        print("PDF saved:", output_pdf)


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
    ## Renewable Self-Reliance Scenario Analysis
    What additional renewable generation capacity and energy storage are required for Germany to meet its electricity demand using renewable energy alone?

    In this scenario, conventional generation from lignite, hard coal, fossil gas, nuclear, and other conventional sources is excluded. Hydropower, biomass, solar, wind, and other renewable sources are retained. Additional renewable expansion is modelled through solar and wind generation.
    """)
    return


@app.cell
def _(df_smard_consumption, df_smard_generation, renewable_cols):
    df_self_reliance = (
        df_smard_generation[["Start date"] + renewable_cols]
        .merge(
            df_smard_consumption[["Start date", "Consumption"]],
            on="Start date",
            how="inner"
        )
    )

    df_self_reliance["Renewable Generation [MWh]"] = (
        df_self_reliance[renewable_cols].sum(axis=1)
    )

    df_self_reliance["Renewable Balance [MWh]"] = (
        df_self_reliance["Renewable Generation [MWh]"]
        - df_self_reliance["Consumption"]
    )

    df_self_reliance["Renewable Surplus [MWh]"] = (
        df_self_reliance["Renewable Balance [MWh]"]
        .clip(lower=0)
    )

    df_self_reliance["Renewable Deficit [MWh]"] = (
        df_self_reliance["Renewable Balance [MWh]"]
        .clip(upper=0)
        .abs()
    )

    print("RENEWABLE-ONLY SYSTEM BALANCE — 2025")
    print(
        "Total renewable generation:",
        round(df_self_reliance["Renewable Generation [MWh]"].sum() / 1_000_000, 2),
        "TWh"
    )
    print(
        "Total demand:",
        round(df_self_reliance["Consumption"].sum() / 1_000_000, 2),
        "TWh"
    )
    print(
        "Renewable surplus:",
        round(df_self_reliance["Renewable Surplus [MWh]"].sum() / 1_000_000, 2),
        "TWh"
    )
    print(
        "Renewable deficit:",
        round(df_self_reliance["Renewable Deficit [MWh]"].sum() / 1_000_000, 2),
        "TWh"
    )

    df_self_reliance.head()
    return (df_self_reliance,)


@app.cell
def _(df_self_reliance):
    def _():
        storage_capacity_gwh = 68
        storage_capacity_mwh = storage_capacity_gwh * 1000
        storage_efficiency = 0.85

        soc = 0.0

        remaining_surplus = []
        remaining_deficit = []
        storage_soc = []
        charged_energy = []
        discharged_energy = []

        for _, row in df_self_reliance.iterrows():

            surplus = row["Renewable Surplus [MWh]"]
            deficit = row["Renewable Deficit [MWh]"]

            if surplus > 0:
                available_space = storage_capacity_mwh - soc
                charge = min(surplus, available_space)

                soc += charge * storage_efficiency

                remaining_surplus.append(surplus - charge)
                remaining_deficit.append(0)
                charged_energy.append(charge)
                discharged_energy.append(0)

            else:
                discharge = min(deficit, soc)

                soc -= discharge

                remaining_surplus.append(0)
                remaining_deficit.append(deficit - discharge)
                charged_energy.append(0)
                discharged_energy.append(discharge)

            storage_soc.append(soc)

        df_self_reliance_storage = df_self_reliance.copy()

        df_self_reliance_storage["Storage SOC [MWh]"] = storage_soc
        df_self_reliance_storage["Charged Energy [MWh]"] = charged_energy
        df_self_reliance_storage["Discharged Energy [MWh]"] = discharged_energy
        df_self_reliance_storage["Remaining Renewable Surplus [MWh]"] = remaining_surplus
        df_self_reliance_storage["Remaining Renewable Deficit [MWh]"] = remaining_deficit

        print("RENEWABLE SELF-RELIANCE WITH CURRENT STORAGE")
        print(f"Storage capacity: {storage_capacity_gwh} GWh")
        print(
            "Stored renewable surplus:",
            round(df_self_reliance_storage["Charged Energy [MWh]"].sum() / 1_000_000, 2),
            "TWh"
        )
        print(
            "Used from storage:",
            round(df_self_reliance_storage["Discharged Energy [MWh]"].sum() / 1_000_000, 2),
            "TWh"
        )
        print(
            "Remaining renewable deficit:",
            round(df_self_reliance_storage["Remaining Renewable Deficit [MWh]"].sum() / 1_000_000, 2),
            "TWh"
        )
        print(
            "Remaining renewable surplus:",
            round(df_self_reliance_storage["Remaining Renewable Surplus [MWh]"].sum() / 1_000_000, 2),
            "TWh"
        )
        return df_self_reliance_storage.head()


    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Increase solar and wind generation.
    """)
    return


@app.cell
def _(df_self_reliance):
    current_solar_twh = df_self_reliance["Solar"].sum() / 1_000_000

    current_wind_twh = (
        df_self_reliance["Wind Onshore"].sum()
        + df_self_reliance["Wind Offshore"].sum()
    ) / 1_000_000

    current_renewable_twh = (
        df_self_reliance["Renewable Generation [MWh]"].sum()
        / 1_000_000
    )

    total_demand_twh = (
        df_self_reliance["Consumption"].sum()
        / 1_000_000
    )

    annual_energy_gap_twh = total_demand_twh - current_renewable_twh

    print("CURRENT RENEWABLE ENERGY GAP")
    print(f"Current solar generation: {current_solar_twh:.2f} TWh")
    print(f"Current wind generation: {current_wind_twh:.2f} TWh")
    print(f"Current renewable generation: {current_renewable_twh:.2f} TWh")
    print(f"Total demand: {total_demand_twh:.2f} TWh")
    print(f"Annual renewable energy gap: {annual_energy_gap_twh:.2f} TWh")
    return (
        annual_energy_gap_twh,
        current_renewable_twh,
        current_solar_twh,
        current_wind_twh,
        total_demand_twh,
    )


@app.cell
def _(
    annual_energy_gap_twh,
    current_renewable_twh,
    current_solar_twh,
    current_wind_twh,
    pd,
    total_demand_twh,
):
    renewable_share = current_renewable_twh / total_demand_twh * 100

    renewable_balance_table = pd.DataFrame({
        "Metric": [
            "Solar generation",
            "Wind generation",
            "Total renewable generation",
            "Total electricity demand",
            "Renewable share of demand",
            "Annual renewable energy gap",
        ],
        "Value": [
            f"{current_solar_twh:.2f} TWh",
            f"{current_wind_twh:.2f} TWh",
            f"{current_renewable_twh:.2f} TWh",
            f"{total_demand_twh:.2f} TWh",
            f"{renewable_share:.1f} %",
            f"{annual_energy_gap_twh:.2f} TWh",
        ],
    })

    renewable_balance_table
    return


@app.cell
def _(df_self_reliance, month_order, storage_efficiency):
    df_monthly_self_reliance = df_self_reliance.copy()



    df_monthly_self_reliance["Month"] = (
        df_monthly_self_reliance["Start date"]
        .dt.strftime("%b 2025")
    )

    monthly_deficit_analysis = (
        df_monthly_self_reliance
        .groupby("Month")
        .agg(
            Renewable_Generation_TWh=(
                "Renewable Generation [MWh]",
                lambda x: x.sum() / 1_000_000
            ),
            Demand_TWh=(
                "Consumption",
                lambda x: x.sum() / 1_000_000
            ),
            Renewable_Deficit_TWh=(
                "Renewable Deficit [MWh]",
                lambda x: x.sum() / 1_000_000
            ),
            Renewable_Surplus_TWh=(
                "Renewable Surplus [MWh]",
                lambda x: x.sum() / 1_000_000
            ),
            Max_Hourly_Deficit_GWh=(
                "Renewable Deficit [MWh]",
                lambda x: x.max() / 1000
            ),
        )
    )


    monthly_deficit_analysis = monthly_deficit_analysis.reindex(month_order)

    monthly_deficit_analysis["Extra_Renewable_Needed_TWh"] = (
        monthly_deficit_analysis["Renewable_Deficit_TWh"]
        / storage_efficiency
    )

    monthly_deficit_analysis.round(2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    "If Germany relied only on renewables and storage, how much demand would remain unmet?" https://www.energy-charts.info/charts/installed_power/chart.htm?c=DE&year=2026&legendItems=1x8gt (current capacity values taken from fraunhofer)
    https://www.bundeswirtschaftsministerium.de/Redaktion/EN/Downloads/Energy/0406_ueberblickspapier_osterpaket_en.pdf?__blob=publicationFile&v=1&utm_source - future expansion values

    https://www.ise.fraunhofer.de/en/press-media/press-releases/2026/german-public-electricity-generation-in-2025-wind-and-solar-power-take-the-lead.html?utm_source battery expansion storage
    """)
    return


@app.cell
def _(df_smard_consumption, df_smard_generation, pd, px, renewable_cols):
    sr_current_capacity = {
        "wind_onshore_gw": 70.08,
        "wind_offshore_gw": 10.60,
        "solar_gw": 125.2,
        "battery_gwh": 29.80,
        "pumped_hydro_gwh": 40.0,
    }

    sr_scenarios = {
        "2026 Current": {**sr_current_capacity, "battery_gwh": 29.80},

        "EEG 2030 + 100 GWh storage": {
            "wind_onshore_gw": 115.0,
            "wind_offshore_gw": 30.0,
            "solar_gw": 215.0,
            "battery_gwh": 100.0,
            "pumped_hydro_gwh": 40.0,
        },

        "EEG 2030 + 170 GWh storage": {
            "wind_onshore_gw": 115.0,
            "wind_offshore_gw": 30.0,
            "solar_gw": 215.0,
            "battery_gwh": 170.0,
            "pumped_hydro_gwh": 40.0,
        },

        "Self-reliant estimation 1": {
            "wind_onshore_gw": 150.0,
            "wind_offshore_gw": 40.0,
            "solar_gw": 300.0,
            "battery_gwh": 200.0,
            "pumped_hydro_gwh": 40.0,
        },

        "Self-reliant estimation 2": {
            "wind_onshore_gw": 200.0,
            "wind_offshore_gw": 60.0,
            "solar_gw": 600.0,
            "battery_gwh": 250.0,
            "pumped_hydro_gwh": 40.0,
        },
    }

    sr_col_won = "Wind Onshore"
    sr_col_woff = "Wind Offshore"
    sr_col_solar = "Solar"

    sr_base = df_smard_generation.copy()

    sr_base_won = sr_current_capacity["wind_onshore_gw"]
    sr_base_woff = sr_current_capacity["wind_offshore_gw"]
    sr_base_solar = sr_current_capacity["solar_gw"]

    sr_efficiency = 0.85
    sr_results = []

    for sr_name, sr_caps in sr_scenarios.items():

        sr_df = sr_base.copy()

        sr_df[sr_col_won] = (
            sr_base[sr_col_won]
            * (sr_caps["wind_onshore_gw"] / sr_base_won)
        )

        sr_df[sr_col_woff] = (
            sr_base[sr_col_woff]
            * (sr_caps["wind_offshore_gw"] / sr_base_woff)
        )

        sr_df[sr_col_solar] = (
            sr_base[sr_col_solar]
            * (sr_caps["solar_gw"] / sr_base_solar)
        )

        sr_df["Renewable Gen"] = sr_df[renewable_cols].sum(axis=1)

        sr_df = sr_df.merge(
            df_smard_consumption[["Start date", "Consumption"]],
            on="Start date",
            how="inner",
        )

        sr_df["Net"] = sr_df["Renewable Gen"] - sr_df["Consumption"]

        sr_storage_mwh = (
            sr_caps["battery_gwh"] + sr_caps["pumped_hydro_gwh"]
        ) * 1000

        sr_soc = 0.0
        sr_unmet = 0.0

        for sr_net in sr_df["Net"]:

            if sr_net > 0:
                sr_charge = min(sr_net, sr_storage_mwh - sr_soc)
                sr_soc += sr_charge * sr_efficiency

            else:
                sr_deficit = abs(sr_net)
                sr_discharge = min(sr_deficit, sr_soc)
                sr_soc -= sr_discharge
                sr_unmet += (sr_deficit - sr_discharge)

        sr_total_cons = sr_df["Consumption"].sum()
        sr_self_suff = (1 - sr_unmet / sr_total_cons) * 100
        sr_ren_share = sr_df["Renewable Gen"].sum() / sr_total_cons * 100

        sr_results.append({
            "Scenario": sr_name,
            "Wind Onshore [GW]": sr_caps["wind_onshore_gw"],
            "Wind Offshore [GW]": sr_caps["wind_offshore_gw"],
            "Solar [GW]": sr_caps["solar_gw"],
            "Battery Storage [GWh]": sr_caps["battery_gwh"],
            "Total Storage [GWh]": sr_caps["battery_gwh"] + sr_caps["pumped_hydro_gwh"],
            "Renewable Share [%]": round(sr_ren_share, 1),
            "Self-Sufficiency [%]": round(sr_self_suff, 1),
            "Unmet Demand [TWh]": round(sr_unmet / 1e6, 1),
        })

    df_self_reliance2 = pd.DataFrame(sr_results)

    df_self_reliance2["Scenario Label"] = df_self_reliance2["Scenario"].replace({
        "2026 Current": "2026<br>Current",
        "EEG 2030 + 100 GWh storage": "EEG 2030<br>+ 100 GWh storage",
        "EEG 2030 + 170 GWh storage": "EEG 2030<br>+ 170 GWh storage",
        "Self-reliant estimation 1": "Self-reliant<br>estimation 1",
        "Self-reliant estimation 2": "Self-reliant<br>estimation 2",
    })

    fig_sr = px.bar(
        df_self_reliance2,
        x="Scenario Label",
        y="Self-Sufficiency [%]",
        text="Self-Sufficiency [%]",
        color="Scenario Label",
        title="Germany Renewable Self-Sufficiency Under Different Capacity Scenarios",
        color_discrete_sequence=[
            "#B4B2A9",
            "#1D9E75",
            "#0F6E56",
            "#085041",
            "#0B3D2E",
        ],
    )

    fig_sr.add_hline(
        y=100,
        line_dash="dash",
        line_color="red",
        annotation_text="100% self-reliant",
        annotation_position="top right",
    )

    fig_sr.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        marker_line_width=0,
    )

    fig_sr.update_layout(
        template="plotly_white",
        height=600,
        width=1100,
        showlegend=False,
        title=dict(
            x=0.5,
            font=dict(size=16),
        ),
        xaxis_title="Scenario",
        yaxis_title="Self-Sufficiency [%]",
        yaxis=dict(
            range=[0, 120],
            dtick=20,
            gridcolor="lightgray",
        ),
        xaxis=dict(
            tickangle=0,
            tickfont=dict(size=12),
        ),
        margin=dict(l=80, r=80, t=100, b=120),
    )

    fig_sr.show()

    df_self_reliance2.drop(columns=["Scenario Label"])
    return (df_self_reliance2,)


@app.cell
def _(df_self_reliance2, go):

    df_cap_plot = df_self_reliance2.copy()

    df_cap_plot["Scenario Short"] = df_cap_plot["Scenario"].replace({
        "2026 Current": "2026<br>Current",
        "EEG 2030 + 100 GWh storage": "EEG 2030<br>100 GWh storage",
        "EEG 2030 + 170 GWh storage": "EEG 2030<br>170 GWh storage",
        "Self-reliant estimation 1": "Self-reliant<br>Scenario 1",
        "Self-reliant estimation 2": "Self-reliant<br>Scenario 2",
    })

    df_cap_plot["Total Renewable Capacity [GW]"] = (
        df_cap_plot["Wind Onshore [GW]"]
        + df_cap_plot["Wind Offshore [GW]"]
        + df_cap_plot["Solar [GW]"]
    )

    # ----------------------------
    # Create figure
    # ----------------------------
    fig_capacity = go.Figure()

    fig_capacity.add_bar(
        x=df_cap_plot["Scenario Short"],
        y=df_cap_plot["Wind Onshore [GW]"],
        name="Wind Onshore",
        marker_color="#4C78A8",
    )

    fig_capacity.add_bar(
        x=df_cap_plot["Scenario Short"],
        y=df_cap_plot["Wind Offshore [GW]"],
        name="Wind Offshore",
        marker_color="#72B7B2",
    )

    fig_capacity.add_bar(
        x=df_cap_plot["Scenario Short"],
        y=df_cap_plot["Solar [GW]"],
        name="Solar",
        marker_color="#F2C14E",
    )

    # ----------------------------
    # Total capacity labels
    # ----------------------------
    fig_capacity.add_scatter(
        x=df_cap_plot["Scenario Short"],
        y=df_cap_plot["Total Renewable Capacity [GW]"] + 20,
        mode="text",
        text=[
            f"{v:.0f} GW"
            for v in df_cap_plot["Total Renewable Capacity [GW]"]
        ],
        textfont=dict(
            size=15,
            color="black",
        ),
        showlegend=False,
    )

    # ----------------------------
    # Layout
    # ----------------------------
    fig_capacity.update_layout(
        barmode="stack",
        template="plotly_white",
        title=dict(
            text="Installed Renewable Capacity by Scenario",
            x=0.5,
            font=dict(size=22),
        ),
        xaxis_title="Scenario",
        yaxis_title="Installed Capacity [GW]",
        height=550,
        width=1100,
        legend=dict(
            orientation="h",
            y=1.12,
            x=0.5,
            xanchor="center",
            font=dict(size=12),
        ),
        margin=dict(
            l=70,
            r=40,
            t=110,
            b=90,
        ),
    )

    fig_capacity.update_yaxes(
        range=[
            0,
            df_cap_plot["Total Renewable Capacity [GW]"].max() * 1.15,
        ],
        gridcolor="lightgray",
        zeroline=False,
    )

    fig_capacity.show()
    return


@app.cell
def _(Path, df_self_reliance2):
    import matplotlib
    matplotlib.use("pgf")
    import matplotlib.pyplot as pgf_plt

    matplotlib.rcParams.update({
        "pgf.texsystem": "pdflatex",
        "font.family": "serif",
        "text.usetex": True,
        "pgf.rcfonts": False,
        "pgf.preamble": "\n".join([
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage[T1]{fontenc}",
            r"\usepackage{lmodern}",
            r"\providecommand{\mathdefault}[1]{#1}",
        ]),
        "axes.formatter.use_mathtext": False,
        "axes.unicode_minus": False,
        "axes.labelsize": 11,
        "font.size": 11,
        "legend.fontsize": 10,
        "xtick.labelsize": 8,
        "ytick.labelsize": 9,
        "figure.figsize": (7.8, 4.6),
    })

    pgf_df = df_self_reliance2.copy()

    pgf_df["Scenario Short"] = pgf_df["Scenario"].replace({
        "2026 Current": "2026\nCurrent",
        "EEG 2030 + 100 GWh storage": "EEG 2030\n100 GWh storage",
        "EEG 2030 + 170 GWh storage": "EEG 2030\n170 GWh storage",
        "Self-reliant estimation 1": "Self-reliant\nScenario 1",
        "Self-reliant estimation 2": "Self-reliant\nScenario 2",
    })

    pgf_scenarios = pgf_df["Scenario Short"].tolist()
    pgf_wind_on = pgf_df["Wind Onshore [GW]"].tolist()
    pgf_wind_off = pgf_df["Wind Offshore [GW]"].tolist()
    pgf_solar = pgf_df["Solar [GW]"].tolist()

    pgf_totals = [
        wo + wf + s
        for wo, wf, s in zip(
            pgf_wind_on,
            pgf_wind_off,
            pgf_solar,
        )
    ]

    pgf_x = range(len(pgf_scenarios))
    pgf_w = 0.5

    pgf_fig, pgf_ax = pgf_plt.subplots()

    pgf_ax.bar(
        pgf_x,
        pgf_wind_on,
        pgf_w,
        label="Wind Onshore",
        color="#4C78A8",
    )

    pgf_ax.bar(
        pgf_x,
        pgf_wind_off,
        pgf_w,
        bottom=pgf_wind_on,
        label="Wind Offshore",
        color="#72B7B2",
    )

    pgf_ax.bar(
        pgf_x,
        pgf_solar,
        pgf_w,
        bottom=[
            a + b
            for a, b in zip(
                pgf_wind_on,
                pgf_wind_off,
            )
        ],
        label="Solar",
        color="#F2C14E",
    )

    for pgf_idx, pgf_total in enumerate(pgf_totals):
        pgf_ax.text(
            pgf_idx,
            pgf_total + 8,
            f"{int(pgf_total)} GW",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    pgf_ax.set_xticks(list(pgf_x))
    pgf_ax.set_xticklabels(
        pgf_scenarios,
        fontsize=9,
    )

    pgf_ax.set_ylabel("Installed Capacity [GW]")
    pgf_ax.set_title("Installed Renewable Capacity by Scenario")

    pgf_ax.set_ylim(
        0,
        max(pgf_totals) * 1.15,
    )

    pgf_ax.yaxis.grid(
        True,
        color="lightgray",
        linewidth=0.5,
    )

    pgf_ax.set_axisbelow(True)

    pgf_ax.spines["top"].set_visible(False)
    pgf_ax.spines["right"].set_visible(False)

    pgf_ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.12),
        ncol=3,
        fontsize=9,
        frameon=False,
    )

    pgf_plt.tight_layout()

    # ============================================================
    # Save inside the project repository
    # ============================================================

    Path("figures").mkdir(
        parents=True,
        exist_ok=True,
    )

    output_pgf = "figures/capacity_scenarios.pgf"
    output_pdf = "figures/capacity_scenarios.pdf"

    pgf_fig.savefig(
        output_pgf,
        backend="pgf",
        bbox_inches="tight",
    )

    pgf_fig.savefig(
        output_pdf,
        bbox_inches="tight",
    )

    print("PGF saved:", output_pgf)
    print("PDF saved:", output_pdf)

    pgf_plt.close(pgf_fig)
    return (pgf_plt,)


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


@app.cell
def _(df_self_reliance2, pgf_plt):
    def _():
        pgf_sr = df_self_reliance2.copy()

        pgf_sr["Scenario Short"] = pgf_sr["Scenario"].replace({
            "2026 Current": "2026\nCurrent",
            "EEG 2030 + 100 GWh storage": "EEG 2030\n+ 100 GWh storage",
            "EEG 2030 + 170 GWh storage": "EEG 2030\n+ 170 GWh storage",
            "Self-reliant estimation 1": "Self-reliant\nestimation 1",
            "Self-reliant estimation 2": "Self-reliant\nestimation 2",
        })

        pgf_x = range(len(pgf_sr))
        pgf_values = pgf_sr["Self-Sufficiency [%]"].tolist()

        pgf_colors = [
            "#B4B2A9",
            "#1D9E75",
            "#0F6E56",
            "#085041",
            "#0B3D2E",
        ]

        pgf_fig, pgf_ax = pgf_plt.subplots()

        pgf_ax.bar(
            pgf_x,
            pgf_values,
            width=0.6,
            color=pgf_colors,
        )

        for i, value in enumerate(pgf_values):
            pgf_ax.text(
                i,
                value + 1.2,
                f"{value:.1f}\\%",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        pgf_ax.axhline(
            y=100,
            color="red",
            linestyle="--",
            linewidth=1.1,
        )

        pgf_ax.text(
            len(pgf_values) - 0.1,
            101.5,
            "100\\% self-reliant",
            ha="right",
            va="bottom",
            fontsize=9,
            color="red",
        )

        pgf_ax.set_xticks(list(pgf_x))
        pgf_ax.set_xticklabels(pgf_sr["Scenario Short"], fontsize=9)
        pgf_ax.set_ylabel("Self-sufficiency [\\%]")
        pgf_ax.set_xlabel("Scenario")
        pgf_ax.set_title("Renewable Self-Sufficiency by Scenario")
        pgf_ax.set_ylim(0, 120)
        pgf_ax.yaxis.grid(True, color="lightgray", linewidth=0.5)
        pgf_ax.set_axisbelow(True)
        pgf_ax.spines["top"].set_visible(False)
        pgf_ax.spines["right"].set_visible(False)

        pgf_plt.subplots_adjust(
            top=0.88,
            bottom=0.24,
            left=0.10,
            right=0.98,
        )

        pgf_plt.savefig(
            r"D:\Research_Project\Thesis\Thesis\figures\self_sufficiency_scenarios.pgf",
            backend="pgf"
        )

        print("PGF saved: self_sufficiency_scenarios.pgf")
        return pgf_plt.close()


    _()
    return


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
