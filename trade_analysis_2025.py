import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from pathlib import Path
    import re
    import sys

    # Make sure this notebook can import utils.py when it is placed in the project root.
    ROOT = Path(__file__).resolve().parent
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from utils import load_smard_market_trade, smard_load

    DATA_CLEANED = ROOT / "data" / "cleaned"
    REPORTS = ROOT / "reports"
    FIGURES = ROOT / "figures"
    for folder in [DATA_CLEANED, REPORTS, FIGURES]:
        folder.mkdir(parents=True, exist_ok=True)
    return DATA_CLEANED, load_smard_market_trade, mo, pd, px, re, smard_load


@app.cell
def _(mo):
    mo.md(r"""
    # Germany Electricity Import/Export Analysis — 2025

    This notebook focuses only on **Germany's cross-border electricity trade** in 2025.

    ## Main questions

    1. Was Germany a net electricity importer or exporter in 2025?
    2. Which countries did Germany import from and export to the most?
    3. How did trade patterns change month by month?
    4. Are imports higher during low-renewable / high residual-load periods?
    5. Are exports higher during renewable surplus periods?

    ## Why this matters for STAGES

    The main STAGES project asks whether renewables can cover Germany's electricity demand. Imports and exports are important because Germany is part of the European interconnected grid. Germany can export electricity during surplus periods and import electricity during low-renewable or high-demand periods.

    So this section helps explain **cross-border balancing**: not just how much Germany produces, but how it interacts with neighbouring electricity systems.
    """)
    return


@app.cell
def _(DATA_CLEANED, load_smard_market_trade, pd):
    START_DATE_TRADE = "2025-01-01"
    END_DATE_TRADE = "2026-01-01"  # exclusive
    TRADE_CACHE = DATA_CLEANED / "smard_trade_2025_country_hourly.csv"

    def trade_load_or_fetch(force_refresh: bool = False) -> pd.DataFrame:
        """Load cached SMARD market-trade data or fetch it from the SMARD endpoint."""
        if TRADE_CACHE.exists() and not force_refresh:
            trade_df_loaded = pd.read_csv(TRADE_CACHE)
            trade_df_loaded["Start date"] = pd.to_datetime(trade_df_loaded["Start date"])
            if "End date" in trade_df_loaded.columns:
                trade_df_loaded["End date"] = pd.to_datetime(trade_df_loaded["End date"])
            return trade_df_loaded

        trade_df_downloaded = load_smard_market_trade(
            start_date=START_DATE_TRADE,
            end_date=END_DATE_TRADE,
        )
        trade_df_downloaded.to_csv(TRADE_CACHE, index=False)
        return trade_df_downloaded

    df_trade_2025 = trade_load_or_fetch(force_refresh=False)
    return END_DATE_TRADE, START_DATE_TRADE, TRADE_CACHE, df_trade_2025


@app.cell
def _(END_DATE_TRADE, START_DATE_TRADE, TRADE_CACHE, df_trade_2025, mo):
    mo.md(f"""
    ## 1. Trade data loaded

    | Item | Value |
    |---|---:|
    | Period | `{START_DATE_TRADE}` to `{END_DATE_TRADE}` exclusive |
    | Hourly rows | **{len(df_trade_2025):,}** |
    | Columns | **{len(df_trade_2025.columns):,}** |
    | Start | `{df_trade_2025['Start date'].min()}` |
    | End | `{df_trade_2025['Start date'].max()}` |
    | Cache file | `{TRADE_CACHE.relative_to(TRADE_CACHE.parents[2]) if len(TRADE_CACHE.parents) > 2 else TRADE_CACHE}` |

    The data is loaded through the existing project helper function `load_smard_market_trade(...)` from `utils.py`. The first run fetches the data from SMARD; later runs use the cached CSV in `data/cleaned/`.
    """)
    return


@app.cell
def _(df_trade_2025):
    df_trade_2025.head()
    return


