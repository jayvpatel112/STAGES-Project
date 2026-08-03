from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from smard_client import CONVENTIONALS, RENEWABLES

COLORS = {
    "Wind Onshore": "#2E86AB",
    "Wind Offshore": "#5DADE2",
    "Solar": "#F4D03F",
    "Hydro": "#2874A6",
    "Biomass": "#52BE80",
    "Other Renewable": "#A9DFBF",
    "Lignite": "#8E6E53",
    "Hard Coal": "#4D5656",
    "Fossil Gas": "#AF7AC5",
    "Nuclear": "#D7BDE2",
    "Other Conventional": "#95A5A6",
    "Pumped Storage": "#85C1E9",
    "Total Load": "#1B2631",
    "Total Generation": "#7D3C98",
    "Total Renewable": "#148F77",
    "Total Conventional": "#B03A2E",
    "Residual Load": "#C0392B",
    "Net Import Proxy": "#A93226",
    "Exportable Surplus Proxy": "#117A65",
}


def set_house_style() -> None:
    plt.rcParams.update(
        {
            "figure.figsize": (12, 5.8),
            "figure.dpi": 120,
            "savefig.dpi": 200,
            "axes.grid": True,
            "grid.alpha": 0.28,
            "grid.linewidth": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titlesize": 13,
            "axes.titleweight": "semibold",
            "axes.labelsize": 11,
            "legend.frameon": False,
            "font.size": 10,
        }
    )


def _save(fig, figures_dir: str | Path, filename: str):
    path = Path(figures_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    return fig, path


def _format_date_axis(ax) -> None:
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.tick_params(axis="x", rotation=30)


def _daily_mean(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    return df.set_index("Start date")[list(cols)].resample("D").mean()


def plot_renewable_generation(df: pd.DataFrame, figures_dir: str | Path):
    daily = _daily_mean(df, RENEWABLES)
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.stackplot(
        daily.index,
        [daily[col] for col in RENEWABLES],
        labels=RENEWABLES,
        colors=[COLORS[col] for col in RENEWABLES],
        alpha=0.92,
    )
    ax.set_title("Renewable electricity generation by source, Q1 2025")
    ax.set_ylabel("Daily average generation [MWh/h]")
    ax.set_xlabel("Date")
    _format_date_axis(ax)
    ax.legend(loc="upper left", ncol=3)
    fig.tight_layout()
    return _save(fig, figures_dir, "q1_renewable_generation.png")


def plot_conventional_generation(df: pd.DataFrame, figures_dir: str | Path):
    daily = _daily_mean(df, CONVENTIONALS)
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.stackplot(
        daily.index,
        [daily[col] for col in CONVENTIONALS],
        labels=CONVENTIONALS,
        colors=[COLORS[col] for col in CONVENTIONALS],
        alpha=0.92,
    )
    ax.set_title("Conventional and balancing generation by source, Q1 2025")
    ax.set_ylabel("Daily average generation [MWh/h]")
    ax.set_xlabel("Date")
    _format_date_axis(ax)
    ax.legend(loc="upper left", ncol=3)
    fig.tight_layout()
    return _save(fig, figures_dir, "q1_conventional_generation.png")


def plot_generation_vs_demand(df: pd.DataFrame, figures_dir: str | Path):
    daily = _daily_mean(df, ["Total Load", "Total Generation", "Total Renewable", "Total Conventional"])
    fig, ax = plt.subplots(figsize=(13, 6))
    for col in ["Total Load", "Total Generation", "Total Renewable", "Total Conventional"]:
        ax.plot(daily.index, daily[col], label=col, linewidth=2.0, color=COLORS[col])
    ax.set_title("Generation and electricity demand, Q1 2025")
    ax.set_ylabel("Daily average [MWh/h]")
    ax.set_xlabel("Date")
    _format_date_axis(ax)
    ax.legend(loc="upper left", ncol=2)
    fig.tight_layout()
    return _save(fig, figures_dir, "q1_generation_vs_demand.png")


def plot_generation_mix_donut(df: pd.DataFrame, figures_dir: str | Path):
    totals = df[RENEWABLES + CONVENTIONALS].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 7))
    colors = [COLORS.get(src, None) for src in totals.index]
    wedges, texts, autotexts = ax.pie(
        totals.values,
        labels=totals.index,
        colors=colors,
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 3 else "",
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.42, "edgecolor": "white"},
        pctdistance=0.78,
        labeldistance=1.08,
    )
    ax.set_title("Electricity generation mix by source, Q1 2025")
    ax.text(0, 0, f"{totals.sum()/1_000_000:.1f}\nTWh", ha="center", va="center", fontsize=13, weight="semibold")
    fig.tight_layout()
    return _save(fig, figures_dir, "q1_generation_mix.png")


