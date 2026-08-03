"""Smoke-test the nine PGF figure types without downloading API data.

Run ``python validate_pgf_export.py``.  The script builds representative
Matplotlib figures in a temporary directory and, when LuaLaTeX is installed,
imports all nine PGF files into one test PDF.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pgf_export import save_png_and_pgf


NAMES = [
    "trade_01_annual_net_balance.png",
    "trade_02_gross_imp_exp.png",
    "trade_03_stacked_by_neighbour.png",
    "trade_04_partners_imp_exp.png",
    "trade_05_net_per_neighbour.png",
    "trade_06_heatmap.png",
    "trade_07_monthly_seasonal.png",
    "trade_08_month_year_heatmap.png",
    "trade_09_relationship_evolution.png",
]


def build_representative_figures(output_dir: Path) -> list[Path]:
    years = np.arange(2019, 2026)
    x = np.arange(len(years))
    values = np.array([35.0, 22.0, 12.0, 3.0, -11.0, -24.0, -18.0])
    countries = ["France", "Netherlands", "Austria", "Denmark"]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(years, values, color=["#2563eb" if v >= 0 else "#ef4444" for v in values])
    ax.set_title("Annual net electricity balance — Germany, 2019 to 2025")
    ax.set_ylabel("Net balance (TWh)   +export / -import")
    save_png_and_pgf(fig, NAMES[0], output_dir)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - 0.2, np.linspace(55, 32, 7), 0.4, label="Gross exports")
    ax.bar(x + 0.2, np.linspace(25, 50, 7), 0.4, label="Gross imports")
    ax.set_xticks(x, years)
    ax.legend()
    save_png_and_pgf(fig, NAMES[1], output_dir)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.6))
    bottom = np.zeros(7)
    for index, country in enumerate(countries):
        series = np.sin(x / 2 + index) * (8 - index)
        ax.bar(years, series, bottom=bottom, label=country)
        bottom += series
    ax.legend()
    save_png_and_pgf(fig, NAMES[2], output_dir)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.6))
    y = np.arange(len(countries))
    ax.barh(y - 0.2, [42, 31, 22, 17], 0.4, label="Exports to")
    ax.barh(y + 0.2, [55, 48, 19, 20], 0.4, label="Imports from")
    ax.set_yticks(y, countries)
    ax.legend()
    save_png_and_pgf(fig, NAMES[3], output_dir)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.barh(countries, [-18, -7, 4, 11])
    ax.axvline(0, color="black")
    save_png_and_pgf(fig, NAMES[4], output_dir)
    plt.close(fig)

    matrix = np.linspace(-15, 15, 28).reshape(4, 7)
    fig, (ax, cax) = plt.subplots(
        1, 2, figsize=(10.5, 5.6),
        gridspec_kw={"width_ratios": [32, 1], "wspace": 0.08},
    )
    mesh = ax.pcolormesh(
        np.arange(8) - 0.5, np.arange(5) - 0.5, matrix,
        cmap="RdBu", vmin=-15, vmax=15, shading="flat",
    )
    ax.set_xticks(x, years)
    ax.set_yticks(np.arange(4), countries)
    ax.set_ylim(3.5, -0.5)
    colour_edges = np.linspace(-15, 15, 65)
    colour_centres = (colour_edges[:-1] + colour_edges[1:]) / 2
    cax.barh(
        colour_centres, np.ones_like(colour_centres),
        height=(colour_edges[1] - colour_edges[0]) * 1.02,
        color=plt.get_cmap("RdBu")((colour_centres + 15) / 30),
        edgecolor="none",
    )
    cax.set_xlim(0, 1)
    cax.set_ylim(-15, 15)
    cax.set_xticks([])
    cax.yaxis.tick_right()
    cax.grid(False)
    save_png_and_pgf(fig, NAMES[5], output_dir)
    plt.close(fig)

    dates = pd.date_range("2019-01-01", periods=84, freq="MS")
    monthly = np.sin(np.arange(84) / 5) * 3 - np.linspace(-2, 2, 84)
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.fill_between(dates, monthly, 0, where=monthly >= 0, color="#2563eb")
    ax.fill_between(dates, monthly, 0, where=monthly < 0, color="#ef4444")
    save_png_and_pgf(fig, NAMES[6], output_dir)
    plt.close(fig)

    month_matrix = np.sin(np.arange(84).reshape(12, 7) / 6)
    fig, (ax, cax) = plt.subplots(
        1, 2, figsize=(10.5, 5.4),
        gridspec_kw={"width_ratios": [32, 1], "wspace": 0.08},
    )
    mesh = ax.pcolormesh(
        np.arange(8) - 0.5, np.arange(13) - 0.5, month_matrix,
        cmap="RdBu", vmin=-1, vmax=1, shading="flat",
    )
    ax.set_xticks(x, years)
    ax.set_yticks(np.arange(12), [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ])
    ax.set_ylim(11.5, -0.5)
    colour_edges = np.linspace(-1, 1, 65)
    colour_centres = (colour_edges[:-1] + colour_edges[1:]) / 2
    cax.barh(
        colour_centres, np.ones_like(colour_centres),
        height=(colour_edges[1] - colour_edges[0]) * 1.02,
        color=plt.get_cmap("RdBu")((colour_centres + 1) / 2),
        edgecolor="none",
    )
    cax.set_xlim(0, 1)
    cax.set_ylim(-1, 1)
    cax.set_xticks([])
    cax.yaxis.tick_right()
    cax.grid(False)
    save_png_and_pgf(fig, NAMES[7], output_dir)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 6))
    for index, country in enumerate(countries):
        ax.plot(years, np.sin(x / 2 + index) * 10, marker="o", label=country)
    ax.set_title("Evolution of each trading relationship, 2019 to 2025")
    ax.legend()
    save_png_and_pgf(fig, NAMES[8], output_dir)
    plt.close(fig)

    return [output_dir / Path(name).with_suffix(".pgf") for name in NAMES]


def compile_lualatex(pgf_files: list[Path], output_dir: Path) -> None:
    if shutil.which("lualatex") is None:
        print("Created nine PGF files; LuaLaTeX is not installed, so import testing was skipped.")
        return

    inputs = "\n".join(
        rf"\resizebox{{\textwidth}}{{!}}{{\input{{{path.name}}}}}\par\clearpage"
        for path in pgf_files
    )
    tex = (
        r"\documentclass{article}" "\n"
        r"\usepackage{graphicx}" "\n"
        r"\usepackage{pgf}" "\n"
        r"\begin{document}" "\n"
        + inputs + "\n"
        + r"\end{document}" "\n"
    )
    tex_path = output_dir / "pgf_import_test.tex"
    tex_path.write_text(tex, encoding="utf-8")
    result = subprocess.run(
        ["lualatex", "-halt-on-error", "-interaction=nonstopmode", tex_path.name],
        cwd=output_dir,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        raise RuntimeError("LuaLaTeX could not import the generated PGF figures")
    print("Created and LuaLaTeX-tested all nine PGF figure types successfully.")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="trade-pgf-test-") as temp_dir:
        output_dir = Path(temp_dir)
        pgf_files = build_representative_figures(output_dir)
        compile_lualatex(pgf_files, output_dir)


if __name__ == "__main__":
    main()