@app.cell
def _(df_trade_2025, mo):
    export_cols_trade = [c for c in df_trade_2025.columns if "(export)" in c.lower()]
    import_cols_trade = [c for c in df_trade_2025.columns if "(import)" in c.lower()]

    mo.md(
        f"""
    ## 2. Available import/export columns

    | Column type | Count |
    |---|---:|
    | Export country/partner columns | **{len(export_cols_trade)}** |
    | Import country/partner columns | **{len(import_cols_trade)}** |

    These columns are the country-level trade variables returned by the SMARD market-data download. The notebook uses them to calculate country-wise totals.
    """
    )
    return export_cols_trade, import_cols_trade


@app.cell
def _(export_cols_trade, import_cols_trade, mo):
    mo.md(
        "### Export columns\n"
        + "\n".join([f"- `{c}`" for c in export_cols_trade])
        + "\n\n### Import columns\n"
        + "\n".join([f"- `{c}`" for c in import_cols_trade])
    )
    return


@app.cell
def _(df_trade_2025, export_cols_trade, import_cols_trade, pd, re):
    def trade_partner_from_column(col: str) -> str:
        """
        Convert a SMARD country trade column into a readable partner name.

        The exact SMARD labels can change slightly, so this function is deliberately
        conservative: it removes units/direction words and keeps the readable partner text.
        """
        name = str(col)
        name = name.replace(" Calculated resolutions", "")
        name = re.sub(r"\[.*?\]", "", name)
        name = re.sub(r"\(\s*export\s*\)", "", name, flags=re.I)
        name = re.sub(r"\(\s*import\s*\)", "", name, flags=re.I)
        name = re.sub(r"commercial exchange", "", name, flags=re.I)
        name = re.sub(r"cross[- ]border", "", name, flags=re.I)
        name = name.replace("Germany/Luxembourg", "Germany")
        name = name.replace("Germany", "")
        name = name.replace("DE/LU", "")
        name = name.replace("DE", "")
        name = re.sub(r"[→➜>]+", " ", name)
        name = re.sub(r"[-–—_/]+", " ", name)
        name = re.sub(r"\s+", " ", name).strip(" :;,.|()")
        return name if name else col

    def trade_to_long(df: pd.DataFrame) -> pd.DataFrame:
        pieces = []
        for col in export_cols_trade:
            partner = trade_partner_from_column(col)
            temp = df[["Start date", col]].copy()
            temp.columns = ["Date", "MWh"]
            temp["Country"] = partner
            temp["Direction"] = "Export"
            pieces.append(temp)
        for col in import_cols_trade:
            partner = trade_partner_from_column(col)
            temp = df[["Start date", col]].copy()
            temp.columns = ["Date", "MWh"]
            temp["MWh"] = temp["MWh"].abs()
            temp["Country"] = partner
            temp["Direction"] = "Import"
            pieces.append(temp)

        if not pieces:
            return pd.DataFrame(columns=["Date", "MWh", "Country", "Direction"])

        out = pd.concat(pieces, ignore_index=True)
        out["Date"] = pd.to_datetime(out["Date"])
        out["Month"] = out["Date"].dt.to_period("M").astype(str)
        out["Month_Name"] = out["Date"].dt.strftime("%b")
        out["MWh"] = pd.to_numeric(out["MWh"], errors="coerce").fillna(0)
        return out

    df_trade_long_2025 = trade_to_long(df_trade_2025)
    return (df_trade_long_2025,)


@app.cell
def _(df_trade_long_2025):
    df_trade_long_2025.head(12)
    return


