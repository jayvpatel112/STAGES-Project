import marimo

__generated_with = "0.23.5"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    mo.md(
        r"""
        # Q1 2025 German Electricity System — Detailed Analysis Notebook

        This notebook is a standalone analytical workspace for the first quarter of 2025. It is **not** written as a report section. The purpose is to understand the data first, inspect the behaviour of the system from several angles, and only then decide what should enter the written report.

        The working question is:

        **How much of Germany's electricity demand was met by renewable generation in Q1 2025, and when did a residual load remain for conventional generation or imports?**

        The quarter is useful because it combines winter demand, strong but variable wind generation, weak early-year solar generation, and the transition into spring. This makes it a good stress test for the renewable system before the analysis moves to the full year.

        The notebook follows the analysis path below:

        1. download and cache real hourly SMARD data;
        2. check data coverage, units, and missing values;
        3. group sources into renewable and conventional/balancing generation;
        4. compare generation with demand;
        5. quantify residual load and the net-trade proxy;
        6. inspect wind and solar separately;
        7. identify best and worst hours;
        8. optionally add representative weather context;
        9. export figures and tables for later report writing.

        No synthetic electricity data is used. If the API does not provide a required electricity series, the notebook should show that problem rather than silently inventing data.
        """
    )
    return (mo,)


@app.cell
def _():
    from pathlib import Path
    import sys

    ROOT = Path(__file__).resolve().parent
    SRC = ROOT / "src"
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))

    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    from smard_client import (
        CONVENTIONALS,
        GENERATION_SOURCES,
        PERIOD_END,
        PERIOD_START,
        RENEWABLES,
        SOURCE_FILTERS,
        TIMEZONE,
        download_q1_2025,
    )
    from energy_analysis import (
        best_renewable_hours,
        correlation_table,
        daily_summary,
        data_quality_table,
        format_report_numbers,
        headline_metrics,
        load_or_download,
        monthly_summary,
        source_totals,
        worst_residual_load_hours,
        write_analysis_outputs,
    )
    from plotting import (
        plot_case_study_worst_week,
        plot_conventional_generation,
        plot_generation_mix_donut,
        plot_generation_vs_demand,
        plot_renewable_breakdown,
        plot_renewable_generation,
        plot_renewable_share_of_demand,
        plot_residual_load_and_trade_proxy,
        plot_solar_monthly_profile,
        plot_wind_detail,
        set_house_style,
    )
    from weather_client import WEATHER_LOCATIONS, load_or_download_weather
    from weather_analysis import (
        merge_energy_weather,
        plot_weather_relationships,
        save_weather_outputs,
        weather_correlation_table,
        weather_data_quality,
        weather_monthly_summary,
        worst_shortfalls_with_weather,
    )

    RAW = ROOT / "data" / "raw"
    PROCESSED = ROOT / "data" / "processed"
    FIGURES = ROOT / "figures"
    REPORTS = ROOT / "reports"
    for folder in [RAW, PROCESSED, FIGURES, REPORTS]:
        folder.mkdir(parents=True, exist_ok=True)

    set_house_style()

    return (
        CONVENTIONALS,
        FIGURES,
        GENERATION_SOURCES,
        PERIOD_END,
        PERIOD_START,
        PROCESSED,
        RAW,
        RENEWABLES,
        REPORTS,
        SOURCE_FILTERS,
        TIMEZONE,
        WEATHER_LOCATIONS,
        best_renewable_hours,
        correlation_table,
        daily_summary,
        data_quality_table,
        download_q1_2025,
        format_report_numbers,
        headline_metrics,
        load_or_download,
        load_or_download_weather,
        merge_energy_weather,
        monthly_summary,
        mo,
        np,
        pd,
        plot_case_study_worst_week,
        plot_conventional_generation,
        plot_generation_mix_donut,
        plot_generation_vs_demand,
        plot_renewable_breakdown,
        plot_renewable_generation,
        plot_renewable_share_of_demand,
        plot_residual_load_and_trade_proxy,
        plot_solar_monthly_profile,
        plot_weather_relationships,
        plot_wind_detail,
        plt,
        save_weather_outputs,
        source_totals,
        weather_correlation_table,
        weather_data_quality,
        weather_monthly_summary,
        worst_residual_load_hours,
        worst_shortfalls_with_weather,
        write_analysis_outputs,
    )


