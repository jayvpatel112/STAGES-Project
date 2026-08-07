import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell
def hero(mo):
    mo.md(r"""
    # Germany's Cross-Border Electricity Trade — 2019 to 2025

    A comprehensive analysis of Germany's electricity exchange with its
    European neighbours across seven years, built entirely on measured data
    from the **Energy-Charts API** (Fraunhofer ISE), which aggregates the
    official ENTSO-E transparency records. Every chart is real; nothing is
    synthetic.

    **Final sign convention used in this notebook and in the report**

    - **Gross exports** = electricity sent from Germany to neighbours
    - **Gross imports** = electricity received by Germany from neighbours
    - **Net trade** = gross exports minus gross imports
    - Therefore, **positive values mean Germany is a net exporter** and
      **negative values mean Germany is a net importer**.

    To keep the figures internally consistent, all final net-trade results are
    derived from the gross export and gross import series.
    """)
    return


@app.cell
def imports():
    import json
    import time
    import urllib.request
    from pathlib import Path

    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Patch

    import marimo as mo

    return Patch, Path, json, mdates, mo, np, pd, plt, time, urllib


@app.cell
def config(Path):
    YEARS = list(range(2019, 2026))
    BASE_URL = "https://api.energy-charts.info"

    HERE = Path(__file__).resolve().parent
    CACHE = HERE / "data" / "_cache"
    FIGS = HERE / "figures"
    REPORTS = HERE / "reports"
    CACHE.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    NEIGHBOUR_ALIASES = {
        "france": "France",
        "netherlands": "Netherlands",
        "switzerland": "Switzerland",
        "austria": "Austria",
        "czech republic": "Czechia", "czechia": "Czechia",
        "poland": "Poland",
        "denmark 1": "Denmark", "denmark 2": "Denmark", "denmark": "Denmark",
        "sweden 4": "Sweden", "sweden": "Sweden",
        "luxembourg": "Luxembourg",
        "belgium": "Belgium",
        "norway 2": "Norway", "norway": "Norway",
    }

    PALETTE = {
        "France": "#3b82f6", "Netherlands": "#f97316", "Switzerland": "#ef4444",
        "Austria": "#16a34a", "Czechia": "#8b5cf6", "Poland": "#0ea5e9",
        "Denmark": "#eab308", "Sweden": "#6366f1", "Luxembourg": "#ec4899",
        "Belgium": "#84cc16", "Norway": "#14b8a6",
    }
    COL = {
        "export": "#2563eb", "import": "#ef4444",
        "ink": "#0f172a", "muted": "#64748b",
        "grid": "#eef2f7", "bg": "#f8fafc", "accent": "#f59e0b",
    }
    return BASE_URL, CACHE, COL, FIGS, HERE, NEIGHBOUR_ALIASES, PALETTE, REPORTS, YEARS


@app.cell
def house_style(plt):
    plt.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 220,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
        "font.family": "serif",
        "font.size": 11,
        "axes.edgecolor": "#94a3b8",
        "axes.linewidth": 0.8,
        "axes.labelcolor": "#334155",
        "axes.grid": True,
        "grid.color": "#eef2f7",
        "grid.linewidth": 0.9,
        "axes.axisbelow": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.titlecolor": "#0f172a",
        "axes.titlepad": 14,
        "xtick.color": "#475569",
        "ytick.color": "#475569",
        "legend.frameon": False,
        "legend.fontsize": 9.5,
        "pgf.texsystem": "lualatex",
        "pgf.rcfonts": False,
        "pgf.preamble": r"\usepackage[T1]{fontenc}",
    })

    def save_png_and_pgf(fig, name, FIGS):
        _png_path = FIGS / name
        _pgf_path = FIGS / f"{_png_path.stem}.pgf"
        fig.savefig(_png_path)
        fig.savefig(_pgf_path)
        return _png_path, _pgf_path

    return (save_png_and_pgf,)