@app.cell
def _(df_trade_2025, df_trade_long_2025, mo):
    total_export_twh = df_trade_2025["Total_Export_MWh"].sum() / 1e6
    total_import_twh = df_trade_2025["Total_Import_MWh"].sum() / 1e6
    net_trade_twh = df_trade_2025["Net_Trade_MWh"].sum() / 1e6
    net_status = "net exporter" if net_trade_twh > 0 else "net importer"

    country_direction_summary = (
        df_trade_long_2025
        .groupby(["Country", "Direction"], as_index=False)["MWh"]
        .sum()
    )

    country_summary_wide = (
        country_direction_summary
        .pivot(index="Country", columns="Direction", values="MWh")
        .fillna(0)
        .reset_index()
    )

    if "Export" not in country_summary_wide.columns:
        country_summary_wide["Export"] = 0.0
    if "Import" not in country_summary_wide.columns:
        country_summary_wide["Import"] = 0.0

    country_summary_wide["Net Export"] = country_summary_wide["Export"] - country_summary_wide["Import"]
    country_summary_wide["Export [TWh]"] = country_summary_wide["Export"] / 1e6
    country_summary_wide["Import [TWh]"] = country_summary_wide["Import"] / 1e6
    country_summary_wide["Net Export [TWh]"] = country_summary_wide["Net Export"] / 1e6
    country_summary_wide = country_summary_wide.sort_values("Net Export [TWh]", ascending=False)

    top_export_partner = country_summary_wide.sort_values("Export [TWh]", ascending=False).iloc[0]
    top_import_partner = country_summary_wide.sort_values("Import [TWh]", ascending=False).iloc[0]

    mo.md(
        f"""
    ## 3. Executive summary — Germany's 2025 electricity trade

    | Metric | Value | Meaning |
    |---|---:|---|
    | Total exports | **{total_export_twh:.2f} TWh** | Electricity sent from Germany to neighbouring countries |
    | Total imports | **{total_import_twh:.2f} TWh** | Electricity received by Germany from neighbouring countries |
    | Net trade balance | **{net_trade_twh:.2f} TWh** | Positive = net exporter, negative = net importer |
    | Overall status | **Germany was a {net_status}** | Based on annual exports minus imports |
    | Largest export partner | **{top_export_partner['Country']} ({top_export_partner['Export [TWh]']:.2f} TWh)** | Country receiving the most electricity from Germany |
    | Largest import partner | **{top_import_partner['Country']} ({top_import_partner['Import [TWh]']:.2f} TWh)** | Country supplying the most electricity to Germany |

    **Important interpretation:** imports do not automatically mean electricity shortage. In the European power market, Germany may import electricity because it is cheaper or more available abroad, and export when domestic generation is high.
    """
    )
    return (
        country_summary_wide,
        net_status,
        net_trade_twh,
        top_export_partner,
        top_import_partner,
        total_export_twh,
        total_import_twh,
    )


@app.cell
def _(country_summary_wide):
    country_summary_wide[["Country", "Export [TWh]", "Import [TWh]", "Net Export [TWh]"]]
    return


@app.cell
def _(country_summary_wide, px):
    country_totals_plot_df = country_summary_wide.sort_values("Export [TWh]", ascending=False)
    fig_country_totals_trade = px.bar(
        country_totals_plot_df,
        x="Country",
        y=["Export [TWh]", "Import [TWh]"],
        barmode="group",
        title="Germany electricity trade by country — imports and exports, 2025",
        labels={"value": "Electricity [TWh]", "variable": "Direction"},
    )
    fig_country_totals_trade.update_layout(height=520, xaxis_tickangle=-35, legend_title="")
    fig_country_totals_trade
    return


@app.cell
def _(country_summary_wide, px):
    net_country_plot_df = country_summary_wide.sort_values("Net Export [TWh]")
    fig_net_country_trade = px.bar(
        net_country_plot_df,
        x="Net Export [TWh]",
        y="Country",
        orientation="h",
        title="Net electricity trade balance by country, 2025",
        labels={"Net Export [TWh]": "Net export [TWh] (negative = net import)", "Country": "Partner country"},
    )
    fig_net_country_trade.add_vline(x=0, line_dash="dash")
    fig_net_country_trade.update_layout(height=520)
    fig_net_country_trade
    return