@app.cell
def _(PERIOD_END, PERIOD_START, SOURCE_FILTERS, TIMEZONE, mo):
    source_rows = "\n".join([f"- `{filter_id}` — {name}" for name, filter_id in SOURCE_FILTERS.items()])
    mo.md(
        f"""
        ## 1. Analysis setup

        **Period:** `{PERIOD_START}` to `{PERIOD_END}`<br>
        **Timezone:** `{TIMEZONE}`<br>
        **Resolution:** hourly<br>
        **Region:** Germany<br>
        **Electricity source:** SMARD/Bundesnetzagentur chart-data API

        The notebook uses the following SMARD filter IDs:

        {source_rows}

        The values are treated as **MWh per hour**. When the values are summed over time, they become MWh; dividing by 1,000,000 gives TWh.
        """
    )
    return


@app.cell
def _(PROCESSED, RAW, download_q1_2025, load_or_download, mo):
    processed_file = PROCESSED / "q1_2025_smard_hourly.csv"
    energy_df, energy_messages = load_or_download(processed_file, RAW, download_q1_2025)

    energy_message_text = "\n".join([f"- {energy_load_message}" for energy_load_message in energy_messages])
    mo.md(
        f"""
        ## 2. Electricity data load

        Loaded **{len(energy_df):,} hourly rows**.

        - First timestamp: `{energy_df['Start date'].min()}`
        - Last timestamp: `{energy_df['Start date'].max()}`
        - Processed file: `{processed_file}`

        Load messages:

        {energy_message_text}
        """
    )
    return energy_df, energy_messages, processed_file


@app.cell
def _(energy_df):
    energy_df.head(12)
    return


@app.cell
def _(data_quality_table, energy_df, mo):
    energy_quality = data_quality_table(energy_df)
    mo.vstack(
        [
            mo.md(
                """
                ## 3. Data quality check

                Before making any interpretation, the hourly coverage has to be checked. Q1 2025 includes the spring daylight-saving transition in Europe/Berlin, so the expected number of local hourly rows is not simply 90 × 24.
                """
            ),
            mo.ui.table(energy_quality),
        ]
    )
    return (energy_quality,)


@app.cell
def _(CONVENTIONALS, RENEWABLES, mo):
    mo.md(
        f"""
        ## 4. Source grouping

        Renewable generation is grouped as:

        **{', '.join(RENEWABLES)}**

        Conventional and balancing generation is grouped as:

        **{', '.join(CONVENTIONALS)}**

        Pumped storage is kept in the conventional/balancing group because it is not a primary renewable generation source in this accounting. It mainly shifts electricity across time.
        """
    )
    return


@app.cell
def _(energy_df, headline_metrics, mo):
    headline = headline_metrics(energy_df)
    mo.vstack(
        [
            mo.md(
                """
                ## 5. Headline metrics

                The two key percentages are deliberately kept separate:

                - **renewable share of generation** tells us how much domestic production came from renewable sources;
                - **renewable share of demand** tells us how much of total electricity demand was covered by renewable generation.

                The second metric is the direct answer to the project question.
                """
            ),
            mo.ui.table(headline),
        ]
    )
    return (headline,)


@app.cell
def _(energy_df, source_totals, mo):
    source_table = source_totals(energy_df)
    mo.vstack(
        [
            mo.md(
                """
                ## 6. Source-level totals

                This table shows which technologies actually carried the quarter. It is useful because the renewable percentage alone hides whether the quarter was mainly wind-driven, solar-driven, or supported by steady sources such as biomass and hydro.
                """
            ),
            mo.ui.table(source_table),
        ]
    )
    return (source_table,)