@app.cell
def data_layer(BASE_URL, CACHE, NEIGHBOUR_ALIASES, json, np, pd, time, urllib):
    def get_json(url, cache_name):
        _cache_file = CACHE / cache_name
        if _cache_file.exists():
            try:
                return json.loads(_cache_file.read_text())
            except Exception:
                _cache_file.unlink(missing_ok=True)
        _last_error = None
        for _attempt in range(3):
            try:
                _req = urllib.request.Request(
                    url, headers={"User-Agent": "stages-trade/2.1"}
                )
                with urllib.request.urlopen(_req, timeout=120) as _response:
                    _data = json.loads(_response.read().decode())
                _cache_file.write_text(json.dumps(_data))
                time.sleep(0.25)
                return _data
            except Exception as _exc:
                _last_error = _exc
                time.sleep(0.8 * (_attempt + 1))
        raise _last_error

    def fetch_cbet_year(year):
        _url = (
            f"{BASE_URL}/cbet?country=de"
            f"&start={year}-01-01T00:00Z"
            f"&end={year}-12-31T23:00Z"
        )
        return get_json(_url, f"cbet_de_{year}.json")

    def parse_cbet(payload):
        """Return gross import/export frames in MW, plus a raw net series.

        The API sign convention can be confusing. To keep the final report
        correct, this notebook computes all official figures from gross imports
        and gross exports and then derives net trade as exports minus imports.
        The raw net series is retained only for diagnostic checking.
        """
        _secs = payload.get("unix_seconds") or []
        _idx = pd.to_datetime(np.array(_secs, dtype="int64"), unit="s", utc=True)
        _countries = payload.get("countries") or []

        _net_raw = {}
        _imports = {}
        _exports = {}
        _unmatched = []

        for _entry in _countries:
            _raw_name = str(_entry.get("name", "")).strip()
            _canon = NEIGHBOUR_ALIASES.get(_raw_name.lower())
            if _canon is None:
                _unmatched.append(_raw_name)
                continue

            _source_gw = pd.Series(_entry.get("data") or [], index=_idx, dtype="float64")
            _source_mw = _source_gw * 1000.0

            # Energy-Charts /cbet source convention used here:
            # + import to Germany, - export from Germany.
            _import_mw = _source_mw.clip(lower=0)
            _export_mw = -_source_mw.clip(upper=0)
            _raw_net_export_mw = -_source_mw

            for _target, _series in (
                (_net_raw, _raw_net_export_mw),
                (_imports, _import_mw),
                (_exports, _export_mw),
            ):
                _target[_canon] = (
                    _target[_canon].add(_series, fill_value=0)
                    if _canon in _target
                    else _series
                )

        _raw_net_df = pd.DataFrame(_net_raw).sort_index()
        _import_df = pd.DataFrame(_imports).sort_index()
        _export_df = pd.DataFrame(_exports).sort_index()

        if len(_raw_net_df) >= 2:
            _step_min = float(
                np.median(
                    np.diff(_raw_net_df.index.values)
                    .astype("timedelta64[m]")
                    .astype(int)
                )
            )
            _step_h = _step_min / 60.0
        else:
            _step_h = 1.0

        return _raw_net_df, _import_df, _export_df, {
            "unmatched": sorted(set(_unmatched)),
            "step_h": _step_h,
            "source_unit": "GW",
            "converted_unit": "MW",
        }

    return fetch_cbet_year, parse_cbet


@app.cell
def fetch_ui(mo):
    fetch_button = mo.ui.run_button(
        label="  Fetch data and export PNG + PGF figures  ",
        kind="success",
    )
    mo.md(
        f"""
        ## 1. Load the data

        First run downloads the seven yearly files from Energy-Charts and caches
        them under `data/_cache/` — subsequent runs are instant. The notebook
        then writes all nine report charts to `figures/` as both PNG previews
        and LuaLaTeX-compatible PGF figures.

        {fetch_button}
        """
    )
    return (fetch_button,)