@app.cell
def _(df_trade_long_2025):
    monthly_country_trade = (
        df_trade_long_2025
        .groupby(["Month", "Country", "Direction"], as_index=False)["MWh"]
        .sum()
    )
    monthly_country_trade["TWh"] = monthly_country_trade["MWh"] / 1e6

    monthly_total_trade = (
        df_trade_long_2025
        .groupby(["Month", "Direction"], as_index=False)["MWh"]
        .sum()
    )
    monthly_total_trade["TWh"] = monthly_total_trade["MWh"] / 1e6
    return monthly_country_trade, monthly_total_trade


@app.cell
def _(monthly_total_trade, px):
    fig_monthly_total_trade = px.bar(
        monthly_total_trade,
        x="Month",
        y="TWh",
        color="Direction",
        barmode="group",
        title="Monthly German electricity imports and exports, 2025",
        labels={"TWh": "Electricity [TWh]", "Month": "Month"},
    )
    fig_monthly_total_trade.update_layout(height=500)
    fig_monthly_total_trade
    return


@app.cell
def _(monthly_country_trade):
    monthly_country_wide = (
        monthly_country_trade
        .pivot_table(index=["Month", "Country"], columns="Direction", values="MWh", aggfunc="sum", fill_value=0)
        .reset_index()
    )
    if "Export" not in monthly_country_wide.columns:
        monthly_country_wide["Export"] = 0.0
    if "Import" not in monthly_country_wide.columns:
        monthly_country_wide["Import"] = 0.0
    monthly_country_wide["Net Export MWh"] = monthly_country_wide["Export"] - monthly_country_wide["Import"]
    monthly_country_wide["Net Export TWh"] = monthly_country_wide["Net Export MWh"] / 1e6
    monthly_country_wide["Export TWh"] = monthly_country_wide["Export"] / 1e6
    monthly_country_wide["Import TWh"] = monthly_country_wide["Import"] / 1e6
    return (monthly_country_wide,)


@app.cell
def _(monthly_country_wide, px):
    heatmap_df_trade = monthly_country_wide.pivot(index="Country", columns="Month", values="Net Export TWh").fillna(0)
    fig_trade_heatmap = px.imshow(
        heatmap_df_trade,
        aspect="auto",
        title="Monthly net electricity trade by country, 2025",
        labels={"x": "Month", "y": "Country", "color": "Net export [TWh]"},
        color_continuous_scale="RdBu",
        color_continuous_midpoint=0,
    )
    fig_trade_heatmap.update_layout(height=600)
    fig_trade_heatmap
    return


@app.cell
def _(monthly_country_wide):
    monthly_country_wide.sort_values(["Month", "Net Export TWh"], ascending=[True, False])
    return


@app.cell
def _(df_trade_2025, pd):
    daily_trade_2025 = (
        df_trade_2025
        .set_index("Start date")[["Total_Export_MWh", "Total_Import_MWh", "Net_Trade_MWh"]]
        .resample("D")
        .sum()
        .reset_index()
    )
    daily_trade_2025["Date"] = pd.to_datetime(daily_trade_2025["Start date"]).dt.normalize()
    daily_trade_2025["Export TWh"] = daily_trade_2025["Total_Export_MWh"] / 1e6
    daily_trade_2025["Import TWh"] = daily_trade_2025["Total_Import_MWh"] / 1e6
    daily_trade_2025["Net Export TWh"] = daily_trade_2025["Net_Trade_MWh"] / 1e6
    return (daily_trade_2025,)


@app.cell
def _(daily_trade_2025, px):
    fig_daily_net_trade = px.line(
        daily_trade_2025,
        x="Date",
        y="Net Export TWh",
        title="Daily net electricity trade balance, Germany 2025",
        labels={"Net Export TWh": "Net export [TWh/day]", "Date": "Date"},
    )
    fig_daily_net_trade.add_hline(y=0, line_dash="dash")
    fig_daily_net_trade.update_layout(height=480)
    fig_daily_net_trade
    return