@app.cell
def _(energy_df, monthly_summary, mo):
    monthly = monthly_summary(energy_df)
    mo.vstack(
        [
            mo.md(
                """
                ## 7. Monthly development inside Q1

                January, February, and March should not be collapsed too quickly. Solar generation changes visibly across these three months, while wind and residual load can move in the opposite direction depending on weather conditions.
                """
            ),
            mo.ui.table(monthly),
        ]
    )
    return (monthly,)


@app.cell
def _(FIGURES, energy_df, plot_renewable_generation):
    renewable_generation_fig, renewable_generation_path = plot_renewable_generation(energy_df, FIGURES)
    renewable_generation_fig
    return renewable_generation_fig, renewable_generation_path


@app.cell
def _(mo, renewable_generation_path):
    mo.md(
        f"""
        ### Renewable generation pattern

        The stacked renewable figure is saved at:

        `{renewable_generation_path}`

        Use this plot to check whether Q1 is mainly wind-led and whether solar begins to rise from winter into March.
        """
    )
    return


@app.cell
def _(FIGURES, energy_df, plot_conventional_generation):
    conventional_generation_fig, conventional_generation_path = plot_conventional_generation(energy_df, FIGURES)
    conventional_generation_fig
    return conventional_generation_fig, conventional_generation_path


@app.cell
def _(mo, conventional_generation_path):
    mo.md(
        f"""
        ### Conventional and balancing generation pattern

        The conventional/balancing figure is saved at:

        `{conventional_generation_path}`

        This plot should be read together with residual load. Conventional generation is not just a separate category; it is the part of the system that often responds when renewable output does not meet demand.
        """
    )
    return


@app.cell
def _(FIGURES, energy_df, plot_generation_vs_demand):
    generation_vs_demand_fig, generation_vs_demand_path = plot_generation_vs_demand(energy_df, FIGURES)
    generation_vs_demand_fig
    return generation_vs_demand_fig, generation_vs_demand_path


@app.cell
def _(mo):
    mo.md(
        r"""
        ## 8. Demand, generation, and the residual-load idea

        The main system quantity is **residual load**:

        \[
        \text{Residual load} = \text{Electricity demand} - \text{Renewable generation}
        \]

        When residual load is positive, renewable generation alone is not enough. The remaining gap must be supplied by conventional generation, storage discharge, demand flexibility, or imports. When residual load is negative, renewables exceed demand for that hour.
        """
    )
    return


@app.cell
def _(FIGURES, energy_df, plot_residual_load_and_trade_proxy):
    residual_trade_fig, residual_trade_path = plot_residual_load_and_trade_proxy(energy_df, FIGURES)
    residual_trade_fig
    return residual_trade_fig, residual_trade_path


@app.cell
def _(FIGURES, energy_df, plot_renewable_share_of_demand):
    renewable_share_fig, renewable_share_path = plot_renewable_share_of_demand(energy_df, FIGURES)
    renewable_share_fig
    return renewable_share_fig, renewable_share_path


@app.cell
def _(energy_df, correlation_table, mo):
    energy_correlations = correlation_table(energy_df)
    mo.vstack(
        [
            mo.md(
                """
                ## 9. First correlation checks

                These correlations are not used as final causal proof. They are diagnostic checks that help decide which relationships deserve closer inspection. In the report we should avoid overclaiming from simple correlations, especially when weather and market decisions are involved.
                """
            ),
            mo.ui.table(energy_correlations),
        ]
    )
    return (energy_correlations,)


@app.cell
def _(FIGURES, energy_df, plot_generation_mix_donut):
    generation_mix_fig, generation_mix_path = plot_generation_mix_donut(energy_df, FIGURES)
    generation_mix_fig
    return generation_mix_fig, generation_mix_path