def plot_renewable_breakdown(df: pd.DataFrame, figures_dir: str | Path):
    totals = (df[RENEWABLES].sum() / 1_000_000).sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.barh(totals.index, totals.values, color=[COLORS[col] for col in totals.index])
    ax.set_title("Renewable generation totals by source, Q1 2025")
    ax.set_xlabel("Generation [TWh]")
    for i, value in enumerate(totals.values):
        ax.text(value, i, f" {value:.2f}", va="center")
    fig.tight_layout()
    return _save(fig, figures_dir, "q1_renewable_breakdown.png")


def plot_wind_detail(df: pd.DataFrame, figures_dir: str | Path):
    hourly = df.set_index("Start date")[["Wind Onshore", "Wind Offshore", "Total Wind", "Total Load"]]
    daily = hourly.resample("D").mean()
    rolling = hourly["Total Wind"].rolling(24, min_periods=6).mean()

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(hourly.index, rolling, label="Total wind, 24-hour rolling mean", color=COLORS["Total Renewable"], linewidth=1.7)
    ax.plot(daily.index, daily["Wind Onshore"], label="Wind Onshore, daily average", color=COLORS["Wind Onshore"], linewidth=1.8)
    ax.plot(daily.index, daily["Wind Offshore"], label="Wind Offshore, daily average", color=COLORS["Wind Offshore"], linewidth=1.8)
    ax.set_title("Wind generation variability, Q1 2025")
    ax.set_ylabel("Generation [MWh/h]")
    ax.set_xlabel("Date")
    _format_date_axis(ax)
    ax.legend(loc="upper left")
    fig.tight_layout()
    return _save(fig, figures_dir, "q1_wind_detail.png")


def plot_solar_monthly_profile(df: pd.DataFrame, figures_dir: str | Path):
    profile = df.groupby(["Month", "Hour"], sort=False)["Solar"].mean().reset_index()
    month_order = ["January", "February", "March"]
    fig, ax = plt.subplots(figsize=(11, 6))
    for month in month_order:
        subset = profile[profile["Month"] == month]
        if subset.empty:
            continue
        ax.plot(subset["Hour"], subset["Solar"], label=month, linewidth=2.2)
    ax.set_title("Average hourly solar generation by month, Q1 2025")
    ax.set_ylabel("Average solar generation [MWh/h]")
    ax.set_xlabel("Hour of day")
    ax.set_xticks(range(0, 24, 2))
    ax.legend(title="Month")
    fig.tight_layout()
    return _save(fig, figures_dir, "q1_solar_monthly_profile.png")


def plot_renewable_share_of_demand(df: pd.DataFrame, figures_dir: str | Path):
    daily = _daily_mean(df, ["Renewable Share of Load"])
    fig, ax = plt.subplots(figsize=(13, 5.8))
    ax.plot(daily.index, daily["Renewable Share of Load"] * 100, color=COLORS["Total Renewable"], linewidth=2.0)
    ax.axhline(100, linestyle="--", linewidth=1.2, color="black", label="100% of demand")
    ax.set_title("Daily renewable share of electricity demand, Q1 2025")
    ax.set_ylabel("Renewable share of demand [%]")
    ax.set_xlabel("Date")
    ax.set_ylim(bottom=0)
    _format_date_axis(ax)
    ax.legend(loc="upper left")
    fig.tight_layout()
    return _save(fig, figures_dir, "q1_renewable_share_of_demand.png")