@app.cell
def _(df_trade_2025, df_trade_long_2025, pd):
    def partner_breakdown_for_day(target_date, direction: str, top_n: int = 10):
        target_day = pd.to_datetime(target_date).date()
        subset = df_trade_long_2025[
            (df_trade_long_2025["Date"].dt.date == target_day)
            & (df_trade_long_2025["Direction"] == direction)
        ]
        out = (
            subset
            .groupby("Country", as_index=False)["MWh"]
            .sum()
            .sort_values("MWh", ascending=False)
            .head(top_n)
        )
        out["TWh"] = out["MWh"] / 1e6
        return out

    daily_extreme_table = daily_trade_extremes = pd.DataFrame({
        "Case": [
            "Highest total import day",
            "Highest total export day",
            "Strongest net import day",
            "Strongest net export day",
        ],
        "Date": [
            df_trade_2025.groupby(df_trade_2025["Start date"].dt.date)["Total_Import_MWh"].sum().idxmax(),
            df_trade_2025.groupby(df_trade_2025["Start date"].dt.date)["Total_Export_MWh"].sum().idxmax(),
            df_trade_2025.groupby(df_trade_2025["Start date"].dt.date)["Net_Trade_MWh"].sum().idxmin(),
            df_trade_2025.groupby(df_trade_2025["Start date"].dt.date)["Net_Trade_MWh"].sum().idxmax(),
        ],
    })
    return daily_extreme_table, partner_breakdown_for_day


@app.cell
def _(daily_extreme_table):
    daily_extreme_table
    return


@app.cell
def _(daily_extreme_table, partner_breakdown_for_day):
    highest_import_day = daily_extreme_table.loc[daily_extreme_table["Case"] == "Highest total import day", "Date"].iloc[0]
    highest_export_day = daily_extreme_table.loc[daily_extreme_table["Case"] == "Highest total export day", "Date"].iloc[0]

    highest_import_partner_breakdown = partner_breakdown_for_day(highest_import_day, "Import", top_n=10)
    highest_export_partner_breakdown = partner_breakdown_for_day(highest_export_day, "Export", top_n=10)
    return (
        highest_export_day,
        highest_export_partner_breakdown,
        highest_import_day,
        highest_import_partner_breakdown,
    )


@app.cell
def _(highest_import_day, highest_import_partner_breakdown, mo):
    mo.md(f"## 4. Case study: highest import day — {highest_import_day}")
    highest_import_partner_breakdown[["Country", "TWh"]]
    return


@app.cell
def _(highest_export_day, highest_export_partner_breakdown, mo):
    mo.md(f"## 5. Case study: highest export day — {highest_export_day}")
    highest_export_partner_breakdown[["Country", "TWh"]]
    return


@app.cell
def _(highest_import_partner_breakdown, px):
    fig_highest_import_day = px.bar(
        highest_import_partner_breakdown,
        x="Country",
        y="TWh",
        title="Country breakdown on Germany's highest import day",
        labels={"TWh": "Imports [TWh]"},
    )
    fig_highest_import_day.update_layout(height=450, xaxis_tickangle=-35)
    fig_highest_import_day
    return


@app.cell
def _(highest_export_partner_breakdown, px):
    fig_highest_export_day = px.bar(
        highest_export_partner_breakdown,
        x="Country",
        y="TWh",
        title="Country breakdown on Germany's highest export day",
        labels={"TWh": "Exports [TWh]"},
    )
    fig_highest_export_day.update_layout(height=450, xaxis_tickangle=-35)
    fig_highest_export_day
    return


