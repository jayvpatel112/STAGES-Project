from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


def merge_energy_weather(energy_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    if weather_df.empty:
        return energy_df.copy()
    return energy_df.merge(weather_df, on="Start date", how="left")


def weather_data_quality(locations_df: pd.DataFrame, aggregated_df: pd.DataFrame) -> pd.DataFrame:
    if locations_df.empty or aggregated_df.empty:
        return pd.DataFrame([{"Check": "Weather data", "Value": "Not available"}])
    rows = [
        {"Check": "Location-level rows", "Value": len(locations_df)},
        {"Check": "Aggregated hourly rows", "Value": len(aggregated_df)},
        {"Check": "Locations", "Value": locations_df["Location"].nunique()},
        {"Check": "Start timestamp", "Value": str(aggregated_df["Start date"].min())},
        {"Check": "End timestamp", "Value": str(aggregated_df["Start date"].max())},
    ]
    for col in [c for c in aggregated_df.columns if c.startswith("Weather")]:
        rows.append({"Check": f"Missing values — {col}", "Value": int(aggregated_df[col].isna().sum())})
    return pd.DataFrame(rows)


def weather_correlation_table(df: pd.DataFrame) -> pd.DataFrame:
    needed = [
        "Total Wind",
        "Solar",
        "Total Load",
        "Residual Load",
        "Weather Wind Speed [km/h]",
        "Weather Sunshine [min]",
        "Weather Temperature [C]",
        "Weather Cloud Cover [%]",
    ]
    if any(col not in df for col in needed):
        return pd.DataFrame([{"Relationship": "Weather correlations", "Correlation r": None, "Note": "Weather columns unavailable"}])
    pairs = [
        ("Wind generation vs representative wind speed", "Total Wind", "Weather Wind Speed [km/h]"),
        ("Solar generation vs representative sunshine", "Solar", "Weather Sunshine [min]"),
        ("Solar generation vs cloud cover", "Solar", "Weather Cloud Cover [%]"),
        ("Load vs representative temperature", "Total Load", "Weather Temperature [C]"),
        ("Residual load vs representative wind speed", "Residual Load", "Weather Wind Speed [km/h]"),
        ("Residual load vs representative sunshine", "Residual Load", "Weather Sunshine [min]"),
    ]
    corr = df[[a for _, a, _ in pairs] + [b for _, _, b in pairs]].corr(numeric_only=True)
    return pd.DataFrame([{"Relationship": label, "Correlation r": corr.loc[a, b]} for label, a, b in pairs])


def weather_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    weather_cols = [c for c in df.columns if c.startswith("Weather")]
    if not weather_cols:
        return pd.DataFrame()
    return df.groupby("Month", sort=False)[weather_cols + ["Total Wind", "Solar", "Total Load", "Residual Load"]].mean().reset_index()


def worst_shortfalls_with_weather(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    cols = [
        "Start date",
        "Total Load",
        "Total Renewable",
        "Total Wind",
        "Solar",
        "Residual Load",
        "Weather Wind Speed [km/h]",
        "Weather Sunshine [min]",
        "Weather Temperature [C]",
        "Weather Cloud Cover [%]",
    ]
    cols = [c for c in cols if c in df.columns]
    return df.nlargest(n, "Residual Load")[cols].reset_index(drop=True)


def save_weather_outputs(df: pd.DataFrame, weather_agg: pd.DataFrame, weather_locations: pd.DataFrame, reports_dir: str | Path) -> dict[str, Path]:
    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    outputs = {
        "weather_correlations": reports / "q1_2025_weather_correlations.csv",
        "weather_monthly_summary": reports / "q1_2025_weather_monthly_summary.csv",
        "worst_shortfalls_with_weather": reports / "q1_2025_worst_shortfalls_with_weather.csv",
        "weather_aggregated": reports / "q1_2025_weather_aggregated_preview.csv",
        "weather_locations": reports / "q1_2025_weather_locations_preview.csv",
    }
    weather_correlation_table(df).to_csv(outputs["weather_correlations"], index=False)
    weather_monthly_summary(df).to_csv(outputs["weather_monthly_summary"], index=False)
    worst_shortfalls_with_weather(df).to_csv(outputs["worst_shortfalls_with_weather"], index=False)
    weather_agg.head(200).to_csv(outputs["weather_aggregated"], index=False)
    weather_locations.head(200).to_csv(outputs["weather_locations"], index=False)
    return outputs


def _save(fig, figures_dir: str | Path, filename: str):
    path = Path(figures_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    return fig, path


def _format_date_axis(ax) -> None:
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.tick_params(axis="x", rotation=30)


def plot_weather_relationships(df: pd.DataFrame, figures_dir: str | Path) -> dict[str, Path]:
    outputs: dict[str, Path] = {}
    if "Weather Wind Speed [km/h]" not in df:
        return outputs

    daily = df.set_index("Start date").resample("D").mean(numeric_only=True).reset_index()

    fig, ax1 = plt.subplots(figsize=(13, 5.8))
    ax1.plot(daily["Start date"], daily["Total Wind"], label="Wind generation", linewidth=2.0)
    ax1.set_ylabel("Wind generation [MWh/h]")
    ax2 = ax1.twinx()
    ax2.plot(daily["Start date"], daily["Weather Wind Speed [km/h]"], linestyle="--", label="Wind speed", linewidth=1.8)
    ax2.set_ylabel("Wind speed [km/h]")
    ax1.set_title("Daily wind generation and representative wind speed, Q1 2025")
    _format_date_axis(ax1)
    fig.tight_layout()
    _, outputs["weather_wind"] = _save(fig, figures_dir, "q1_weather_wind_generation_speed.png")

    fig, ax1 = plt.subplots(figsize=(13, 5.8))
    ax1.plot(daily["Start date"], daily["Solar"], label="Solar generation", linewidth=2.0)
    ax1.set_ylabel("Solar generation [MWh/h]")
    ax2 = ax1.twinx()
    ax2.plot(daily["Start date"], daily["Weather Sunshine [min]"], linestyle="--", label="Sunshine", linewidth=1.8)
    ax2.set_ylabel("Sunshine [min/h]")
    ax1.set_title("Daily solar generation and representative sunshine, Q1 2025")
    _format_date_axis(ax1)
    fig.tight_layout()
    _, outputs["weather_solar"] = _save(fig, figures_dir, "q1_weather_solar_sunshine.png")

    fig, ax1 = plt.subplots(figsize=(13, 5.8))
    ax1.plot(daily["Start date"], daily["Total Load"], label="Electricity demand", linewidth=2.0)
    ax1.set_ylabel("Load [MWh/h]")
    ax2 = ax1.twinx()
    ax2.plot(daily["Start date"], daily["Weather Temperature [C]"], linestyle="--", label="Temperature", linewidth=1.8)
    ax2.set_ylabel("Temperature [°C]")
    ax1.set_title("Daily electricity demand and representative temperature, Q1 2025")
    _format_date_axis(ax1)
    fig.tight_layout()
    _, outputs["weather_temperature_load"] = _save(fig, figures_dir, "q1_weather_temperature_load.png")

    return outputs