def plot_residual_load_and_trade_proxy(df: pd.DataFrame, figures_dir: str | Path):
    daily = df.set_index("Start date")[["Residual Load", "Net Import Proxy", "Exportable Surplus Proxy"]].resample("D").mean()
    fig, ax = plt.subplots(figsize=(13, 5.8))
    ax.plot(daily.index, daily["Residual Load"], color=COLORS["Residual Load"], linewidth=2.0, label="Residual load")
    ax.fill_between(daily.index, 0, daily["Net Import Proxy"], color=COLORS["Net Import Proxy"], alpha=0.25, label="Import proxy")
    ax.fill_between(daily.index, 0, -daily["Exportable Surplus Proxy"], color=COLORS["Exportable Surplus Proxy"], alpha=0.25, label="Exportable surplus proxy")
    ax.axhline(0, color="black", linewidth=1.0)
    ax.set_title("Residual load and net-trade proxy, Q1 2025")
    ax.set_ylabel("Daily average [MWh/h]")
    ax.set_xlabel("Date")
    _format_date_axis(ax)
    ax.legend(loc="upper left")
    fig.tight_layout()
    return _save(fig, figures_dir, "q1_residual_load_trade_proxy.png")


def plot_case_study_worst_week(df: pd.DataFrame, figures_dir: str | Path):
    worst_day = df.groupby("Date")["Residual Load"].mean().idxmax()
    start = pd.Timestamp(worst_day, tz="Europe/Berlin") - pd.Timedelta(days=3)
    end = pd.Timestamp(worst_day, tz="Europe/Berlin") + pd.Timedelta(days=4)
    case = df[(df["Start date"] >= start) & (df["Start date"] < end)].copy()
    if case.empty:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.text(0.5, 0.5, "No case-study data available", ha="center", va="center")
        return _save(fig, figures_dir, "q1_worst_residual_load_week.png")
    fig, ax = plt.subplots(figsize=(13, 6))
    for col in ["Total Load", "Total Renewable", "Total Conventional", "Residual Load"]:
        ax.plot(case["Start date"], case[col], label=col, color=COLORS.get(col), linewidth=1.8)
    ax.axhline(0, color="black", linewidth=1.0)
    ax.set_title(f"Highest-residual-load week around {worst_day}, Q1 2025")
    ax.set_ylabel("MWh/h")
    ax.set_xlabel("Date")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%H:%M"))
    ax.legend(loc="upper left", ncol=2)
    fig.tight_layout()
    return _save(fig, figures_dir, "q1_worst_residual_load_week.png")


def plot_all_energy_figures(df: pd.DataFrame, figures_dir: str | Path) -> dict[str, Path]:
    set_house_style()
    plotters = {
        "renewable_generation": plot_renewable_generation,
        "conventional_generation": plot_conventional_generation,
        "generation_vs_demand": plot_generation_vs_demand,
        "generation_mix": plot_generation_mix_donut,
        "renewable_breakdown": plot_renewable_breakdown,
        "wind_detail": plot_wind_detail,
        "solar_monthly_profile": plot_solar_monthly_profile,
        "renewable_share_of_demand": plot_renewable_share_of_demand,
        "residual_load_trade_proxy": plot_residual_load_and_trade_proxy,
        "worst_residual_load_week": plot_case_study_worst_week,
    }
    outputs: dict[str, Path] = {}
    for name, plotter in plotters.items():
        fig, path = plotter(df, figures_dir)
        outputs[name] = path
    return outputs