@app.cell
def _(FIGURES, energy_df, plot_renewable_breakdown):
    renewable_breakdown_fig, renewable_breakdown_path = plot_renewable_breakdown(energy_df, FIGURES)
    renewable_breakdown_fig
    return renewable_breakdown_fig, renewable_breakdown_path


@app.cell
def _(mo):
    mo.md(
        """
        ## 10. Wind and solar as separate questions

        Wind and solar should not be discussed as if they behave the same way. In Q1, wind can dominate the renewable total, but it is volatile. Solar is lower in winter but has a strong daily cycle and should grow from January to March.
        """
    )
    return


@app.cell
def _(FIGURES, energy_df, plot_wind_detail):
    wind_detail_fig, wind_detail_path = plot_wind_detail(energy_df, FIGURES)
    wind_detail_fig
    return wind_detail_fig, wind_detail_path


@app.cell
def _(FIGURES, energy_df, plot_solar_monthly_profile):
    solar_profile_fig, solar_profile_path = plot_solar_monthly_profile(energy_df, FIGURES)
    solar_profile_fig
    return solar_profile_fig, solar_profile_path


@app.cell
def _(best_renewable_hours, energy_df, mo, worst_residual_load_hours):
    worst_hours_table = worst_residual_load_hours(energy_df, n=15)
    best_hours_table = best_renewable_hours(energy_df, n=15)
    mo.vstack(
        [
            mo.md(
                """
                ## 11. Best and worst hours

                The average quarter can hide the actual stress moments. These two tables locate the hours with the largest residual load and the hours where renewable generation covered the largest share of demand.
                """
            ),
            mo.md("### Highest residual-load hours"),
            mo.ui.table(worst_hours_table),
            mo.md("### Highest renewable-share hours"),
            mo.ui.table(best_hours_table),
        ]
    )
    return best_hours_table, worst_hours_table


@app.cell
def _(FIGURES, energy_df, plot_case_study_worst_week):
    worst_week_fig, worst_week_path = plot_case_study_worst_week(energy_df, FIGURES)
    worst_week_fig
    return worst_week_fig, worst_week_path


@app.cell
def _(format_report_numbers, energy_df, mo):
    report_numbers_text = format_report_numbers(energy_df)
    mo.vstack(
        [
            mo.md(
                """
                ## 12. Number block for later report writing

                This block is generated after the analysis tables above. It is not the report text. It is the controlled numerical source from which the Q1 report section should be written.
                """
            ),
            mo.md(f"```text\n{report_numbers_text}\n```"),
        ]
    )
    return (report_numbers_text,)


@app.cell
def _(REPORTS, energy_df, mo, write_analysis_outputs):
    analysis_output_paths = write_analysis_outputs(energy_df, REPORTS)
    analysis_output_lines = "\n".join([f"- `{analysis_output_path}`" for analysis_output_path in analysis_output_paths.values()])
    mo.md(
        f"""
        ## 13. Exported analysis tables

        The notebook has written the analysis tables and number block to:

        {analysis_output_lines}
        """
    )
    return (analysis_output_paths,)


@app.cell
def _(mo):
    weather_toggle = mo.ui.checkbox(value=True, label="Include optional Bright Sky/DWD representative weather context")
    mo.vstack(
        [
            mo.md(
                """
                ## 14. Optional weather context

                The electricity data tells us **when** renewable generation falls short. Weather indicators help explore **why** the shortfall happened: low wind speed, low sunshine, cloud cover, or temperature-driven demand.

                The weather part uses representative German locations and should be interpreted as explanatory context, not a perfect national weather model.
                """
            ),
            weather_toggle,
        ]
    )
    return (weather_toggle,)