@app.cell
def fetch(YEARS, fetch_button, fetch_cbet_year, mo, np, parse_cbet, pd):
    mo.stop(not fetch_button.value, mo.md("*Click the green button above to load data.*"))

    _raw_net_frames = []
    _import_frames = []
    _export_frames = []
    _diag = {}

    for _year in YEARS:
        _raw_net, _imports, _exports, _year_diag = parse_cbet(fetch_cbet_year(_year))
        _raw_net_frames.append(_raw_net)
        _import_frames.append(_imports)
        _export_frames.append(_exports)
        _diag[_year] = _year_diag

    _raw_net_mw = pd.concat(_raw_net_frames).sort_index()
    _raw_import_mw = pd.concat(_import_frames).sort_index()
    _raw_export_mw = pd.concat(_export_frames).sort_index()

    _raw_net_mw = _raw_net_mw[~_raw_net_mw.index.duplicated(keep="first")]
    _raw_import_mw = _raw_import_mw[~_raw_import_mw.index.duplicated(keep="first")]
    _raw_export_mw = _raw_export_mw[~_raw_export_mw.index.duplicated(keep="first")]

    _step_h = float(np.mean([_diag[_year]["step_h"] for _year in YEARS if _diag[_year]["step_h"]]))
    _unmatched_names = sorted({_name for _year in YEARS for _name in _diag[_year]["unmatched"]})

    energy_raw_net_mwh = _raw_net_mw * _step_h
    energy_import_mwh = _raw_import_mw * _step_h
    energy_export_mwh = _raw_export_mw * _step_h
    data_ready = _raw_import_mw.shape[0] > 0

    _found = ", ".join(_raw_import_mw.columns) if data_ready else "—"
    _ignored = ", ".join(_unmatched_names) if _unmatched_names else "none"

    _diag_banner = mo.md(
        f"""
        ### Data loaded

        - **{len(_raw_import_mw):,}** time steps at **{_step_h * 60:.0f} min** resolution
        - Period: **{_raw_import_mw.index.min():%Y-%m-%d} → {_raw_import_mw.index.max():%Y-%m-%d}**
        - Neighbours found: **{_found}**
        - Aggregate/non-neighbour rows ignored: *{_ignored}*
        - Gross trade series extracted and cached successfully.
        - Final net trade in all report charts is computed as **exports minus imports**.
        """
    )
    _diag_banner
    return data_ready, energy_export_mwh, energy_import_mwh, energy_raw_net_mwh


@app.cell
def aggregate(data_ready, energy_export_mwh, energy_import_mwh, energy_raw_net_mwh, mo, pd):
    mo.stop(not data_ready)

    _export_twh = energy_export_mwh / 1e6
    _import_twh = energy_import_mwh / 1e6
    _raw_net_twh = energy_raw_net_mwh / 1e6

    annual_exp = _export_twh.resample("YE").sum()
    annual_imp = _import_twh.resample("YE").sum()
    annual_net = annual_exp - annual_imp
    annual_raw_net = _raw_net_twh.resample("YE").sum()

    _monthly_exp = _export_twh.resample("MS").sum()
    _monthly_imp = _import_twh.resample("MS").sum()
    _monthly_net = _monthly_exp - _monthly_imp
    monthly_total = _monthly_net.sum(axis=1)

    for _frame in (annual_exp, annual_imp, annual_net, annual_raw_net):
        _frame.index = _frame.index.year

    ann_total_exp = annual_exp.sum(axis=1)
    ann_total_imp = annual_imp.sum(axis=1)
    ann_total_net = annual_net.sum(axis=1)
    ann_total_raw_net = annual_raw_net.sum(axis=1)

    partner_exp = annual_exp.sum()
    partner_imp = annual_imp.sum()
    partner_net = partner_exp - partner_imp

    _monthly_total_for_heatmap = monthly_total.copy()
    _monthly_total_for_heatmap.index = pd.MultiIndex.from_arrays(
        [_monthly_total_for_heatmap.index.year, _monthly_total_for_heatmap.index.month],
        names=["year", "month"],
    )
    heat_month_year = _monthly_total_for_heatmap.unstack("year")

    derived_minus_raw = ann_total_net - ann_total_raw_net

    return (
        ann_total_exp,
        ann_total_imp,
        ann_total_net,
        ann_total_raw_net,
        annual_exp,
        annual_imp,
        annual_net,
        derived_minus_raw,
        heat_month_year,
        monthly_total,
        partner_exp,
        partner_imp,
        partner_net,
    )


@app.cell
def diagnostics(ann_total_net, ann_total_raw_net, data_ready, derived_minus_raw, mo, pd):
    mo.stop(not data_ready)
    _diagnostics_df = pd.DataFrame({
        "Net from exports-imports (TWh)": ann_total_net,
        "Raw API-derived net (TWh)": ann_total_raw_net,
        "Difference (derived - raw)": derived_minus_raw,
    })
    mo.md("## 2. Sign-convention diagnostic")
    _diagnostics_df
    return