@app.cell
def _(daily_trade_2025, mo, pd, smard_load):
    def try_load_energy_for_trade():
        try:
            energy = smard_load("cleaned_smard_2025.csv")
        except Exception:
            return None
        if "Date" not in energy.columns:
            return None
        return energy

    df_energy_for_trade = try_load_energy_for_trade()

    if df_energy_for_trade is None:
        mo.md(
            """
    ## 6. Trade vs renewable generation

    `data/cleaned/cleaned_smard_2025.csv` was not found, so this section is skipped. If the main STAGES notebook has already been run, this file should exist and the trade-vs-renewables analysis will run automatically.
    """
        )
        daily_trade_energy = None
    else:
        energy_daily_for_trade = (
            df_energy_for_trade
            .set_index("Date")[["Total_Renewable", "Grid_Load", "Residual_Load", "Renewable_Share_Pct", "Total_Wind", "Solar"]]
            .resample("D")
            .sum(numeric_only=True)
            .reset_index()
        )
        energy_daily_for_trade["Renewable Share of Load [%]"] = (
            energy_daily_for_trade["Total_Renewable"] / energy_daily_for_trade["Grid_Load"] * 100
        )
        energy_daily_for_trade["Date"] = pd.to_datetime(energy_daily_for_trade["Date"]).dt.normalize()
        daily_trade_energy = daily_trade_2025.merge(energy_daily_for_trade, on="Date", how="inner")
        mo.md(
            f"""
    ## 6. Trade vs renewable generation

    Merged daily trade with daily SMARD energy data.

    | Item | Value |
    |---|---:|
    | Daily rows | **{len(daily_trade_energy):,}** |
    | Date range | `{daily_trade_energy['Date'].min()}` → `{daily_trade_energy['Date'].max()}` |

    This lets us test whether Germany imports more during low-renewable days and exports more during high-renewable days.
    """
        )
    return (daily_trade_energy,)


@app.cell
def _(daily_trade_energy, mo):
    if daily_trade_energy is not None and len(daily_trade_energy) > 0:
        corr_net_trade_renewable_share = daily_trade_energy["Net Export TWh"].corr(daily_trade_energy["Renewable Share of Load [%]"])
        corr_net_trade_residual_load = daily_trade_energy["Net Export TWh"].corr(daily_trade_energy["Residual_Load"])
        corr_import_renewable_share = daily_trade_energy["Import TWh"].corr(daily_trade_energy["Renewable Share of Load [%]"])
        corr_export_renewable_share = daily_trade_energy["Export TWh"].corr(daily_trade_energy["Renewable Share of Load [%]"])

        mo.md(
            f"""
    ### Relationship between trade and renewables

    | Relationship | Correlation |
    |---|---:|
    | Net exports vs renewable share of load | **{corr_net_trade_renewable_share:.2f}** |
    | Net exports vs residual load | **{corr_net_trade_residual_load:.2f}** |
    | Imports vs renewable share of load | **{corr_import_renewable_share:.2f}** |
    | Exports vs renewable share of load | **{corr_export_renewable_share:.2f}** |

    Interpretation guide:

    - Positive net export vs renewable share means Germany tends to export more on high-renewable days.
    - Negative net export vs residual load means Germany tends to import more when residual load is high.
    - These are correlations, not proof of causality, but they are useful evidence for cross-border balancing.
    """
        )
    else:
        corr_net_trade_renewable_share = None
        corr_net_trade_residual_load = None
        corr_import_renewable_share = None
        corr_export_renewable_share = None
    return


@app.cell
def _(daily_trade_energy, px):
    if daily_trade_energy is not None and len(daily_trade_energy) > 0:
        fig_trade_vs_renewable_share = px.scatter(
            daily_trade_energy,
            x="Renewable Share of Load [%]",
            y="Net Export TWh",
            trendline="ols",
            title="Daily net trade vs renewable share of load, 2025",
            labels={
                "Renewable Share of Load [%]": "Renewable generation / load [%]",
                "Net Export TWh": "Net export [TWh/day]",
            },
        )
        fig_trade_vs_renewable_share.add_hline(y=0, line_dash="dash")
        fig_trade_vs_renewable_share.update_layout(height=500)
        fig_trade_vs_renewable_share
    else:
        fig_trade_vs_renewable_share = None
        fig_trade_vs_renewable_share
    return