@app.cell
def _(
    PROCESSED,
    RAW,
    WEATHER_LOCATIONS,
    load_or_download_weather,
    mo,
    pd,
    weather_toggle,
):
    weather_processed_file = PROCESSED / "q1_2025_weather_hourly_aggregated.csv"
    weather_locations_file = PROCESSED / "q1_2025_weather_locations_hourly.csv"

    if weather_toggle.value:
        try:
            weather_agg_df, weather_locations_df, weather_messages = load_or_download_weather(
                weather_processed_file,
                weather_locations_file,
                RAW,
            )
        except Exception as exc:  # noqa: BLE001
            weather_agg_df = pd.DataFrame()
            weather_locations_df = pd.DataFrame()
            weather_messages = [f"Weather data could not be loaded: {exc}"]
    else:
        weather_agg_df = pd.DataFrame()
        weather_locations_df = pd.DataFrame()
        weather_messages = ["Weather context disabled by notebook checkbox."]

    location_text = "\n".join([f"- {loc.name}: {loc.role}" for loc in WEATHER_LOCATIONS])
    weather_message_text = "\n".join([f"- {weather_load_message}" for weather_load_message in weather_messages])
    mo.md(
        f"""
        ### Weather data load

        Representative locations:

        {location_text}

        Messages:

        {message_text}
        """
    )
    return weather_agg_df, weather_locations_df, weather_messages


@app.cell
def _(mo, weather_agg_df, weather_data_quality, weather_locations_df):
    weather_quality = weather_data_quality(weather_locations_df, weather_agg_df)
    mo.vstack([mo.md("### Weather data quality"), mo.ui.table(weather_quality)])
    return (weather_quality,)


@app.cell
def _(energy_df, merge_energy_weather, weather_agg_df):
    energy_weather_df = merge_energy_weather(energy_df, weather_agg_df)
    energy_weather_df.head(10)
    return (energy_weather_df,)


@app.cell
def _(
    energy_weather_df,
    mo,
    weather_correlation_table,
    weather_monthly_summary,
    worst_shortfalls_with_weather,
):
    weather_correlations = weather_correlation_table(energy_weather_df)
    weather_monthly = weather_monthly_summary(energy_weather_df)
    weather_worst_shortfalls = worst_shortfalls_with_weather(energy_weather_df, n=15)
    mo.vstack(
        [
            mo.md("### Weather-energy relationship checks"),
            mo.ui.table(weather_correlations),
            mo.md("### Monthly weather-energy averages"),
            mo.ui.table(weather_monthly),
            mo.md("### Highest residual-load hours with weather context"),
            mo.ui.table(weather_worst_shortfalls),
        ]
    )
    return weather_correlations, weather_monthly, weather_worst_shortfalls


@app.cell
def _(FIGURES, energy_weather_df, plot_weather_relationships):
    weather_figure_paths = plot_weather_relationships(energy_weather_df, FIGURES)
    weather_figure_paths
    return (weather_figure_paths,)


@app.cell
def _(
    REPORTS,
    energy_weather_df,
    mo,
    save_weather_outputs,
    weather_agg_df,
    weather_locations_df,
):
    if not weather_agg_df.empty:
        weather_output_paths = save_weather_outputs(
            energy_weather_df,
            weather_agg_df,
            weather_locations_df,
            REPORTS,
        )
        weather_output_lines = "\n".join([f"- `{weather_output_path}`" for weather_output_path in weather_output_paths.values()])
    else:
        weather_output_paths = {}
        weather_output_lines = "- Weather outputs not written because weather data is unavailable or disabled."
    mo.md(
        f"""
        ### Exported weather-context tables

        {weather_output_lines}
        """
    )
    return (weather_output_paths,)


@app.cell
def _(mo):
    dashboard_month = mo.ui.dropdown(
        options=["All", "January", "February", "March"],
        value="All",
        label="Month",
    )
    dashboard_view = mo.ui.dropdown(
        options=["Demand vs renewables", "Residual load", "Wind and solar", "All source groups"],
        value="Demand vs renewables",
        label="View",
    )
    mo.vstack(
        [
            mo.md(
                """
                ## 15. Interactive inspection panel

                Use this panel to inspect the quarter before writing. It helps check whether a planned report statement is really visible in the data.
                """
            ),
            mo.hstack([dashboard_month, dashboard_view]),
        ]
    )
    return dashboard_month, dashboard_view


