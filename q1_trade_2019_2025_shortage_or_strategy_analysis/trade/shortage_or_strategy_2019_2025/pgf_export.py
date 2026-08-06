"""Export the fixed STAGES thesis charts as Matplotlib PGF files.

The interactive Marimo dashboard remains in Plotly.  This module recreates the
eight static figures used by the LaTeX chapter and writes both ``.pgf`` files
and small ``.png`` previews to ``figures/``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

# Keep the notebook/browser independent from Matplotlib's GUI backends.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FIGURE_NAMES = (
    "net_balance_annual",
    "generation_mix_annual",
    "nuclear_phaseout",
    "price_2022",
    "seasonal_rhythm",
    "residual_anomaly",
    "cost_substitution",
    "renewable_share_demand",
)


def configure_pgf() -> None:
    """Configure Matplotlib for PGF files compiled with LuaLaTeX."""
    matplotlib.rcParams.update(
        {
            "pgf.texsystem": "lualatex",
            "pgf.rcfonts": False,
            "text.usetex": False,
            "font.family": "serif",
            "font.size": 9.0,
            "axes.titlesize": 10.0,
            "axes.labelsize": 9.0,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "legend.fontsize": 7.6,
            "axes.edgecolor": "#cbd5e1",
            "axes.linewidth": 0.8,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": "#e8edf3",
            "grid.linewidth": 0.7,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
        }
    )


def _finish_axis(ax: plt.Axes, *, zero_line: bool = False) -> None:
    ax.grid(axis="x", visible=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors="#64748b")
    if zero_line:
        ax.axhline(0, color="#0f172a", linewidth=0.9, zorder=3)


def _save(fig: plt.Figure, output_dir: Path, stem: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    pgf_path = output_dir / f"{stem}.pgf"
    png_path = output_dir / f"{stem}.png"
    try:
        fig.savefig(pgf_path, format="pgf", bbox_inches="tight")
    except Exception as exc:
        raise RuntimeError(
            "PGF export failed. Install LuaLaTeX and make sure the 'lualatex' "
            "command is available, then run the export again."
        ) from exc
    fig.savefig(png_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return pgf_path, png_path


def _validate(monthly: pd.DataFrame, annual: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    m = monthly.copy()
    a = annual.copy()
    m["month"] = pd.to_datetime(m["month"])
    m = m.sort_values("month").reset_index(drop=True)
    a = a.sort_values("year").reset_index(drop=True)

    monthly_required = {
        "month",
        "gen_solar",
        "gen_wind",
        "net_trade",
        "residual_load",
        "demand",
    }
    annual_required = {
        "year",
        "net_trade",
        "net_import",
        "demand",
        "gen_nuclear",
        "gen_renewables",
        "gen_gas",
        "renewable_share",
        "price",
    }
    missing_m = sorted(monthly_required - set(m.columns))
    missing_a = sorted(annual_required - set(a.columns))
    if missing_m or missing_a:
        raise ValueError(
            f"Cannot export plots. Missing monthly columns: {missing_m}; "
            f"missing annual columns: {missing_a}."
        )
    return m, a


def _net_balance_annual(annual: pd.DataFrame, colors: Mapping[str, str]) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6.7, 3.65))
    years = annual["year"].astype(int).to_numpy()
    values = annual["net_trade"].to_numpy()
    bar_colors = [colors["export"] if value > 0 else colors["import"] for value in values]
    bars = ax.bar(years, values, color=bar_colors, width=0.68)
    ax.bar_label(bars, labels=[f"{v:+.0f}" for v in values], padding=3, fontsize=8)
    ax.set_ylabel("Net balance (TWh): generation - load")
    ax.set_xticks(years)
    _finish_axis(ax, zero_line=True)
    return fig


def _generation_mix_annual(
    annual: pd.DataFrame,
    colors: Mapping[str, str],
    generation_order: Sequence[str],
    generation_labels: Mapping[str, str],
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7.05, 4.35))
    years = annual["year"].astype(int).to_numpy()
    bottom = np.zeros(len(annual))
    for source in generation_order:
        values = annual[f"gen_{source}"].fillna(0).to_numpy()
        ax.bar(
            years,
            values,
            bottom=bottom,
            width=0.72,
            color=colors[source],
            label=generation_labels[source],
        )
        bottom += values
    ax.plot(
        years,
        annual["demand"],
        color=colors["ink"],
        linewidth=1.8,
        linestyle=(0, (2, 2)),
        marker="o",
        markersize=3.6,
        label="Demand (load)",
        zorder=5,
    )
    ax.set_ylabel("TWh")
    ax.set_xticks(years)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=5, frameon=False)
    _finish_axis(ax)
    return fig


def _nuclear_phaseout(
    annual: pd.DataFrame,
    colors: Mapping[str, str],
) -> plt.Figure:
    # Extra width and panel spacing prevent the central y-axis labels
    # from overlapping.
    fig, (ax_left, ax_right) = plt.subplots(
        1,
        2,
        figsize=(8.2, 3.7),
        gridspec_kw={"wspace": 0.62},
    )

    years = annual["year"].astype(int).to_numpy()

    # Left panel: nuclear output and net balance
    ax_left.bar(
        years,
        annual["gen_nuclear"],
        color=colors["nuclear"],
        alpha=0.85,
        label="Nuclear",
    )

    ax_left.set_title("Nuclear output vs. net balance")
    ax_left.set_ylabel("Nuclear generation (TWh)", labelpad=5)
    ax_left.set_xticks(years)
    ax_left.tick_params(axis="x", rotation=45)
    _finish_axis(ax_left)

    ax_balance = ax_left.twinx()

    ax_balance.plot(
        years,
        annual["net_trade"],
        color=colors["import"],
        linewidth=1.8,
        marker="o",
        markersize=3.5,
        label="Net balance",
    )

    ax_balance.set_ylabel("Net balance (TWh)", labelpad=4)
    ax_balance.axhline(
        0,
        color=colors["ink"],
        linewidth=0.8,
    )
    ax_balance.grid(False)

    left_handles, left_labels = ax_left.get_legend_handles_labels()
    balance_handles, balance_labels = ax_balance.get_legend_handles_labels()

    ax_left.legend(
        left_handles + balance_handles,
        left_labels + balance_labels,
        loc="lower left",
        frameon=False,
    )

    # Right panel: lost nuclear output and gained renewable output
    nuclear_lost = (
        annual["gen_nuclear"].iloc[0]
        - annual["gen_nuclear"]
    )

    renewables_gained = (
        annual["gen_renewables"]
        - annual["gen_renewables"].iloc[0]
    )

    x = np.arange(len(years))
    width = 0.36

    ax_right.bar(
        x - width / 2,
        nuclear_lost,
        width,
        color=colors["nuclear"],
        alpha=0.8,
        label="Nuclear lost",
    )

    ax_right.bar(
        x + width / 2,
        renewables_gained,
        width,
        color=colors["biomass"],
        alpha=0.8,
        label="Renewables gained",
    )

    ax_right.set_title("Cumulative change since first year")
    ax_right.set_ylabel("Change (TWh)", labelpad=5)
    ax_right.set_xticks(x, years, rotation=45)

    ax_right.legend(
        loc="upper left",
        frameon=False,
    )

    _finish_axis(ax_right, zero_line=True)

    return fig


def _price_2022(annual: pd.DataFrame, colors: Mapping[str, str]) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6.7, 3.65))
    data = annual.dropna(subset=["price"])
    years = data["year"].astype(int).to_numpy()
    prices = data["price"].to_numpy()
    bar_colors = [colors["import"] if price > 150 else colors["accent"] for price in prices]
    bars = ax.bar(years, prices, color=bar_colors, width=0.68)
    ax.bar_label(bars, labels=[f"EUR {p:.0f}" for p in prices], padding=3, fontsize=8)
    ax.set_ylabel("EUR/MWh (annual average)")
    ax.set_xticks(years)
    if 2022 in years:
        y_2022 = float(data.loc[data["year"] == 2022, "price"].iloc[0])
        ax.annotate(
            "Gas-price shock",
            xy=(2022, y_2022),
            xytext=(2021.15, y_2022 * 1.13),
            color=colors["import"],
            arrowprops={"arrowstyle": "->", "color": colors["import"], "linewidth": 0.9},
        )
    _finish_axis(ax)
    return fig


def _seasonal_rhythm(
    monthly: pd.DataFrame,
    colors: Mapping[str, str],
    selected_years: Sequence[int] | None,
) -> plt.Figure:
    available_years = sorted(monthly["month"].dt.year.unique())
    if selected_years is None:
        selected_years = available_years[-3:]
    selected_years = [int(y) for y in selected_years if int(y) in available_years]
    if not selected_years:
        raise ValueError("No selected seasonal-profile years are present in the monthly data.")

    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    palette = [colors["accent"], colors["import"], colors["biomass"], colors["gas"], colors["nuclear"], colors["hydro"]]
    fig, axes = plt.subplots(3, 1, figsize=(6.7, 6.7), sharex=True)
    for index, year in enumerate(selected_years):
        data = monthly[monthly["month"].dt.year == year].copy()
        x = data["month"].dt.month.to_numpy()
        color = palette[index % len(palette)]
        axes[0].plot(x, data["gen_solar"] + data["gen_wind"], marker="o", markersize=2.8, linewidth=1.5, color=color, label=str(year))
        axes[1].plot(x, data["net_trade"], marker="o", markersize=2.8, linewidth=1.5, color=color)
        axes[2].plot(x, data["residual_load"], marker="o", markersize=2.8, linewidth=1.5, color=color)

    titles = (
        "Wind + solar generation (TWh/month)",
        "Net balance (TWh/month)",
        "Residual load (TWh/month)",
    )
    for ax, title in zip(axes, titles):
        ax.set_title(title, loc="left")
        ax.set_ylabel("TWh")
        _finish_axis(ax)
    axes[1].axhline(0, color=colors["muted"], linewidth=0.8, linestyle=(0, (2, 2)))
    axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, 1.28), ncol=len(selected_years), frameon=False)
    axes[2].set_xticks(range(1, 13), month_labels)
    return fig


def _residual_anomaly(monthly: pd.DataFrame, colors: Mapping[str, str]) -> plt.Figure:
    data = monthly.dropna(subset=["residual_load", "net_trade", "demand"]).copy()
    data["year"] = data["month"].dt.year
    data["net_imports"] = -data["net_trade"]
    data["rl_anom"] = data["residual_load"] - data.groupby("year")["residual_load"].transform("mean")
    data["ni_anom"] = data["net_imports"] - data.groupby("year")["net_imports"].transform("mean")

    fig, ax = plt.subplots(figsize=(6.7, 4.15))
    years = sorted(data["year"].unique())
    palette = plt.get_cmap("tab10")
    for index, year in enumerate(years):
        subset = data[data["year"] == year]
        ax.scatter(subset["rl_anom"], subset["ni_anom"], s=27, alpha=0.78, color=palette(index % 10), label=str(year))

    x = data["rl_anom"].to_numpy()
    y = data["ni_anom"].to_numpy()
    correlation = float(np.corrcoef(x, y)[0, 1]) if np.std(x) > 0 and np.std(y) > 0 else float("nan")
    if np.std(x) > 0:
        slope, intercept = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_line, slope * x_line + intercept, color=colors["ink"], linewidth=1.5, linestyle="--", label=f"Trend r={correlation:+.2f}")
    ax.axhline(0, color=colors["grid"], linewidth=0.9)
    ax.axvline(0, color=colors["grid"], linewidth=0.9)
    ax.set_xlabel("Residual-load anomaly (TWh vs. yearly average)")
    ax.set_ylabel("Net-import anomaly (TWh vs. yearly average)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=4, frameon=False)
    _finish_axis(ax)
    return fig


def _cost_substitution(
    annual: pd.DataFrame,
    colors: Mapping[str, str],
) -> plt.Figure:
    # Extra width and spacing prevent the central y-axis labels from overlapping.
    fig, (ax_price, ax_gas) = plt.subplots(
        1,
        2,
        figsize=(8.2, 3.7),
        gridspec_kw={"wspace": 0.65},
    )

    years = annual["year"].astype(int).to_numpy()
    x = np.arange(len(years))

    # Left panel: electricity price and net imports
    ax_price_import = ax_price.twinx()

    ax_price_import.bar(
        x,
        annual["net_import"],
        color=colors["import"],
        alpha=0.38,
        width=0.65,
        label="Net imports",
    )

    ax_price.plot(
        x,
        annual["price"],
        color=colors["gas"],
        marker="o",
        markersize=3.5,
        linewidth=1.8,
        label="German price",
    )

    ax_price.set_title("German price and net imports")
    ax_price.set_ylabel("EUR/MWh")
    ax_price_import.set_ylabel("Net imports (TWh)", labelpad=7)
    ax_price.set_xticks(x, years, rotation=45)
    ax_price_import.grid(False)

    p_handles, p_labels = ax_price.get_legend_handles_labels()
    i_handles, i_labels = ax_price_import.get_legend_handles_labels()

    ax_price.legend(
        p_handles + i_handles,
        p_labels + i_labels,
        loc="upper left",
        frameon=False,
    )

    _finish_axis(ax_price)

    # Right panel: gas generation and net imports
    ax_gas_import = ax_gas.twinx()

    ax_gas_import.bar(
        x,
        annual["net_import"],
        color=colors["import"],
        alpha=0.38,
        width=0.65,
        label="Net imports",
    )

    ax_gas.plot(
        x,
        annual["gen_gas"],
        color=colors["lignite"],
        marker="o",
        markersize=3.5,
        linewidth=1.8,
        label="Gas generation",
    )

    ax_gas.set_title("Gas generation and net imports")
    ax_gas.set_ylabel("Gas generation (TWh)", labelpad=7)
    ax_gas_import.set_ylabel("Net imports (TWh)")
    ax_gas.set_xticks(x, years, rotation=45)
    ax_gas_import.grid(False)

    g_handles, g_labels = ax_gas.get_legend_handles_labels()
    gi_handles, gi_labels = ax_gas_import.get_legend_handles_labels()

    ax_gas.legend(
        g_handles + gi_handles,
        g_labels + gi_labels,
        loc="upper left",
        frameon=False,
    )

    _finish_axis(ax_gas)

    return fig


def _renewable_share_demand(annual: pd.DataFrame, colors: Mapping[str, str]) -> plt.Figure:
    fig, (ax_share, ax_demand) = plt.subplots(1, 2, figsize=(7.05, 3.55))
    years = annual["year"].astype(int).to_numpy()

    share = annual["renewable_share"].to_numpy()
    ax_share.plot(years, share, color=colors["biomass"], linewidth=2.0, marker="o", markersize=4)
    ax_share.fill_between(years, 0, share, color=colors["biomass"], alpha=0.10)
    for year, value in zip(years, share):
        ax_share.annotate(f"{value:.0f}%", (year, value), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=7.5)
    ax_share.set_title("Renewable share of demand")
    ax_share.set_ylabel("Percent")
    ax_share.set_xticks(years)
    ax_share.tick_params(axis="x", rotation=45)
    _finish_axis(ax_share)

    demand = annual["demand"].to_numpy()
    ax_demand.plot(years, demand, color=colors["accent"], linewidth=2.0, marker="o", markersize=4)
    baseline = max(0.0, float(np.nanmin(demand)) * 0.94)
    ax_demand.fill_between(years, baseline, demand, color=colors["accent"], alpha=0.08)
    for year, value in zip(years, demand):
        ax_demand.annotate(f"{value:.0f}", (year, value), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=7.5)
    ax_demand.set_title("Total demand / load")
    ax_demand.set_ylabel("TWh")
    ax_demand.set_xticks(years)
    ax_demand.tick_params(axis="x", rotation=45)
    _finish_axis(ax_demand)
    return fig


def export_all_pgf(
    monthly: pd.DataFrame,
    annual: pd.DataFrame,
    output_dir: str | Path,
    colors: Mapping[str, str],
    generation_order: Sequence[str],
    generation_labels: Mapping[str, str],
    selected_years: Sequence[int] | None = None,
) -> list[Path]:
    """Create all eight fixed thesis plots and return their PGF paths."""
    configure_pgf()
    monthly, annual = _validate(monthly, annual)
    output = Path(output_dir)

    figures = {
        "net_balance_annual": _net_balance_annual(annual, colors),
        "generation_mix_annual": _generation_mix_annual(
            annual, colors, generation_order, generation_labels
        ),
        "nuclear_phaseout": _nuclear_phaseout(annual, colors),
        "price_2022": _price_2022(annual, colors),
        "seasonal_rhythm": _seasonal_rhythm(monthly, colors, selected_years),
        "residual_anomaly": _residual_anomaly(monthly, colors),
        "cost_substitution": _cost_substitution(annual, colors),
        "renewable_share_demand": _renewable_share_demand(annual, colors),
    }

    pgf_paths = []
    for stem, figure in figures.items():
        pgf_path, _ = _save(figure, output, stem)
        pgf_paths.append(pgf_path)
    return pgf_paths