@app.cell
def _(daily_trade_energy, px):
    if daily_trade_energy is not None and len(daily_trade_energy) > 0:
        fig_trade_vs_residual_load = px.scatter(
            daily_trade_energy,
            x="Residual_Load",
            y="Net Export TWh",
            trendline="ols",
            title="Daily net trade vs residual load, 2025",
            labels={"Residual_Load": "Daily residual load [MWh]", "Net Export TWh": "Net export [TWh/day]"},
        )
        fig_trade_vs_residual_load.add_hline(y=0, line_dash="dash")
        fig_trade_vs_residual_load.update_layout(height=500)
        fig_trade_vs_residual_load
    else:
        fig_trade_vs_residual_load = None
        fig_trade_vs_residual_load
    return


@app.cell
def _(daily_trade_energy, pd):
    if daily_trade_energy is not None and len(daily_trade_energy) > 0:
        low_renewable_threshold = daily_trade_energy["Renewable Share of Load [%]"].quantile(0.25)
        high_renewable_threshold = daily_trade_energy["Renewable Share of Load [%]"].quantile(0.75)

        low_renewable_days = daily_trade_energy[daily_trade_energy["Renewable Share of Load [%]"] <= low_renewable_threshold]
        high_renewable_days = daily_trade_energy[daily_trade_energy["Renewable Share of Load [%]"] >= high_renewable_threshold]

        renewable_trade_comparison = pd.DataFrame({
            "Group": ["Lowest 25% renewable-share days", "Highest 25% renewable-share days"],
            "Average import [TWh/day]": [low_renewable_days["Import TWh"].mean(), high_renewable_days["Import TWh"].mean()],
            "Average export [TWh/day]": [low_renewable_days["Export TWh"].mean(), high_renewable_days["Export TWh"].mean()],
            "Average net export [TWh/day]": [low_renewable_days["Net Export TWh"].mean(), high_renewable_days["Net Export TWh"].mean()],
            "Average renewable share [%]": [low_renewable_days["Renewable Share of Load [%]"].mean(), high_renewable_days["Renewable Share of Load [%]"].mean()],
        })
    else:
        renewable_trade_comparison = pd.DataFrame()
    return (renewable_trade_comparison,)


@app.cell
def _(renewable_trade_comparison):
    renewable_trade_comparison
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 7. How to interpret this trade analysis

    This section should be used carefully. Electricity imports and exports are not simply a sign of shortage or surplus. Germany is part of a European electricity market, so cross-border trade depends on:

    - renewable generation in Germany,
    - demand in Germany,
    - generation availability in neighbouring countries,
    - electricity prices,
    - grid constraints,
    - market coupling and cross-border capacity.

    A good conclusion is therefore:

    > Germany's electricity trade acts as a flexibility mechanism. During high-renewable periods Germany may export more electricity, while during low-renewable or high residual-load periods it may import more. However, imports are not automatically evidence of failure; they are also part of normal European market optimization.
    """)
    return


@app.cell
def _(
    mo,
    net_status,
    net_trade_twh,
    top_export_partner,
    top_import_partner,
    total_export_twh,
    total_import_twh,
):
    mo.md(f"""
    # Summary

    ## Main findings

    1. Germany exported **{total_export_twh:.2f} TWh** and imported **{total_import_twh:.2f} TWh** of electricity in 2025.
    2. The annual net balance was **{net_trade_twh:.2f} TWh**, meaning Germany was a **{net_status}** overall.
    3. The largest export partner was **{top_export_partner['Country']}** with **{top_export_partner['Export [TWh]']:.2f} TWh**.
    4. The largest import partner was **{top_import_partner['Country']}** with **{top_import_partner['Import [TWh]']:.2f} TWh**.
    5. Country-level trade is not symmetric: Germany can be a net exporter to some countries and a net importer from others.
    6. Monthly trade patterns help reveal when Germany relies more on imports and when it sends surplus electricity abroad.

    ## What this adds to STAGES

    This trade analysis adds a system-level perspective. It shows that answering whether renewables can cover demand is not only a domestic generation question. Germany also balances electricity through the European grid, exporting during some conditions and importing during others.
    """)
    return


if __name__ == "__main__":
    app.run()