@app.cell
def _(
    CONVENTIONALS,
    RENEWABLES,
    dashboard_month,
    dashboard_view,
    energy_df,
    mo,
    plt,
):
    dashboard_df = energy_df.copy()
    if dashboard_month.value != "All":
        dashboard_df = dashboard_df[dashboard_df["Month"] == dashboard_month.value]

    daily_dash = dashboard_df.set_index("Start date").resample("D").mean(numeric_only=True).reset_index()
    dash_fig, dash_ax = plt.subplots(figsize=(13, 5.5))

    if dashboard_view.value == "Demand vs renewables":
        dash_ax.plot(daily_dash["Start date"], daily_dash["Total Load"], label="Total Load", linewidth=2)
        dash_ax.plot(daily_dash["Start date"], daily_dash["Total Renewable"], label="Total Renewable", linewidth=2)
    elif dashboard_view.value == "Residual load":
        dash_ax.plot(daily_dash["Start date"], daily_dash["Residual Load"], label="Residual Load", linewidth=2)
        dash_ax.axhline(0, color="black", linewidth=1)
    elif dashboard_view.value == "Wind and solar":
        dash_ax.plot(daily_dash["Start date"], daily_dash["Total Wind"], label="Total Wind", linewidth=2)
        dash_ax.plot(daily_dash["Start date"], daily_dash["Solar"], label="Solar", linewidth=2)
    else:
        dash_ax.plot(daily_dash["Start date"], daily_dash["Total Renewable"], label="Total Renewable", linewidth=2)
        dash_ax.plot(daily_dash["Start date"], daily_dash["Total Conventional"], label="Total Conventional", linewidth=2)
        dash_ax.plot(daily_dash["Start date"], daily_dash["Total Load"], label="Total Load", linewidth=2)

    dash_ax.set_title(f"{dashboard_view.value} — {dashboard_month.value}")
    dash_ax.set_ylabel("Daily average [MWh/h]")
    dash_ax.set_xlabel("Date")
    dash_ax.legend()
    dash_fig.tight_layout()

    total_load = dashboard_df["Total Load"].sum() / 1_000_000
    total_renewable = dashboard_df["Total Renewable"].sum() / 1_000_000
    renewable_share = total_renewable / total_load if total_load else 0

    mo.vstack(
        [
            mo.md(
                f"""
                ### Selected-period metrics

                - Demand: **{total_load:.2f} TWh**
                - Renewable generation: **{total_renewable:.2f} TWh**
                - Renewable share of demand: **{renewable_share:.1%}**
                """
            ),
            dash_fig,
        ]
    )
    return dash_fig


@app.cell
def _(
    analysis_output_paths,
    conventional_generation_path,
    generation_mix_path,
    generation_vs_demand_path,
    mo,
    renewable_breakdown_path,
    renewable_generation_path,
    renewable_share_path,
    residual_trade_path,
    solar_profile_path,
    weather_figure_paths,
    wind_detail_path,
    worst_week_path,
):
    weather_figure_lines = "\n".join([f"- `{weather_figure_path}`" for weather_figure_path in weather_figure_paths.values()]) or "- No weather figures written."
    mo.md(
        f"""
        ## 16. Files produced by the notebook

        Energy figures:

        - `{renewable_generation_path}`
        - `{conventional_generation_path}`
        - `{generation_vs_demand_path}`
        - `{generation_mix_path}`
        - `{renewable_breakdown_path}`
        - `{wind_detail_path}`
        - `{solar_profile_path}`
        - `{renewable_share_path}`
        - `{residual_trade_path}`
        - `{worst_week_path}`

        Weather figures:

        {weather_lines}

        Main numerical output:

        - `{analysis_output_paths['report_numbers']}`

        After running the notebook, open the figures and the number block. Then paste the number block into the chat so the Q1 report section can be written from verified data instead of assumptions.
        """
    )
    return


if __name__ == "__main__":
    app.run()
