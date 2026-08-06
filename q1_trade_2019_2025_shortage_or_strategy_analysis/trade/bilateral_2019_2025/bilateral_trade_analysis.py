import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell
def hero(mo):
    mo.md(r"""
    # Germany's Cross-Border Electricity Trade — 2019 → 2025

    A comprehensive analysis of Germany's electricity exchange with its
    European neighbours across seven years, built entirely on measured data
    from the **Energy-Charts API** (Fraunhofer ISE), which aggregates the
    official ENTSO-E transparency records. Every chart is real; nothing is
    synthetic.

    **Sign convention.** Positive values are net *exports* from Germany;
    negative values are net *imports* into Germany.
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
    from pgf_export import save_png_and_pgf

    import marimo as mo

    return (
        Patch,
        Path,
        json,
        mdates,
        mo,
        np,
        pd,
        plt,
        save_png_and_pgf,
        time,
        urllib,
    )


@app.cell
def config(Path):
    YEARS = list(range(2019, 2026))
    BASE_URL = "https://api.energy-charts.info"

    HERE = Path(__file__).resolve().parent
    CACHE = HERE / "data" / "_cache"
    FIGS = HERE / "figures"
    CACHE.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    # Energy-Charts returns full country names, sometimes with a bidding-zone
    # suffix ("Denmark 1", "Norway 2"). Everything in this map is a neighbour
    # we want counted; anything else the API returns is dropped and reported.
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
    return BASE_URL, CACHE, COL, FIGS, NEIGHBOUR_ALIASES, PALETTE, YEARS


@app.cell
def house_style(plt, save_png_and_pgf):
    plt.rcParams.update({
        "figure.dpi": 120, "savefig.dpi": 220, "savefig.bbox": "tight",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Sans", "font.size": 11,
        "axes.edgecolor": "#94a3b8", "axes.linewidth": 0.8,
        "axes.labelcolor": "#334155",
        "axes.grid": True, "grid.color": "#eef2f7", "grid.linewidth": 0.9,
        "axes.axisbelow": True,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titlesize": 14, "axes.titleweight": "bold",
        "axes.titlecolor": "#0f172a", "axes.titlepad": 14,
        "xtick.color": "#475569", "ytick.color": "#475569",
        "legend.frameon": False, "legend.fontsize": 9.5,
    })

    def save_fig(fig, name, FIGS):
        return save_png_and_pgf(fig, name, FIGS)

    return (save_fig,)


@app.cell
def data_layer(BASE_URL, CACHE, NEIGHBOUR_ALIASES, json, np, pd, time, urllib):
    def get_json(url, cache_name):
        cf = CACHE / cache_name
        if cf.exists():
            try:
                return json.loads(cf.read_text())
            except Exception:
                cf.unlink(missing_ok=True)
        last = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "stages-trade/2.0"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    data = json.loads(r.read().decode())
                cf.write_text(json.dumps(data))
                time.sleep(0.25)
                return data
            except Exception as e:
                last = e
                time.sleep(0.8 * (attempt + 1))
        raise last

    def fetch_cbet_year(year):
        # UTC ISO timestamps avoid timezone ambiguity across DST changes
        url = (f"{BASE_URL}/cbet?country=de"
               f"&start={year}-01-01T00:00Z"
               f"&end={year}-12-31T23:00Z")
        return get_json(url, f"cbet_de_{year}.json")

    def parse_cbet(payload):
        """Return German net exports, imports, and exports in MW.

        Energy-Charts ``/cbet`` reports scheduled commercial exchanges in GW
        using the source convention positive = import and negative = export.
        The returned net frame is converted to the thesis convention
        positive = German export and negative = German import.

        Gross imports and exports are separated before bidding zones belonging
        to the same country are combined. This avoids understating gross flows
        when Germany imports through one zone and exports through another in
        the same interval.
        """
        secs = payload.get("unix_seconds") or []
        idx = pd.to_datetime(np.array(secs, dtype="int64"), unit="s", utc=True)
        countries = payload.get("countries") or []

        net_export, imports, exports, unmatched = {}, {}, {}, []
        for entry in countries:
            raw_name = str(entry.get("name", "")).strip()
            canon = NEIGHBOUR_ALIASES.get(raw_name.lower())
            if canon is None:
                unmatched.append(raw_name)
                continue
            source_gw = pd.Series(
                entry.get("data") or [], index=idx, dtype="float64")
            source_mw = source_gw * 1000.0

            # Energy-Charts source sign: + import, - export.
            import_mw = source_mw.clip(lower=0)
            export_mw = -source_mw.clip(upper=0)
            net_export_mw = -source_mw

            for target, series in (
                (net_export, net_export_mw),
                (imports, import_mw),
                (exports, export_mw),
            ):
                target[canon] = (
                    target[canon].add(series, fill_value=0)
                    if canon in target else series
                )

        net_export_df = pd.DataFrame(net_export).sort_index()
        import_df = pd.DataFrame(imports).sort_index()
        export_df = pd.DataFrame(exports).sort_index()

        if len(net_export_df) >= 2:
            step_min = float(
                np.median(np.diff(net_export_df.index.values)
                          .astype("timedelta64[m]").astype(int))
            )
            step_h = step_min / 60.0
        else:
            step_h = 1.0

        max_abs_gw = (
            float(np.nanmax(np.abs(net_export_df.values))) / 1000.0
            if net_export_df.size else 0.0
        )
        return net_export_df, import_df, export_df, {
            "unmatched": sorted(set(unmatched)),
            "step_h": step_h,
            "source_unit": "GW",
            "converted_unit": "MW",
            "max_abs_source_gw": max_abs_gw,
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
    mo.stop(not fetch_button.value,
            mo.md("*Click the green button above to load data.*"))

    _net_frames = []
    _import_frames = []
    _export_frames = []
    diag = {}
    for _y in YEARS:
        _net, _imports, _exports, _d = parse_cbet(fetch_cbet_year(_y))
        _net_frames.append(_net)
        _import_frames.append(_imports)
        _export_frames.append(_exports)
        diag[_y] = _d

    raw_net_export_mw = pd.concat(_net_frames).sort_index()
    raw_import_mw = pd.concat(_import_frames).sort_index()
    raw_export_mw = pd.concat(_export_frames).sort_index()
    raw_net_export_mw = raw_net_export_mw[
        ~raw_net_export_mw.index.duplicated(keep="first")]
    raw_import_mw = raw_import_mw[
        ~raw_import_mw.index.duplicated(keep="first")]
    raw_export_mw = raw_export_mw[
        ~raw_export_mw.index.duplicated(keep="first")]

    step_h = float(np.mean([diag[_y]["step_h"] for _y in YEARS
                            if diag[_y]["step_h"]]))
    unmatched_names = sorted({n for _y in YEARS
                              for n in diag[_y]["unmatched"]})

    # MW * step_h = MWh per interval
    energy_net_export_mwh = raw_net_export_mw * step_h
    energy_import_mwh = raw_import_mw * step_h
    energy_export_mwh = raw_export_mw * step_h
    data_ready = raw_net_export_mw.shape[0] > 0

    _found = ", ".join(raw_net_export_mw.columns) if data_ready else "—"
    _ignored = ", ".join(unmatched_names) if unmatched_names else "none"

    diag_banner = mo.md(
        f"""
        ### Data loaded

        - **{len(raw_net_export_mw):,}** time steps at **{step_h * 60:.0f} min** resolution
        - Period: **{raw_net_export_mw.index.min():%Y-%m-%d} → {raw_net_export_mw.index.max():%Y-%m-%d}**
        - Neighbours found: **{_found}**
        - Aggregate/non-neighbour rows ignored: *{_ignored}*
        - Source convention: **positive = German import, negative = German export**
        - Analysis convention: **positive = German net export**
        """
    )
    diag_banner
    return (
        data_ready,
        energy_export_mwh,
        energy_import_mwh,
        energy_net_export_mwh,
    )


@app.cell
def aggregate(
    data_ready,
    energy_export_mwh,
    energy_import_mwh,
    energy_net_export_mwh,
    mo,
    pd,
):
    mo.stop(not data_ready)

    net_export_twh = energy_net_export_mwh / 1e6
    export_twh = energy_export_mwh / 1e6
    import_twh = energy_import_mwh / 1e6

    annual_net = net_export_twh.resample("YE").sum()
    annual_exp = export_twh.resample("YE").sum()
    annual_imp = import_twh.resample("YE").sum()

    # Net exports must equal gross exports minus gross imports for every
    # neighbour and year. Fail loudly if a future change breaks the convention.
    _balance_error = (
        annual_net - (annual_exp - annual_imp)
    ).abs().max().max()
    if float(_balance_error) > 1e-9:
        raise AssertionError(
            "Trade balance check failed: net exports != exports - imports "
            f"(maximum error {_balance_error:.3e} TWh)"
        )

    for _d in (annual_net, annual_exp, annual_imp):
        _d.index = _d.index.year

    ann_total_net = annual_net.sum(axis=1)
    ann_total_exp = annual_exp.sum(axis=1)
    ann_total_imp = annual_imp.sum(axis=1)

    partner_net = annual_net.sum()
    partner_exp = annual_exp.sum()
    partner_imp = annual_imp.sum()

    monthly_net = net_export_twh.resample("MS").sum()
    monthly_total = monthly_net.sum(axis=1)

    _mt = monthly_total.copy()
    _mt.index = pd.MultiIndex.from_arrays(
        [_mt.index.year, _mt.index.month], names=["year", "month"])
    heat_month_year = _mt.unstack("year")
    return (
        ann_total_exp,
        ann_total_imp,
        ann_total_net,
        annual_exp,
        annual_imp,
        annual_net,
        heat_month_year,
        monthly_total,
        partner_exp,
        partner_imp,
        partner_net,
    )


@app.cell
def kpi(
    ann_total_exp,
    ann_total_imp,
    ann_total_net,
    data_ready,
    mo,
    partner_exp,
    partner_imp,
):
    mo.stop(not data_ready)

    _flip = next((y for y in ann_total_net.index if ann_total_net[y] < 0), None)
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
        "## 2. Headline numbers, 2019 to 2025\n\n"
        "<div style='display:flex;gap:12px;flex-wrap:wrap;margin:10px 0;'>"
        + _card("Flip year", str(_flip) if _flip else "—",
                "First net-import year", "#dc2626")
        + _card(f"Net {_first_year}", f"{ann_total_net.iloc[0]:+.1f} TWh",
                "beginning of the period", "#2563eb")
        + _card(f"Net {_last_year}", f"{ann_total_net.iloc[-1]:+.1f} TWh",
                "end of the period", "#dc2626")
        + _card("Swing", f"{_delta:+.1f} TWh",
                f"{_last_year} minus {_first_year}", "#0f172a")
        + _card("Top import partner", _top_imp,
                f"{partner_imp.max():.1f} TWh over period", "#dc2626")
        + _card("Top export partner", _top_exp,
                f"{partner_exp.max():.1f} TWh over period", "#2563eb")
        + "</div>\n\n"
        f"Total gross imports **{ann_total_imp.sum():.1f} TWh** versus total gross "
        f"exports **{ann_total_exp.sum():.1f} TWh** across the period."
    )
    return


@app.cell
def fig1(COL, FIGS, Patch, ann_total_net, data_ready, mo, plt, save_fig):
    mo.stop(not data_ready)
    _fig, _ax = plt.subplots(figsize=(10, 5))
    _x = ann_total_net.index.astype(str).tolist()
    _y = ann_total_net.values
    _colors = [COL["export"] if v >= 0 else COL["import"] for v in _y]
    _bars = _ax.bar(_x, _y, color=_colors, edgecolor="white", linewidth=1.2,
                    zorder=3)
    _ax.axhline(0, color=COL["ink"], lw=1.2)
    _span = (max(_y) - min(_y)) if len(_y) else 1.0
    for _b, _v in zip(_bars, _y):
        _off = _span * 0.02
        _ax.text(_b.get_x() + _b.get_width() / 2,
                 _v + (_off if _v >= 0 else -_off),
                 f"{_v:+.1f}", ha="center",
                 va="bottom" if _v >= 0 else "top",
                 fontsize=10.5, fontweight="bold",
                 color=COL["export"] if _v >= 0 else COL["import"])
    _ax.set_title("Annual net electricity balance — Germany, 2019 to 2025")
    _ax.set_ylabel("Net balance (TWh)   +export / -import")
    _ax.margins(y=0.22)
    _ax.legend(handles=[Patch(facecolor=COL["export"], label="Net exporter"),
                        Patch(facecolor=COL["import"], label="Net importer")],
               loc="upper right")
    save_fig(_fig, "trade_01_annual_net_balance.png", FIGS)
    _fig
    return


@app.cell
def fig2(
    COL,
    FIGS,
    ann_total_exp,
    ann_total_imp,
    data_ready,
    mo,
    np,
    plt,
    save_fig,
):
    mo.stop(not data_ready)
    _fig, _ax = plt.subplots(figsize=(10, 5))
    _x = ann_total_exp.index.astype(str).tolist()
    _w = 0.4
    _pos = np.arange(len(_x))
    _ax.bar(_pos - _w / 2, ann_total_exp.values, _w, label="Gross exports",
            color=COL["export"], edgecolor="white", zorder=3)
    _ax.bar(_pos + _w / 2, ann_total_imp.values, _w, label="Gross imports",
            color=COL["import"], edgecolor="white", zorder=3)
    for _i in range(len(_x)):
        _ax.text(_pos[_i] - _w / 2, ann_total_exp.values[_i] + 1.2,
                 f"{ann_total_exp.values[_i]:.0f}", ha="center",
                 fontsize=9, color=COL["export"])
        _ax.text(_pos[_i] + _w / 2, ann_total_imp.values[_i] + 1.2,
                 f"{ann_total_imp.values[_i]:.0f}", ha="center",
                 fontsize=9, color=COL["import"])
    _ax.set_xticks(_pos)
    _ax.set_xticklabels(_x)
    _ax.set_ylabel("Energy (TWh)")
    _ax.set_title("Gross exports and gross imports each year")
    _ax.legend(loc="upper right")
    save_fig(_fig, "trade_02_gross_imp_exp.png", FIGS)
    _fig
    return


@app.cell
def fig3(COL, FIGS, PALETTE, annual_net, data_ready, mo, plt, save_fig):
    mo.stop(not data_ready)
    _cols = ([c for c in PALETTE if c in annual_net.columns]
             + [c for c in annual_net.columns if c not in PALETTE])
    _n = len(annual_net)
    _bp = [0.0] * _n
    _bn = [0.0] * _n
    _x = annual_net.index.astype(str).tolist()

    _fig, _ax = plt.subplots(figsize=(11, 5.6))
    for _c in _cols:
        _v = annual_net[_c].values
        _bot = [_bp[_i] if _v[_i] >= 0 else _bn[_i] for _i in range(_n)]
        _ax.bar(_x, _v, bottom=_bot, label=_c,
                color=PALETTE.get(_c, "#94a3b8"),
                edgecolor="white", linewidth=0.6, zorder=3)
        for _i in range(_n):
            _vv = _v[_i]
            if _vv >= 0:
                _bp[_i] += _vv
            else:
                _bn[_i] += _vv

    _ax.axhline(0, color=COL["ink"], lw=1.2)
    _ax.set_title("Net trade by neighbour, stacked — 2019 to 2025")
    _ax.set_ylabel("Net trade (TWh)   +export / -import")
    _ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(1.01, 0.0),
               frameon=False, borderaxespad=0)
    save_fig(_fig, "trade_03_stacked_by_neighbour.png", FIGS)
    _fig
    return


@app.cell
def fig4(
    COL,
    FIGS,
    data_ready,
    mo,
    np,
    partner_exp,
    partner_imp,
    plt,
    save_fig,
):
    mo.stop(not data_ready)
    _names = sorted(
        set(partner_exp.index) | set(partner_imp.index),
        key=lambda n: -(partner_exp.get(n, 0) + partner_imp.get(n, 0)),
    )
    _exp_vals = [partner_exp.get(_n, 0) for _n in _names]
    _imp_vals = [partner_imp.get(_n, 0) for _n in _names]

    _fig, _ax = plt.subplots(figsize=(10, 5.6))
    _y = np.arange(len(_names))
    _ax.barh(_y - 0.2, _exp_vals, height=0.4, color=COL["export"],
             edgecolor="white", label="Exports to", zorder=3)
    _ax.barh(_y + 0.2, _imp_vals, height=0.4, color=COL["import"],
             edgecolor="white", label="Imports from", zorder=3)
    for _yi, _e, _i in zip(_y, _exp_vals, _imp_vals):
        _ax.text(_e + 0.6, _yi - 0.2, f"{_e:.0f}", va="center",
                 fontsize=9, color=COL["export"])
        _ax.text(_i + 0.6, _yi + 0.2, f"{_i:.0f}", va="center",
                 fontsize=9, color=COL["import"])
    _ax.set_yticks(_y)
    _ax.set_yticklabels(_names)
    _ax.invert_yaxis()
    _ax.set_xlabel("Energy (TWh, 2019 to 2025 total)")
    _ax.set_title("Trading partners: who Germany imports from vs exports to")
    _ax.legend(loc="lower right")
    _ax.grid(axis="y", visible=False)
    save_fig(_fig, "trade_04_partners_imp_exp.png", FIGS)
    _fig
    return


@app.cell
def fig5(COL, FIGS, data_ready, mo, partner_net, plt, save_fig):
    mo.stop(not data_ready)
    _s = partner_net.sort_values()
    _fig, _ax = plt.subplots(figsize=(10, 5.4))
    _colors = [COL["export"] if v >= 0 else COL["import"] for v in _s.values]
    _ax.barh(_s.index, _s.values, color=_colors, edgecolor="white", zorder=3)
    for _n, _v in zip(_s.index, _s.values):
        _ax.text(_v + (0.6 if _v >= 0 else -0.6), _n,
                 f"{_v:+.1f}", va="center",
                 ha="left" if _v >= 0 else "right",
                 fontsize=10, fontweight="600")
    _ax.axvline(0, color=COL["ink"], lw=1.2)
    _ax.set_title("Net position by neighbour — 2019 to 2025 total")
    _ax.set_xlabel("Net trade (TWh)   +Germany exports / -Germany imports")
    _ax.grid(axis="y", visible=False)
    _ax.margins(x=0.15)
    save_fig(_fig, "trade_05_net_per_neighbour.png", FIGS)
    _fig
    return


@app.cell
def fig6(FIGS, annual_net, data_ready, mo, np, plt, save_fig):
    mo.stop(not data_ready)
    _order = annual_net.abs().sum().sort_values(ascending=False).index.tolist()
    _M = annual_net.loc[:, _order].T
    _lim = max(float(np.nanmax(np.abs(_M.values))), 1e-9)

    _fig, (_ax, _cax) = plt.subplots(
        1, 2, figsize=(10.5, 5.6),
        gridspec_kw={"width_ratios": [32, 1], "wspace": 0.08},
    )
    # pcolormesh keeps the heatmap cells as vectors in PGF.  imshow would
    # create an additional raster sidecar file that would also need uploading.
    _im = _ax.pcolormesh(
        np.arange(_M.shape[1] + 1) - 0.5,
        np.arange(_M.shape[0] + 1) - 0.5,
        _M.values,
        cmap="RdBu", vmin=-_lim, vmax=_lim, shading="flat",
    )
    _ax.set_xticks(range(len(_M.columns)))
    _ax.set_xticklabels(_M.columns)
    _ax.set_yticks(range(len(_M.index)))
    _ax.set_yticklabels(_M.index)
    _ax.set_xlim(-0.5, _M.shape[1] - 0.5)
    _ax.set_ylim(_M.shape[0] - 0.5, -0.5)
    for _i in range(_M.shape[0]):
        for _j in range(_M.shape[1]):
            _v = _M.values[_i, _j]
            if not np.isnan(_v):
                _ax.text(_j, _i, f"{_v:+.1f}", ha="center", va="center",
                         fontsize=9,
                         color="white" if abs(_v) > _lim * 0.55 else "#0f172a",
                         fontweight="600")
    # A bar-based colour scale stays fully vector in PGF. Matplotlib's normal
    # colourbar would create a separate ``-img0.png`` raster dependency.
    _edges = np.linspace(-_lim, _lim, 65)
    _centres = (_edges[:-1] + _edges[1:]) / 2
    _step = _edges[1] - _edges[0]
    _cax.barh(
        _centres, np.ones_like(_centres), height=_step * 1.02,
        color=plt.get_cmap("RdBu")((_centres + _lim) / (2 * _lim)),
        edgecolor="none",
    )
    _cax.set_xlim(0, 1)
    _cax.set_ylim(-_lim, _lim)
    _cax.set_xticks([])
    _cax.yaxis.tick_right()
    _cax.yaxis.set_label_position("right")
    _cax.set_ylabel(
        "Net trade (TWh)  blue=export, red=import", color="#334155",
    )
    _cax.grid(False)
    for _spine in _cax.spines.values():
        _spine.set_visible(False)
    _ax.set_title("Net trade by neighbour and year — the full matrix")
    _ax.grid(False)
    save_fig(_fig, "trade_06_heatmap.png", FIGS)
    _fig
    return


@app.cell
def fig7(COL, FIGS, data_ready, mdates, mo, monthly_total, plt, save_fig):
    mo.stop(not data_ready)
    _fig, _ax = plt.subplots(figsize=(11, 4.8))
    _v = monthly_total
    _ax.fill_between(_v.index, _v.values, 0, where=(_v.values >= 0),
                     color=COL["export"], alpha=0.85, zorder=3,
                     label="Net export month")
    _ax.fill_between(_v.index, _v.values, 0, where=(_v.values < 0),
                     color=COL["import"], alpha=0.85, zorder=3,
                     label="Net import month")
    _ax.axhline(0, color=COL["ink"], lw=1.2)
    _ax.xaxis.set_major_locator(mdates.YearLocator())
    _ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _ax.set_title("Monthly net balance — the seasonal rhythm")
    _ax.set_ylabel("Net balance (TWh)")
    _ax.legend(loc="upper right")
    save_fig(_fig, "trade_07_monthly_seasonal.png", FIGS)
    _fig
    return


@app.cell
def fig8(FIGS, data_ready, heat_month_year, mo, np, plt, save_fig):
    mo.stop(not data_ready)
    _fig, (_ax, _cax) = plt.subplots(
        1, 2, figsize=(10.5, 5.4),
        gridspec_kw={"width_ratios": [32, 1], "wspace": 0.08},
    )
    _M = heat_month_year
    _lim = max(float(np.nanmax(np.abs(_M.values))), 1e-9)
    # Vector cells avoid auxiliary PNG files in Matplotlib's PGF output.
    _im = _ax.pcolormesh(
        np.arange(_M.shape[1] + 1) - 0.5,
        np.arange(_M.shape[0] + 1) - 0.5,
        _M.values,
        cmap="RdBu", vmin=-_lim, vmax=_lim, shading="flat",
    )
    _months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    _ax.set_yticks(range(len(_M.index)))
    _ax.set_yticklabels(_months)
    _ax.set_xticks(range(len(_M.columns)))
    _ax.set_xticklabels(_M.columns)
    _ax.set_xlim(-0.5, _M.shape[1] - 0.5)
    _ax.set_ylim(_M.shape[0] - 0.5, -0.5)
    for _i in range(_M.shape[0]):
        for _j in range(_M.shape[1]):
            _v = _M.values[_i, _j]
            if not np.isnan(_v):
                _ax.text(_j, _i, f"{_v:+.1f}", ha="center", va="center",
                         fontsize=8.5,
                         color="white" if abs(_v) > _lim * 0.55 else "#0f172a")
    _edges = np.linspace(-_lim, _lim, 65)
    _centres = (_edges[:-1] + _edges[1:]) / 2
    _step = _edges[1] - _edges[0]
    _cax.barh(
        _centres, np.ones_like(_centres), height=_step * 1.02,
        color=plt.get_cmap("RdBu")((_centres + _lim) / (2 * _lim)),
        edgecolor="none",
    )
    _cax.set_xlim(0, 1)
    _cax.set_ylim(-_lim, _lim)
    _cax.set_xticks([])
    _cax.yaxis.tick_right()
    _cax.yaxis.set_label_position("right")
    _cax.set_ylabel("Net balance (TWh)")
    _cax.grid(False)
    for _spine in _cax.spines.values():
        _spine.set_visible(False)
    _ax.set_title("Month x year heatmap — seasonality and trend together")
    _ax.grid(False)
    save_fig(_fig, "trade_08_month_year_heatmap.png", FIGS)
    _fig
    return


@app.cell
def fig9(COL, FIGS, PALETTE, annual_net, data_ready, mo, plt, save_fig):
    mo.stop(not data_ready)
    _fig, _ax = plt.subplots(figsize=(11, 6))
    _order = annual_net.iloc[-1].sort_values(ascending=False).index.tolist()
    for _c in _order:
        _ax.plot(annual_net.index, annual_net[_c],
                 marker="o", ms=5.5, lw=2.2,
                 color=PALETTE.get(_c, "#94a3b8"), label=_c)
    _ax.axhline(0, color=COL["ink"], lw=1, ls="--", alpha=0.5)
    _ax.set_title("Evolution of each trading relationship, 2019 to 2025")
    _ax.set_ylabel("Net trade (TWh)   +export / -import")
    _ax.set_xlabel("Year")
    _ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", frameon=False)
    save_fig(_fig, "trade_09_relationship_evolution.png", FIGS)
    _fig
    return


@app.cell
def year_pick_ui(annual_net, data_ready, mo):
    mo.stop(not data_ready)
    year_pick = mo.ui.dropdown(
        options=[str(y) for y in annual_net.index],
        value=str(annual_net.index[-1]),
        label="Inspect one year",
    )
    mo.md(f"## 3. Interactive: pick a year\n\n{year_pick}")
    return (year_pick,)


@app.cell
def year_view(
    COL,
    annual_exp,
    annual_imp,
    annual_net,
    data_ready,
    mo,
    np,
    plt,
    year_pick,
):
    mo.stop(not data_ready)
    _yr = int(year_pick.value)
    _e = annual_exp.loc[_yr]
    _i = annual_imp.loc[_yr]
    _order = (_e + _i).sort_values(ascending=False).index.tolist()

    _fig, _ax = plt.subplots(figsize=(10.5, 5.6))
    _pos = np.arange(len(_order))
    _ax.barh(_pos - 0.2, [_e[n] for n in _order], height=0.4,
             color=COL["export"], label="Exports to", zorder=3)
    _ax.barh(_pos + 0.2, [_i[n] for n in _order], height=0.4,
             color=COL["import"], label="Imports from", zorder=3)
    _ax.set_yticks(_pos)
    _ax.set_yticklabels(_order)
    _ax.invert_yaxis()
    _ax.set_xlabel("Energy (TWh)")
    _net = annual_net.loc[_yr].sum()
    _pos_label = "net exporter" if _net >= 0 else "net importer"
    _ax.set_title(f"{_yr} per-neighbour flows   "
                  f"(overall net {_net:+.1f} TWh, {_pos_label})")
    _ax.legend(loc="lower right")
    _ax.grid(axis="y", visible=False)
    _fig
    return


@app.cell
def outro(mo):
    mo.md(r"""
    ## 4. What the figures set up

    Read together the nine figures document one story:

    - The **balance turned gradually** into net import; there is no single
      crash year.
    - **Different neighbours drive the swing** — some borders flip from
      export to import while others do not.
    - **Germany imports and exports at the same time**, in the same year and
      often in the same week — the mark of an integrated market routing
      power by price.
    - Trade has a **clear seasonal rhythm**, with imports deepening in winter
      and easing (or flipping to export) in summer.

    The next chapter of the report — *Net Importer: Strategy or Shortage?* —
    takes each of these observations and asks *why*.

    Every figure above has been written to `figures/` as a 220-dpi PNG
    preview and as a LuaLaTeX-compatible `.pgf` file. Upload the nine PGF
    files to the thesis and import them with `\safepgfinput`.
    """)
    return


if __name__ == "__main__":
    app.run()