@app.cell
def kpi(ann_total_exp, ann_total_imp, ann_total_net, data_ready, mo, partner_exp, partner_imp):
    mo.stop(not data_ready)

    _flip = next((_year for _year in ann_total_net.index if ann_total_net[_year] < 0), None)
    _first_year = ann_total_net.index[0]
    _last_year = ann_total_net.index[-1]
    _delta = ann_total_net.iloc[-1] - ann_total_net.iloc[0]
    _top_imp = partner_imp.idxmax()
    _top_exp = partner_exp.idxmax()

    def _card(title, value, sub, color):
        return (
            f"<div style='flex:1;min-width:170px;background:white;"
            f"border-radius:12px;border:1px solid #e5e7eb;padding:16px 18px;'>"
            f"<div style='font-size:11px;letter-spacing:2px;color:{color};"
            f"text-transform:uppercase;font-weight:700;'>{title}</div>"
            f"<div style='font-size:1.7rem;font-weight:700;color:#0f172a;"
            f"margin-top:4px;'>{value}</div>"
            f"<div style='font-size:0.85rem;color:#64748b;margin-top:2px;'>"
            f"{sub}</div></div>"
        )

    mo.md(
        "## 3. Headline numbers, 2019 to 2025\n\n"
        "<div style='display:flex;gap:12px;flex-wrap:wrap;margin:10px 0;'>"
        + _card("Flip year", str(_flip) if _flip else "—", "First net-import year", "#dc2626")
        + _card(f"Net {_first_year}", f"{ann_total_net.iloc[0]:+.1f} TWh", "beginning of the period", "#2563eb")
        + _card(f"Net {_last_year}", f"{ann_total_net.iloc[-1]:+.1f} TWh", "end of the period", "#dc2626")
        + _card("Swing", f"{_delta:+.1f} TWh", f"{_last_year} minus {_first_year}", "#0f172a")
        + _card("Top import partner", _top_imp, f"{partner_imp.max():.1f} TWh over period", "#dc2626")
        + _card("Top export partner", _top_exp, f"{partner_exp.max():.1f} TWh over period", "#2563eb")
        + "</div>\n\n"
        f"Total gross imports **{ann_total_imp.sum():.1f} TWh** versus total gross exports **{ann_total_exp.sum():.1f} TWh** across the period."
    )
    return


@app.cell
def fig1(COL, FIGS, Patch, ann_total_net, data_ready, mo, plt, save_png_and_pgf):
    mo.stop(not data_ready)
    _fig, _ax = plt.subplots(figsize=(10, 5))
    _x_labels = ann_total_net.index.astype(str).tolist()
    _values = ann_total_net.values
    _colors = [COL["export"] if _value >= 0 else COL["import"] for _value in _values]
    _bars = _ax.bar(_x_labels, _values, color=_colors, edgecolor="white", linewidth=1.2, zorder=3)
    _ax.axhline(0, color=COL["ink"], lw=1.2)
    _span = (max(_values) - min(_values)) if len(_values) else 1.0
    for _bar, _value in zip(_bars, _values):
        _offset = _span * 0.02
        _ax.text(
            _bar.get_x() + _bar.get_width() / 2,
            _value + (_offset if _value >= 0 else -_offset),
            f"{_value:+.1f}",
            ha="center",
            va="bottom" if _value >= 0 else "top",
            fontsize=10.5,
            fontweight="bold",
            color=COL["export"] if _value >= 0 else COL["import"],
        )
    _ax.set_title("Annual net electricity balance — Germany, 2019 to 2025")
    _ax.set_ylabel("Net balance (TWh)   +export / -import")
    _ax.margins(y=0.22)
    _ax.legend(
        handles=[
            Patch(facecolor=COL["export"], label="Net exporter"),
            Patch(facecolor=COL["import"], label="Net importer"),
        ],
        loc="upper right",
    )
    save_png_and_pgf(_fig, "trade_01_annual_net_balance.png", FIGS)
    _fig
    return


@app.cell
def fig2(COL, FIGS, ann_total_exp, ann_total_imp, data_ready, mo, np, plt, save_png_and_pgf):
    mo.stop(not data_ready)
    _fig, _ax = plt.subplots(figsize=(10, 5))
    _x_labels = ann_total_exp.index.astype(str).tolist()
    _width = 0.4
    _positions = np.arange(len(_x_labels))
    _ax.bar(_positions - _width / 2, ann_total_exp.values, _width, label="Gross exports", color=COL["export"], edgecolor="white", zorder=3)
    _ax.bar(_positions + _width / 2, ann_total_imp.values, _width, label="Gross imports", color=COL["import"], edgecolor="white", zorder=3)
    for _idx in range(len(_x_labels)):
        _ax.text(_positions[_idx] - _width / 2, ann_total_exp.values[_idx] + 1.2, f"{ann_total_exp.values[_idx]:.0f}", ha="center", fontsize=9, color=COL["export"])
        _ax.text(_positions[_idx] + _width / 2, ann_total_imp.values[_idx] + 1.2, f"{ann_total_imp.values[_idx]:.0f}", ha="center", fontsize=9, color=COL["import"])
    _ax.set_xticks(_positions)
    _ax.set_xticklabels(_x_labels)
    _ax.set_ylabel("Energy (TWh)")
    _ax.set_title("Gross exports and gross imports each year")
    _ax.legend(loc="upper right")
    save_png_and_pgf(_fig, "trade_02_gross_imp_exp.png", FIGS)
    _fig
    return


