from __future__ import annotations

from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from smard_client import CONVENTIONALS, GENERATION_SOURCES, PERIOD_END, PERIOD_START, RENEWABLES

TWH = 1_000_000.0


def load_or_download(processed_file: str | Path, raw_dir: str | Path, downloader: Callable) -> tuple[pd.DataFrame, list[str]]:
    processed_path = Path(processed_file)
    if processed_path.exists():
        df = pd.read_csv(processed_path, parse_dates=["Start date"])
        if df["Start date"].dt.tz is None:
            df["Start date"] = df["Start date"].dt.tz_localize("Europe/Berlin", nonexistent="shift_forward", ambiguous="NaT")
        return df, [f"Loaded processed file from {processed_path}."]

    result = downloader(raw_dir)
    df = result.dataframe
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(processed_path, index=False)
    messages = [
        f"Downloaded {result.raw_files_downloaded} SMARD JSON file(s); loaded {result.raw_files_loaded_from_cache} from cache.",
        f"Saved processed hourly data to {processed_path}.",
    ]
    messages.extend(result.warnings)
    return df, messages


def data_quality_table(df: pd.DataFrame) -> pd.DataFrame:
    expected_hours = len(pd.date_range(PERIOD_START, PERIOD_END, freq="h", inclusive="left"))
    observed_hours = len(df)
    rows = [
        {"Check": "Expected Q1 hourly rows", "Value": expected_hours},
        {"Check": "Observed rows", "Value": observed_hours},
        {"Check": "Start timestamp", "Value": str(df["Start date"].min())},
        {"Check": "End timestamp", "Value": str(df["Start date"].max())},
        {"Check": "Duplicate timestamps", "Value": int(df["Start date"].duplicated().sum())},
    ]
    for col in ["Total Load"] + GENERATION_SOURCES:
        if col in df:
            rows.append({"Check": f"Missing values — {col}", "Value": int(df[col].isna().sum())})
    return pd.DataFrame(rows)