@app.cell
def fig3(COL, FIGS, PALETTE, annual_net, data_ready, mo, plt, save_png_and_pgf):
    mo.stop(not data_ready)
    _columns = [c for c in PALETTE if c in annual_net.columns] + [c for c in annual_net.columns if c not in PALETTE]
    _n_years = len(annual_net)
    _positive_bottom = [0.0] * _n_years
    _negative_bottom = [0.0] * _n_years
    _x_labels = annual_net.index.astype(str).tolist()

    _fig, _ax = plt.subplots(figsize=(11, 5.6))
    for _country in _columns:
        _values = annual_net[_country].values
        _bottom = [_positive_bottom[_idx] if _values[_idx] >= 0 else _negative_bottom[_idx] for _idx in range(_n_years)]
        _ax.bar(_x_labels, _values, bottom=_bottom, label=_country, color=PALETTE.get(_country, "#94a3b8"), edgecolor="white", linewidth=0.6, zorder=3)
        for _idx in range(_n_years):
            if _values[_idx] >= 0:
                _positive_bottom[_idx] += _values[_idx]
            else:
                _negative_bottom[_idx] += _values[_idx]

    _ax.axhline(0, color=COL["ink"], lw=1.2)
    _ax.set_title("Net trade by neighbour, stacked — 2019 to 2025")
    _ax.set_ylabel("Net trade (TWh)   +export / -import")
    _ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(1.01, 0.0), frameon=False, borderaxespad=0)
    save_png_and_pgf(_fig, "trade_03_stacked_by_neighbour.png", FIGS)
    _fig
    return


@app.cell
def fig4(COL, FIGS, data_ready, mo, np, partner_exp, partner_imp, plt, save_png_and_pgf):
    mo.stop(not data_ready)
    _names = sorted(set(partner_exp.index) | set(partner_imp.index), key=lambda _name: -(partner_exp.get(_name, 0) + partner_imp.get(_name, 0)))
    _export_values = [partner_exp.get(_name, 0) for _name in _names]
    _import_values = [partner_imp.get(_name, 0) for _name in _names]

    _fig, _ax = plt.subplots(figsize=(10, 5.6))
    _y_positions = np.arange(len(_names))
    _ax.barh(_y_positions - 0.2, _export_values, height=0.4, color=COL["export"], edgecolor="white", label="Exports to", zorder=3)
    _ax.barh(_y_positions + 0.2, _import_values, height=0.4, color=COL["import"], edgecolor="white", label="Imports from", zorder=3)
    for _y_position, _export_value, _import_value in zip(_y_positions, _export_values, _import_values):
        _ax.text(_export_value + 0.6, _y_position - 0.2, f"{_export_value:.0f}", va="center", fontsize=9, color=COL["export"])
        _ax.text(_import_value + 0.6, _y_position + 0.2, f"{_import_value:.0f}", va="center", fontsize=9, color=COL["import"])
    _ax.set_yticks(_y_positions)
    _ax.set_yticklabels(_names)
    _ax.invert_yaxis()
    _ax.set_xlabel("Energy (TWh, 2019 to 2025 total)")
    _ax.set_title("Trading partners: who Germany imports from vs exports to")
    _ax.legend(loc="lower right")
    _ax.grid(axis="y", visible=False)
    save_png_and_pgf(_fig, "trade_04_partners_imp_exp.png", FIGS)
    _fig
    return


@app.cell
def fig5(COL, FIGS, data_ready, mo, partner_net, plt, save_png_and_pgf):
    mo.stop(not data_ready)
    _series = partner_net.sort_values()
    _fig, _ax = plt.subplots(figsize=(10, 5.4))
    _colors = [COL["export"] if _value >= 0 else COL["import"] for _value in _series.values]
    _ax.barh(_series.index, _series.values, color=_colors, edgecolor="white", zorder=3)
    for _name, _value in zip(_series.index, _series.values):
        _ax.text(_value + (0.6 if _value >= 0 else -0.6), _name, f"{_value:+.1f}", va="center", ha="left" if _value >= 0 else "right", fontsize=10, fontweight="600")
    _ax.axvline(0, color=COL["ink"], lw=1.2)
    _ax.set_title("Net position by neighbour — 2019 to 2025 total")
    _ax.set_xlabel("Net trade (TWh)   +Germany exports / -Germany imports")
    _ax.grid(axis="y", visible=False)
    _ax.margins(x=0.15)
    save_png_and_pgf(_fig, "trade_05_net_per_neighbour.png", FIGS)
    _fig
    return


@app.cell
def fig6(FIGS, annual_net, data_ready, mo, np, plt, save_png_and_pgf):
    mo.stop(not data_ready)
    _order = annual_net.abs().sum().sort_values(ascending=False).index.tolist()
    _matrix = annual_net.loc[:, _order].T
    _limit = max(float(np.nanmax(np.abs(_matrix.values))), 1e-9)

    _fig, (_ax, _cax) = plt.subplots(1, 2, figsize=(10.5, 5.6), gridspec_kw={"width_ratios": [32, 1], "wspace": 0.08})
    _ax.pcolormesh(np.arange(_matrix.shape[1] + 1) - 0.5, np.arange(_matrix.shape[0] + 1) - 0.5, _matrix.values, cmap="RdBu", vmin=-_limit, vmax=_limit, shading="flat")
    _ax.set_xticks(range(len(_matrix.columns)))
    _ax.set_xticklabels(_matrix.columns)
    _ax.set_yticks(range(len(_matrix.index)))
    _ax.set_yticklabels(_matrix.index)
    _ax.set_xlim(-0.5, _matrix.shape[1] - 0.5)
    _ax.set_ylim(_matrix.shape[0] - 0.5, -0.5)
    for _row in range(_matrix.shape[0]):
        for _col in range(_matrix.shape[1]):
            _value = _matrix.values[_row, _col]
            if not np.isnan(_value):
                _ax.text(_col, _row, f"{_value:+.1f}", ha="center", va="center", fontsize=9, color="white" if abs(_value) > _limit * 0.55 else "#0f172a", fontweight="600")
    _edges = np.linspace(-_limit, _limit, 65)
    _centres = (_edges[:-1] + _edges[1:]) / 2
    _step = _edges[1] - _edges[0]
    _cax.barh(_centres, np.ones_like(_centres), height=_step * 1.02, color=plt.get_cmap("RdBu")((_centres + _limit) / (2 * _limit)), edgecolor="none")
    _cax.set_xlim(0, 1)
    _cax.set_ylim(-_limit, _limit)
    _cax.set_xticks([])
    _cax.yaxis.tick_right()
    _cax.yaxis.set_label_position("right")
    _cax.set_ylabel("Net trade (TWh)  blue=export, red=import", color="#334155")
    _cax.grid(False)
    for _spine in _cax.spines.values():
        _spine.set_visible(False)
    _ax.set_title("Net trade by neighbour and year — the full matrix")
    _ax.grid(False)
    save_png_and_pgf(_fig, "trade_06_heatmap.png", FIGS)
    _fig
    return


@app.cell
def fig7(COL, FIGS, data_ready, mdates, mo, monthly_total, plt, save_png_and_pgf):
    mo.stop(not data_ready)
    _fig, _ax = plt.subplots(figsize=(11, 4.8))
    _series = monthly_total
    _ax.fill_between(_series.index, _series.values, 0, where=(_series.values >= 0), color=COL["export"], alpha=0.85, zorder=3, label="Net export month")
    _ax.fill_between(_series.index, _series.values, 0, where=(_series.values < 0), color=COL["import"], alpha=0.85, zorder=3, label="Net import month")
    _ax.axhline(0, color=COL["ink"], lw=1.2)
    _ax.xaxis.set_major_locator(mdates.YearLocator())
    _ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _ax.set_title("Monthly net balance — the seasonal rhythm")
    _ax.set_ylabel("Net balance (TWh)")
    _ax.legend(loc="upper right")
    save_png_and_pgf(_fig, "trade_07_monthly_seasonal.png", FIGS)
    _fig
    return