def headline_metrics(df: pd.DataFrame) -> pd.DataFrame:
    total_load = df["Total Load"].sum() / TWH
    total_generation = df["Total Generation"].sum() / TWH
    total_renewable = df["Total Renewable"].sum() / TWH
    total_conventional = df["Total Conventional"].sum() / TWH
    renewable_share_load = total_renewable / total_load if total_load else np.nan
    renewable_share_generation = total_renewable / total_generation if total_generation else np.nan
    net_import_energy = df["Net Import Proxy"].sum() / TWH
    exportable_surplus = df["Exportable Surplus Proxy"].sum() / TWH
    net_import_hours = int((df["Net Trade Proxy"] < 0).sum())
    net_export_hours = int((df["Net Trade Proxy"] > 0).sum())
    net_balanced_hours = int((df["Net Trade Proxy"] == 0).sum())
    renewable_meet_hours = int(df["Renewables Meet Load"].sum())
    wind_solar = (df["Total Wind"].sum() + df["Solar"].sum()) / TWH
    wind_solar_share_renewables = wind_solar / total_renewable if total_renewable else np.nan

    rows = [
        ("Total demand", total_load, "TWh"),
        ("Total domestic generation", total_generation, "TWh"),
        ("Total renewable generation", total_renewable, "TWh"),
        ("Total conventional generation", total_conventional, "TWh"),
        ("Renewable share of demand", renewable_share_load * 100, "%"),
        ("Renewable share of generation", renewable_share_generation * 100, "%"),
        ("Wind plus solar share of renewables", wind_solar_share_renewables * 100, "%"),
        ("Net-import hours using generation minus load proxy", net_import_hours, "hours"),
        ("Net-export hours using generation minus load proxy", net_export_hours, "hours"),
        ("Balanced hours using generation minus load proxy", net_balanced_hours, "hours"),
        ("Net import energy using proxy", net_import_energy, "TWh"),
        ("Exportable surplus energy using proxy", exportable_surplus, "TWh"),
        ("Hours where renewables meet or exceed load", renewable_meet_hours, "hours"),
        ("Average residual load", df["Residual Load"].mean(), "MWh/h"),
        ("Maximum hourly residual load", df["Residual Load"].max(), "MWh/h"),
        ("Minimum hourly residual load", df["Residual Load"].min(), "MWh/h"),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value", "Unit"])


def source_totals(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for source in GENERATION_SOURCES:
        rows.append(
            {
                "Source": source,
                "Group": "Renewable" if source in RENEWABLES else "Conventional / balancing",
                "Generation [TWh]": df[source].sum() / TWH,
                "Share of generation [%]": df[source].sum() / df["Total Generation"].sum() * 100,
                "Share of demand [%]": df[source].sum() / df["Total Load"].sum() * 100,
            }
        )
    return pd.DataFrame(rows).sort_values("Generation [TWh]", ascending=False).reset_index(drop=True)


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby(["Month Number", "Month"], sort=True).agg(
        **{
            "Demand [TWh]": ("Total Load", lambda x: x.sum() / TWH),
            "Generation [TWh]": ("Total Generation", lambda x: x.sum() / TWH),
            "Renewables [TWh]": ("Total Renewable", lambda x: x.sum() / TWH),
            "Conventional [TWh]": ("Total Conventional", lambda x: x.sum() / TWH),
            "Wind [TWh]": ("Total Wind", lambda x: x.sum() / TWH),
            "Solar [TWh]": ("Solar", lambda x: x.sum() / TWH),
            "Average residual load [MWh/h]": ("Residual Load", "mean"),
            "Net import proxy [TWh]": ("Net Import Proxy", lambda x: x.sum() / TWH),
            "Exportable surplus proxy [TWh]": ("Exportable Surplus Proxy", lambda x: x.sum() / TWH),
            "Renewables meet load [hours]": ("Renewables Meet Load", "sum"),
        }
    )
    grouped = grouped.reset_index()
    grouped["Renewable share of demand [%]"] = grouped["Renewables [TWh]"] / grouped["Demand [TWh]"] * 100
    grouped["Renewable share of generation [%]"] = grouped["Renewables [TWh]"] / grouped["Generation [TWh]"] * 100
    return grouped.drop(columns=["Month Number"])


def daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    daily = df.set_index("Start date").resample("D").agg(
        {
            "Total Load": "mean",
            "Total Generation": "mean",
            "Total Renewable": "mean",
            "Total Conventional": "mean",
            "Total Wind": "mean",
            "Solar": "mean",
            "Residual Load": "mean",
            "Renewable Share of Load": "mean",
            "Net Import Proxy": "sum",
            "Exportable Surplus Proxy": "sum",
        }
    )
    daily = daily.rename(
        columns={
            "Total Load": "Average load [MWh/h]",
            "Total Generation": "Average generation [MWh/h]",
            "Total Renewable": "Average renewable generation [MWh/h]",
            "Total Conventional": "Average conventional generation [MWh/h]",
            "Total Wind": "Average wind generation [MWh/h]",
            "Solar": "Average solar generation [MWh/h]",
            "Residual Load": "Average residual load [MWh/h]",
            "Renewable Share of Load": "Average renewable share of demand",
            "Net Import Proxy": "Daily net import proxy [MWh]",
            "Exportable Surplus Proxy": "Daily exportable surplus proxy [MWh]",
        }
    )
    daily["Date"] = daily.index.date
    return daily.reset_index(drop=True)


def worst_residual_load_hours(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    cols = [
        "Start date",
        "Total Load",
        "Total Renewable",
        "Total Wind",
        "Solar",
        "Total Conventional",
        "Residual Load",
        "Net Import Proxy",
        "Renewable Share of Load",
    ]
    out = df.nlargest(n, "Residual Load")[cols].copy()
    out["Renewable Share of Load"] *= 100
    return out.reset_index(drop=True)


def best_renewable_hours(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    cols = [
        "Start date",
        "Total Load",
        "Total Renewable",
        "Total Wind",
        "Solar",
        "Residual Load",
        "Exportable Surplus Proxy",
        "Renewable Share of Load",
    ]
    out = df.nlargest(n, "Renewable Share of Load")[cols].copy()
    out["Renewable Share of Load"] *= 100
    return out.reset_index(drop=True)


def correlation_table(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "Total Load",
        "Total Renewable",
        "Total Wind",
        "Solar",
        "Total Conventional",
        "Residual Load",
        "Net Import Proxy",
        "Renewable Share of Load",
    ]
    corr = df[cols].corr(numeric_only=True)
    pairs = [
        ("Wind generation vs residual load", "Total Wind", "Residual Load"),
        ("Solar generation vs residual load", "Solar", "Residual Load"),
        ("Renewables vs conventional generation", "Total Renewable", "Total Conventional"),
        ("Residual load vs import proxy", "Residual Load", "Net Import Proxy"),
        ("Load vs residual load", "Total Load", "Residual Load"),
    ]
    return pd.DataFrame(
        [{"Relationship": label, "Correlation r": corr.loc[a, b]} for label, a, b in pairs]
    )


def format_report_numbers(df: pd.DataFrame) -> str:
    metrics = headline_metrics(df)
    sources = source_totals(df)
    monthly = monthly_summary(df)

    def metric_value(name: str) -> float:
        return float(metrics.loc[metrics["Metric"] == name, "Value"].iloc[0])

    lines = [
        "REPORT NUMBERS — Q1 2025 Germany electricity system",
        "====================================================",
        f"Time period: {df['Start date'].min()} to {df['Start date'].max()}",
        f"Hourly rows: {len(df):,}",
        "",
        "Headline totals",
        f"Total demand: {metric_value('Total demand'):.2f} TWh",
        f"Total domestic generation: {metric_value('Total domestic generation'):.2f} TWh",
        f"Total renewable generation: {metric_value('Total renewable generation'):.2f} TWh",
        f"Total conventional generation: {metric_value('Total conventional generation'):.2f} TWh",
        f"Renewable share of demand: {metric_value('Renewable share of demand'):.1f}%",
        f"Renewable share of generation: {metric_value('Renewable share of generation'):.1f}%",
        f"Wind + solar share of renewables: {metric_value('Wind plus solar share of renewables'):.1f}%",
        "",
        "Net trade proxy: total generation minus total load",
        f"Net-import hours: {metric_value('Net-import hours using generation minus load proxy'):.0f}",
        f"Net-export hours: {metric_value('Net-export hours using generation minus load proxy'):.0f}",
        f"Net import energy: {metric_value('Net import energy using proxy'):.2f} TWh",
        f"Exportable surplus energy: {metric_value('Exportable surplus energy using proxy'):.2f} TWh",
        "",
        "Residual load",
        f"Average residual load: {metric_value('Average residual load'):.0f} MWh/h",
        f"Maximum hourly residual load: {metric_value('Maximum hourly residual load'):.0f} MWh/h",
        f"Minimum hourly residual load: {metric_value('Minimum hourly residual load'):.0f} MWh/h",
        "",
        "Per-source generation totals",
    ]
    for _, row in sources.iterrows():
        lines.append(f"{row['Source']}: {row['Generation [TWh]']:.2f} TWh")

    lines.extend(["", "Monthly solar totals"])
    for _, row in monthly.iterrows():
        lines.append(f"{row['Month']}: {row['Solar [TWh]']:.2f} TWh")

    lines.extend(["", "Monthly renewable share of demand"])
    for _, row in monthly.iterrows():
        lines.append(f"{row['Month']}: {row['Renewable share of demand [%]']:.1f}%")

    return "\n".join(lines)


def write_analysis_outputs(df: pd.DataFrame, reports_dir: str | Path) -> dict[str, Path]:
    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)

    outputs = {
        "headline_metrics": reports / "q1_2025_headline_metrics.csv",
        "source_totals": reports / "q1_2025_source_totals.csv",
        "monthly_summary": reports / "q1_2025_monthly_summary.csv",
        "daily_summary": reports / "q1_2025_daily_summary.csv",
        "worst_residual_load_hours": reports / "q1_2025_worst_residual_load_hours.csv",
        "best_renewable_hours": reports / "q1_2025_best_renewable_hours.csv",
        "correlations": reports / "q1_2025_energy_correlations.csv",
        "report_numbers": reports / "q1_2025_report_numbers.txt",
    }

    headline_metrics(df).to_csv(outputs["headline_metrics"], index=False)
    source_totals(df).to_csv(outputs["source_totals"], index=False)
    monthly_summary(df).to_csv(outputs["monthly_summary"], index=False)
    daily_summary(df).to_csv(outputs["daily_summary"], index=False)
    worst_residual_load_hours(df).to_csv(outputs["worst_residual_load_hours"], index=False)
    best_renewable_hours(df).to_csv(outputs["best_renewable_hours"], index=False)
    correlation_table(df).to_csv(outputs["correlations"], index=False)
    outputs["report_numbers"].write_text(format_report_numbers(df), encoding="utf-8")
    return outputs