@app.cell
def fig8(FIGS, data_ready, heat_month_year, mo, np, plt, save_png_and_pgf):
    mo.stop(not data_ready)
    _fig, (_ax, _cax) = plt.subplots(1, 2, figsize=(10.5, 5.4), gridspec_kw={"width_ratios": [32, 1], "wspace": 0.08})
    _matrix = heat_month_year
    _limit = max(float(np.nanmax(np.abs(_matrix.values))), 1e-9)
    _ax.pcolormesh(np.arange(_matrix.shape[1] + 1) - 0.5, np.arange(_matrix.shape[0] + 1) - 0.5, _matrix.values, cmap="RdBu", vmin=-_limit, vmax=_limit, shading="flat")
    _months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    _ax.set_yticks(range(len(_matrix.index)))
    _ax.set_yticklabels(_months)
    _ax.set_xticks(range(len(_matrix.columns)))
    _ax.set_xticklabels(_matrix.columns)
    _ax.set_xlim(-0.5, _matrix.shape[1] - 0.5)
    _ax.set_ylim(_matrix.shape[0] - 0.5, -0.5)
    for _row in range(_matrix.shape[0]):
        for _col in range(_matrix.shape[1]):
            _value = _matrix.values[_row, _col]
            if not np.isnan(_value):
                _ax.text(_col, _row, f"{_value:+.1f}", ha="center", va="center", fontsize=8.5, color="white" if abs(_value) > _limit * 0.55 else "#0f172a")
    _edges = np.linspace(-_limit, _limit, 65)
    _centres = (_edges[:-1] + _edges[1:]) / 2
    _step = _edges[1] - _edges[0]
    _cax.barh(_centres, np.ones_like(_centres), height=_step * 1.02, color=plt.get_cmap("RdBu")((_centres + _limit) / (2 * _limit)), edgecolor="none")
    _cax.set_xlim(0, 1)
    _cax.set_ylim(-_limit, _limit)
    _cax.set_xticks([])
    _cax.yaxis.tick_right()
    _cax.yaxis.set_label_position("right")
    _cax.set_ylabel("Net balance (TWh)")
    _cax.grid(False)
    for _spine in _cax.spines.values():
        _spine.set_visible(False)
    _ax.set_title("Month by year heatmap — seasonality and trend together")
    _ax.grid(False)
    save_png_and_pgf(_fig, "trade_08_month_year_heatmap.png", FIGS)
    _fig
    return


@app.cell
def fig9(COL, FIGS, PALETTE, annual_net, data_ready, mo, plt, save_png_and_pgf):
    mo.stop(not data_ready)
    _fig, _ax = plt.subplots(figsize=(11, 6))
    _order = annual_net.iloc[-1].sort_values(ascending=False).index.tolist()
    for _country in _order:
        _ax.plot(annual_net.index, annual_net[_country], marker="o", ms=5.5, lw=2.2, color=PALETTE.get(_country, "#94a3b8"), label=_country)
    _ax.axhline(0, color=COL["ink"], lw=1, ls="--", alpha=0.5)
    _ax.set_title("Evolution of each trading relationship, 2019 to 2025")
    _ax.set_ylabel("Net trade (TWh)   +export / -import")
    _ax.set_xlabel("Year")
    _ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", frameon=False)
    save_png_and_pgf(_fig, "trade_09_relationship_evolution.png", FIGS)
    _fig
    return


@app.cell
def year_pick_ui(annual_net, data_ready, mo):
    mo.stop(not data_ready)
    year_pick = mo.ui.dropdown(options=[str(_year) for _year in annual_net.index], value=str(annual_net.index[-1]), label="Inspect one year")
    mo.md(f"## 4. Interactive: pick a year\n\n{year_pick}")
    return (year_pick,)


@app.cell
def year_view(COL, annual_exp, annual_imp, annual_net, data_ready, mo, np, plt, year_pick):
    mo.stop(not data_ready)
    _selected_year = int(year_pick.value)
    _exports = annual_exp.loc[_selected_year]
    _imports = annual_imp.loc[_selected_year]
    _order = (_exports + _imports).sort_values(ascending=False).index.tolist()

    _fig, _ax = plt.subplots(figsize=(10.5, 5.6))
    _positions = np.arange(len(_order))
    _ax.barh(_positions - 0.2, [_exports[_name] for _name in _order], height=0.4, color=COL["export"], label="Exports to", zorder=3)
    _ax.barh(_positions + 0.2, [_imports[_name] for _name in _order], height=0.4, color=COL["import"], label="Imports from", zorder=3)
    _ax.set_yticks(_positions)
    _ax.set_yticklabels(_order)
    _ax.invert_yaxis()
    _ax.set_xlabel("Energy (TWh)")
    _net_trade = annual_net.loc[_selected_year].sum()
    _position_label = "net exporter" if _net_trade >= 0 else "net importer"
    _ax.set_title(f"{_selected_year} per-neighbour flows   (overall net {_net_trade:+.1f} TWh, {_position_label})")
    _ax.legend(loc="lower right")
    _ax.grid(axis="y", visible=False)
    _fig
    return


@app.cell
def export_files(FIGS, REPORTS, ann_total_exp, ann_total_imp, ann_total_net, annual_exp, annual_imp, annual_net, data_ready, monthly_total, mo, partner_exp, partner_imp, partner_net, pd):
    mo.stop(not data_ready)

    _annual_summary = pd.DataFrame({
        "gross_exports_twh": ann_total_exp,
        "gross_imports_twh": ann_total_imp,
        "net_trade_twh": ann_total_net,
    })
    _annual_summary.index.name = "year"
    _annual_summary.to_csv(REPORTS / "trade_annual_summary.csv")

    _partner_summary = pd.DataFrame({
        "exports_twh": partner_exp,
        "imports_twh": partner_imp,
        "net_trade_twh": partner_net,
    }).sort_values("net_trade_twh")
    _partner_summary.index.name = "partner"
    _partner_summary.to_csv(REPORTS / "trade_partner_summary.csv")

    _monthly_df = monthly_total.to_frame("net_trade_twh")
    _monthly_df.index.name = "month"
    _monthly_df.to_csv(REPORTS / "trade_monthly_net_balance.csv")

    _lines = [
        "TRADE REPORT NUMBERS — Germany cross-border electricity trade, 2019 to 2025",
        "",
        f"2019 net trade: {ann_total_net.loc[2019]:+.2f} TWh",
        f"2020 net trade: {ann_total_net.loc[2020]:+.2f} TWh",
        f"2021 net trade: {ann_total_net.loc[2021]:+.2f} TWh",
        f"2022 net trade: {ann_total_net.loc[2022]:+.2f} TWh",
        f"2023 net trade: {ann_total_net.loc[2023]:+.2f} TWh",
        f"2024 net trade: {ann_total_net.loc[2024]:+.2f} TWh",
        f"2025 net trade: {ann_total_net.loc[2025]:+.2f} TWh",
        "",
        f"Total gross exports over 2019-2025: {ann_total_exp.sum():.2f} TWh",
        f"Total gross imports over 2019-2025: {ann_total_imp.sum():.2f} TWh",
        "",
        f"Top export partner: {partner_exp.idxmax()} ({partner_exp.max():.2f} TWh)",
        f"Top import partner: {partner_imp.idxmax()} ({partner_imp.max():.2f} TWh)",
    ]
    (REPORTS / "trade_report_numbers.txt").write_text("\n".join(_lines), encoding="utf-8")

    _figure_inventory = [
        "trade_01_annual_net_balance.png / .pgf",
        "trade_02_gross_imp_exp.png / .pgf",
        "trade_03_stacked_by_neighbour.png / .pgf",
        "trade_04_partners_imp_exp.png / .pgf",
        "trade_05_net_per_neighbour.png / .pgf",
        "trade_06_heatmap.png / .pgf",
        "trade_07_monthly_seasonal.png / .pgf",
        "trade_08_month_year_heatmap.png / .pgf",
        "trade_09_relationship_evolution.png / .pgf",
    ]
    (REPORTS / "trade_figure_inventory.txt").write_text("\n".join(_figure_inventory), encoding="utf-8")

    mo.md("## 5. Export complete\n\nSaved corrected PNG and PGF figures to `figures/` and summary tables to `reports/`.")
    return


@app.cell
def outro(mo):
    mo.md(r"""
    ## 6. What the figures now show

    Read together, the nine figures document one story:

    - The **balance turned gradually** into net import; there is no single
      crash year.
    - **Different neighbours drive the swing** — some borders flip from
      export to import while others do not.
    - **Germany imports and exports at the same time**, in the same year and
      often in the same week — the mark of an integrated market routing
      power by price.
    - Trade has a **clear seasonal rhythm**, with imports deepening in winter
      and easing (or flipping to export) in summer.

    The next report chapter — *Germany as a Net Importer: Shortage or Strategy?* —
    takes each of these observations and asks *why*.
    """)
    return


if __name__ == "__main__":
    app.run()
