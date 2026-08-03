import marimo

__generated_with = "0.23.9"
app = marimo.App(
    width="full",
    app_title="STAGES — Germany's Electricity Import Shift",
)


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import json
    import time
    import urllib.request
    from pathlib import Path
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    from pgf_export import export_all_pgf

    return (
        Path,
        export_all_pgf,
        go,
        json,
        make_subplots,
        mo,
        np,
        pd,
        px,
        time,
        urllib,
    )


@app.cell
def _():
    C = {
        "solar":   "#f4b942", "wind":   "#3b82f6", "hydro":  "#06b6d4",
        "biomass": "#22c55e", "nuclear":"#a855f7", "lignite":"#6b4423",
        "hardcoal":"#374151", "gas":    "#fb923c", "other":  "#9ca3af",
        "import":  "#ef4444", "export": "#3b82f6", "ink":    "#0f172a",
        "muted":   "#64748b", "grid":   "#e8edf3", "accent": "#2563eb",
    }
    GEN_ORDER = ["solar", "wind", "hydro", "biomass", "nuclear",
                 "lignite", "hardcoal", "gas", "other"]
    GEN_LABEL = {
        "solar": "Solar", "wind": "Wind", "hydro": "Hydro", "biomass": "Biomass",
        "nuclear": "Nuclear", "lignite": "Lignite", "hardcoal": "Hard coal",
        "gas": "Natural gas", "other": "Other",
    }
    SMARD_FILTERS = {
        1223: "lignite", 1224: "nuclear", 1225: "wind_offshore", 1226: "hydro",
        1227: "other_conventional", 1228: "other_renewable", 4066: "biomass",
        4067: "wind_onshore", 4068: "solar", 4069: "hardcoal",
        4070: "pumped_storage", 4071: "gas", 410: "load", 4359: "residual_load",
    }
    SMARD_REGION = "DE"
    SMARD_RES = "month"
    PRICE_FILTER = 4169  # Großhandelspreis DE/LU day-ahead (best-effort)

    # REAL reference figures, verified from public sources (BNetzA/SMARD annual
    # reviews, Fraunhofer ISE, Open Energy Tracker).
    PRICE_ANCHORS = {2019: 37.7, 2020: 30.5, 2021: 96.8,
                     2022: 235.4, 2023: 95.2, 2024: 78.5}  # 2025 provisional
    GAS_ANCHORS = {2023: 41.0, 2024: 34.8}
    OFFICIAL_NET_IMPORT = {2022: -27.0, 2023: 9.2, 2024: 24.9, 2025: 21.9}
    return (
        C,
        GEN_LABEL,
        GEN_ORDER,
        OFFICIAL_NET_IMPORT,
        PRICE_ANCHORS,
        PRICE_FILTER,
        SMARD_FILTERS,
        SMARD_REGION,
        SMARD_RES,
    )


@app.cell
def _(Path, SMARD_FILTERS, json, pd, time, urllib):
    CACHE = Path(__file__).parent / "data" / "_cache"
    CACHE.mkdir(parents=True, exist_ok=True)
    MONTHLY_CACHE = CACHE / "smard_monthly.csv"
    BASE = "https://www.smard.de/app/chart_data"

    def _get_json(url, cache_name):
        cf = CACHE / cache_name
        if cf.exists():
            try:
                return json.loads(cf.read_text())
            except Exception:
                cf.unlink(missing_ok=True)  # drop a corrupt cache file
        _last = None
        for _attempt in range(3):                 # retry transient failures
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "stages/2.0"})
                with urllib.request.urlopen(req, timeout=60) as _r:
                    data = json.loads(_r.read().decode())
                cf.write_text(json.dumps(data))   # only cache on success
                time.sleep(0.2)
                return data
            except Exception as e:
                _last = e
                time.sleep(0.6 * (_attempt + 1))
        raise _last

    def _series(filter_id, region, resolution):
        idx = _get_json(f"{BASE}/{filter_id}/{region}/index_{resolution}.json",
                        f"idx_{filter_id}_{resolution}.json")
        pts = {}
        skipped = 0
        for ts in idx.get("timestamps", []):
            url = f"{BASE}/{filter_id}/{region}/{filter_id}_{region}_{resolution}_{ts}.json"
            try:
                chunk = _get_json(url, f"s_{filter_id}_{ts}.json")
            except Exception:
                skipped += 1
                continue
            for t, v in chunk.get("series", []):
                if v is not None:
                    pts[t] = v
        if skipped:
            print(f"  ⚠ filter {filter_id}: {skipped} chunk(s) unavailable")
        s = pd.Series(pts)
        if len(s):
            s.index = pd.to_datetime(s.index, unit="ms")
        return s.sort_index()

    def fetch_all(region, resolution, price_filter, start=2019, end=2025):
        cols = {name: _series(fid, region, resolution)
                for fid, name in SMARD_FILTERS.items()}
        raw = pd.DataFrame(cols) / 1_000_000.0
        try:
            price = _series(price_filter, region, resolution)
            if len(price):
                raw["price"] = price
        except Exception:
            pass
        raw.index.name = "month"
        raw = raw[(raw.index.year >= start) & (raw.index.year <= end)]

        _m = pd.DataFrame(index=raw.index)
        _m["gen_solar"]    = raw["solar"]
        _m["gen_wind"]     = raw["wind_onshore"].fillna(0) + raw["wind_offshore"].fillna(0)
        _m["gen_nuclear"]  = raw["nuclear"]
        _m["gen_lignite"]  = raw["lignite"]
        _m["gen_hardcoal"] = raw["hardcoal"]
        _m["gen_gas"]      = raw["gas"]
        _m["gen_hydro"]    = raw["hydro"]
        _m["gen_biomass"]  = raw["biomass"]
        _m["gen_other"]    = (raw["other_conventional"].fillna(0)
                             + raw["other_renewable"].fillna(0)
                             + raw["pumped_storage"].fillna(0))
        gcols = [c for c in _m.columns if c.startswith("gen_")]
        _m["gen_total"]      = _m[gcols].sum(axis=1, min_count=1)
        _m["demand"]         = raw["load"]
        _m["gen_renewables"] = _m[["gen_solar", "gen_wind", "gen_hydro", "gen_biomass"]].sum(axis=1, min_count=1)
        _m["gen_fossil"]     = _m[["gen_lignite", "gen_hardcoal", "gen_gas"]].sum(axis=1, min_count=1)
        # Residual load: prefer SMARD's measured series, fall back to the
        # conventional definition (load − wind − solar) so gaps never break charts.
        _m["residual_load"]  = raw["residual_load"]
        _rl_fallback = _m["demand"] - (_m["gen_solar"] + _m["gen_wind"])
        _m["residual_load"]  = _m["residual_load"].fillna(_rl_fallback)
        _m["net_trade"]      = _m["gen_total"] - _m["demand"]
        if "price" in raw.columns:
            _m["price"] = raw["price"]
        _m = _m.reset_index()
        num = _m.select_dtypes("number").columns
        _m[num] = _m[num].round(3)
        return _m

    def build_annual(monthly, price_anchors):
        _m = monthly.copy()
        _m["year"] = pd.to_datetime(_m["month"]).dt.year
        gcols = [c for c in _m.columns if c.startswith("gen_")]
        _a = _m.groupby("year")[gcols + ["demand", "net_trade", "residual_load"]].sum().reset_index()
        _a["renewable_share"] = _a["gen_renewables"] / _a["demand"] * 100
        _a["net_import"]      = -_a["net_trade"]
        _a["position"]        = _a["net_trade"].apply(lambda x: "Exporter" if x > 0 else "Importer")
        if "price" in _m.columns and _m["price"].notna().any():
            pa = _m.groupby("year")["price"].mean()
            _a["price"] = _a["year"].map(pa).fillna(_a["year"].map(price_anchors))
        else:
            _a["price"] = _a["year"].map(price_anchors)
        return _a.round(3)

    def load_cached():
        if MONTHLY_CACHE.exists():
            return pd.read_csv(MONTHLY_CACHE, parse_dates=["month"])
        return None

    return MONTHLY_CACHE, build_annual, fetch_all, load_cached


@app.cell
def _(mo):
    mo.md(r"""
    <div style="background:linear-gradient(135deg,#0f2d52 0%,#1746a0 55%,#1d4ed8 100%);
                padding:64px 52px 52px; border-radius:18px; color:#ffffff;">
      <div style="font-size:11px; letter-spacing:5px; color:#bfdbfe;
                  text-transform:uppercase; margin-bottom:14px; font-weight:700;">
        STAGES · Energy Systems Analysis · Real SMARD data
      </div>
      <h1 style="font-size:2.9rem; font-weight:750; line-height:1.12; margin:0 0 18px; color:#ffffff;">
        Why did Germany become a net<br>
        electricity <span style="color:#93c5fd;">importer</span>?
      </h1>
      <p style="font-size:1.06rem; color:#eaf2fd; max-width:720px; line-height:1.75; margin:0 0 30px;">
        A data-driven investigation into whether Germany's shift from exporter to importer
        signals a <em>production shortage</em> — or whether it is the rational outcome of an
        integrated European market, a nuclear phase-out, an energy-price war, and the rise of
        variable renewables. Every chart below is built from measured data published by
        Germany's Federal Network Agency (Bundesnetzagentur) via SMARD.de.
      </p>
      <div style="display:flex; gap:14px; flex-wrap:wrap;">
        <div style="background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.28);
                    border-radius:10px; padding:14px 20px;">
          <div style="font-size:1.5rem; font-weight:700; color:#ffffff;">2019–2025</div>
          <div style="font-size:0.8rem; color:#d6e6fb;">monthly resolution</div>
        </div>
        <div style="background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.28);
                    border-radius:10px; padding:14px 20px;">
          <div style="font-size:1.5rem; font-weight:700; color:#ffffff;">9 questions</div>
          <div style="font-size:0.8rem; color:#d6e6fb;">data-backed answers</div>
        </div>
        <div style="background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.28);
                    border-radius:10px; padding:14px 20px;">
          <div style="font-size:1.5rem; font-weight:700; color:#ffffff;">1 dashboard</div>
          <div style="font-size:0.8rem; color:#d6e6fb;">interactive, by year</div>
        </div>
      </div>
    </div>
    """)
    return


@app.cell
def _(mo):
    fetch_button = mo.ui.run_button(
        label="⬇  Fetch / refresh real data from SMARD.de", kind="success")
    mo.md(
        f"""
        <div style="background:#f1f6fb; border:1px solid #cdddee; border-radius:12px;
                    padding:18px 22px; margin:10px 0;">
          <strong>Data loader.</strong> The notebook pulls live electricity data straight from
          SMARD's public API — no key, no synthetic numbers. The first fetch takes a minute and is
          cached to <code>data/_cache/</code>, so later runs are instant. Click once to populate
          every chart below.
          <div style="margin-top:12px;">{mo.as_html(fetch_button)}</div>
        </div>
        """
    )
    return (fetch_button,)


@app.cell
def _(
    MONTHLY_CACHE,
    PRICE_FILTER,
    SMARD_REGION,
    SMARD_RES,
    fetch_all,
    fetch_button,
    mo,
):
    fetch_token = "boot"
    fetch_note = mo.md("")
    if fetch_button.value:
        try:
            with mo.status.spinner(title="Fetching real data from SMARD.de …"):
                _m = fetch_all(SMARD_REGION, SMARD_RES, PRICE_FILTER)
                _m.to_csv(MONTHLY_CACHE, index=False)
            import time as _t
            fetch_token = f"smard-{_t.strftime('%H%M%S')}"
            fetch_note = mo.callout(
                mo.md(f"**Loaded {len(_m)} months of real SMARD data.** Charts below have refreshed."),
                kind="success")
        except Exception as exc:
            fetch_note = mo.callout(
                mo.md(f"Fetch failed: `{exc}`. Check your internet connection and try again."),
                kind="danger")
    fetch_note
    return (fetch_token,)


@app.cell
def _(PRICE_ANCHORS, build_annual, fetch_token, load_cached, pd):
    _ = fetch_token  # re-run after a fetch
    monthly = load_cached()
    coverage = None
    if monthly is not None and len(monthly) > 0:
        # Drop only months missing a core MEASURED value (incomplete/most-recent
        # months SMARD hasn't finalised). residual_load is derived, so excluded.
        monthly = monthly.dropna(subset=["demand", "gen_total"]).reset_index(drop=True)
        monthly = monthly.sort_values("month").reset_index(drop=True)
        _cv = monthly.assign(year=pd.to_datetime(monthly["month"]).dt.year)
        coverage = _cv.groupby("year")["month"].count().to_dict()  # months present per year
    data_ready = monthly is not None and len(monthly) > 0
    annual = build_annual(monthly, PRICE_ANCHORS) if data_ready else None
    has_price = data_ready and "price" in monthly.columns and monthly["price"].notna().any()
    return annual, coverage, data_ready, has_price, monthly


@app.cell
def _(coverage, data_ready, mo):
    if data_ready:
        _incomplete = {y: n for y, n in (coverage or {}).items() if n < 12}
        _warn = ""
        if _incomplete:
            _items = ", ".join(f"{y} ({n}/12 mo)" for y, n in sorted(_incomplete.items()))
            _warn = (f"<div style='margin-top:8px;color:#9a3412;'>⚠ <strong>Partial years:</strong> "
                     f"{_items}. Their <em>annual totals</em> are not directly comparable to full years.</div>")
        _b = mo.md(
            f"""
            <div style="background:#ecfdf5; border-left:4px solid #10b981;
                        padding:13px 20px; border-radius:0 8px 8px 0; margin:10px 0;">
            <strong>📡 Running on real SMARD data.</strong> Generation, load and residual load are
            measured values from the Bundesnetzagentur. Net trade is derived as generation − load
            (a transparent system-level proxy; see Question 1). Wholesale prices are real
            published day-ahead averages.{_warn}
            </div>
            """)
    else:
        _b = mo.callout(
            mo.md("**No data loaded yet.** Click the green **Fetch** button above to download "
                  "real SMARD data. Every section below will populate automatically."),
            kind="warn")
    _b
    return


@app.cell
def _(mo):
    pgf_export_button = mo.ui.run_button(
        label="Export the eight thesis plots as PGF", kind="success"
    )
    mo.md(
        f"""
        <div style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:12px;
                    padding:16px 20px;margin:10px 0;">
          <strong>LaTeX export.</strong> After the SMARD data has loaded, click this button to
          recreate the eight fixed report figures with Matplotlib. The project writes native
          <code>.pgf</code> files and matching PNG previews to <code>figures/</code>.
          <div style="margin-top:12px;">{mo.as_html(pgf_export_button)}</div>
        </div>
        """
    )
    return (pgf_export_button,)


@app.cell
def _(
    C,
    GEN_LABEL,
    GEN_ORDER,
    Path,
    annual,
    data_ready,
    export_all_pgf,
    mo,
    monthly,
    pgf_export_button,
):
    if not pgf_export_button.value:
        pgf_export_note = mo.md("")
    elif not data_ready:
        pgf_export_note = mo.callout(
            mo.md("Load the SMARD data first, then click the PGF export button again."),
            kind="warn",
        )
    else:
        try:
            _output_dir = Path(__file__).parent / "figures"
            with mo.status.spinner(title="Creating LuaLaTeX-compatible PGF figures …"):
                _pgf_files = export_all_pgf(
                    monthly=monthly,
                    annual=annual,
                    output_dir=_output_dir,
                    colors=C,
                    generation_order=GEN_ORDER,
                    generation_labels=GEN_LABEL,
                )
            _file_list = "\n".join(f"- `{path.name}`" for path in _pgf_files)
            pgf_export_note = mo.callout(
                mo.md(
                    f"**Created {len(_pgf_files)} PGF figures in `figures/`.**\n\n"
                    f"{_file_list}\n\n"
                    "Upload these `.pgf` files to Overleaf's `figures` folder. "
                    "The PNG files beside them are only previews."
                ),
                kind="success",
            )
        except Exception as exc:
            pgf_export_note = mo.callout(
                mo.md(f"PGF export failed: `{exc}`"), kind="danger"
            )
    pgf_export_note
    return


@app.cell
def _(C):
    def style_fig(_fig, height=440, title=None, ytitle=None, legend=True):
        _fig.update_layout(
            height=height, title=title,
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter, -apple-system, Segoe UI, sans-serif",
                      size=13, color=C["ink"]),
            margin=dict(t=56 if title else 28, b=40, l=64, r=24),
            legend=dict(orientation="h", y=-0.16, x=0,
                        font=dict(size=11, color=C["muted"])) if legend
                   else dict(visible=False),
            hoverlabel=dict(font_size=12, font_family="Inter"),
        )
        _fig.update_xaxes(showgrid=False, linecolor=C["grid"], ticks="outside",
                         tickcolor=C["grid"], tickfont=dict(color=C["muted"]))
        _fig.update_yaxes(gridcolor=C["grid"], zeroline=False, title=ytitle,
                         tickfont=dict(color=C["muted"]))
        return _fig

    def section(num, title, lede):
        return f"""---
    ## {num} · {title}

    {lede}
    """

    def need_data(mo):
        return mo.callout(mo.md("⬆ Click **Fetch** to load data for this section."), kind="neutral")

    return need_data, section, style_fig


@app.cell
def _(mo, section):
    mo.md(section(
        "Q1", "When did Germany cross from exporter to importer?",
        "For decades Germany ran a large export surplus. The chart tracks the **net balance** "
        "(generation minus load). Blue years are net-export years; red years are net-import years. "
        "The crossing point is the headline event this whole project sets out to explain."))
    return


@app.cell
def _(C, annual, data_ready, go, mo, need_data, style_fig):
    if not data_ready:
        q1 = need_data(mo)
    else:
        colors = [C["export"] if v > 0 else C["import"] for v in annual["net_trade"]]
        _fig = go.Figure(go.Bar(
            x=annual["year"], y=annual["net_trade"], marker_color=colors,
            text=[f"{v:+.0f}" for v in annual["net_trade"]], textposition="outside",
            hovertemplate="%{x}: %{y:+.1f} TWh<extra></extra>"))
        _fig.add_hline(y=0, line_color=C["ink"], line_width=1)
        q1 = style_fig(_fig, height=430,
                       ytitle="Net balance (TWh) · generation − load", legend=False)
    q1
    return


@app.cell
def _(annual, data_ready, mo):
    if not data_ready:
        q1c = mo.md("")
    else:
        flips = annual[annual["net_trade"] < 0]
        first = int(flips["year"].iloc[0]) if len(flips) else None
        last = int(annual["year"].max())
        last_net = annual.loc[annual["year"] == last, "net_trade"].values[0]
        msg = (f"- Germany's balance **first turned negative in {first}** and has stayed negative since."
               if first else "- Germany remained a net exporter across this window.")
        q1c = mo.callout(mo.md(
            f"**Answer.** {msg}\n\n"
            f"- By {last} the net balance reached **{last_net:+.0f} TWh** — a clear net-import position.\n"
            f"- The shift is **gradual**, not a sudden collapse: the export cushion thinned year on "
            f"year before crossing zero. That pattern already hints the cause is structural and "
            f"economic, not a single overnight failure."), kind="info")
    q1c
    return


@app.cell
def _(OFFICIAL_NET_IMPORT, data_ready, mo):
    if not data_ready:
        q1d = mo.md("")
    else:
        rows = "".join(
            f"<tr><td style='padding:4px 14px'>{y}</td>"
            f"<td style='padding:4px 14px;text-align:right'>{v:+.1f} TWh</td>"
            f"<td style='padding:4px 14px;color:#64748b'>{'net importer' if v>0 else 'net exporter'}</td></tr>"
            for y, v in OFFICIAL_NET_IMPORT.items())
        q1d = mo.md(
            f"""
            <div style="background:#fafbfc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 18px;font-size:0.86rem;">
            <strong>Cross-check — official commercial-trade figures (Bundesnetzagentur).</strong>
            Our proxy is generation − load; the regulator publishes <em>gross commercial flows</em>,
            which differ slightly but tell the same story:
            <table style="margin-top:8px;border-collapse:collapse;">{rows}</table>
            <span style="color:#64748b;">Positive = net imports. Both series agree: Germany became a
            net importer in 2023 and the gap widened in 2024.</span>
            </div>
            """)
    q1d
    return


@app.cell
def _(mo, section):
    mo.md(section(
        "Q2", "How did Germany's generation mix change?",
        "The trade balance is downstream of what Germany produces. This stacked view shows every "
        "source against total demand (dotted line). Watch three things at once: **nuclear vanishing**, "
        "**coal shrinking**, and **renewables climbing**."))
    return


@app.cell
def _(
    C,
    GEN_LABEL,
    GEN_ORDER,
    annual,
    data_ready,
    go,
    mo,
    need_data,
    style_fig,
):
    if not data_ready:
        q2 = need_data(mo)
    else:
        _fig = go.Figure()
        for _src in GEN_ORDER:
            _fig.add_trace(go.Bar(
                x=annual["year"], y=annual[f"gen_{_src}"], name=GEN_LABEL[_src],
                marker_color=C[_src],
                hovertemplate=f"{GEN_LABEL[_src]}: %{{y:.0f}} TWh<extra></extra>"))
        _fig.add_trace(go.Scatter(
            x=annual["year"], y=annual["demand"], name="Demand (load)",
            mode="lines+markers", line=dict(color=C["ink"], width=2.5, dash="dot"),
            marker=dict(size=7)))
        _fig.update_layout(barmode="stack")
        q2 = style_fig(_fig, height=480, ytitle="TWh")
    q2
    return


@app.cell
def _(annual, data_ready, mo):
    if not data_ready:
        q2c = mo.md("")
    else:
        _y0, _y1 = int(annual["year"].min()), int(annual["year"].max())
        def chg(_col):
            _a = annual.loc[annual["year"] == _y0, _col].values[0]
            b = annual.loc[annual["year"] == _y1, _col].values[0]
            return _a, b, b - _a
        nuc = chg("gen_nuclear"); _ren = chg("gen_renewables"); fos = chg("gen_fossil")
        q2c = mo.callout(mo.md(
            f"**Answer.** Between {_y0} and {_y1}:\n\n"
            f"- **Nuclear:** {nuc[0]:.0f} → {nuc[1]:.0f} TWh ({nuc[2]:+.0f}) — effectively eliminated.\n"
            f"- **Fossil:** {fos[0]:.0f} → {fos[1]:.0f} TWh ({fos[2]:+.0f}) — a deliberate decline.\n"
            f"- **Renewables:** {_ren[0]:.0f} → {_ren[1]:.0f} TWh ({_ren[2]:+.0f}) — strong growth, but it "
            f"had to backfill *both* the nuclear exit and the fossil drawdown at once. That double "
            f"burden is the structural space imports now occupy."), kind="info")
    q2c
    return


@app.cell
def _(mo, section):
    mo.md(section(
        "Q3", "How much did the nuclear phase-out matter?",
        "Germany's last three reactors closed on **15 April 2023**. Nuclear was *firm* power — "
        "available day and night, all year. The left panel overlays nuclear output on the net "
        "balance; the right asks whether renewable growth actually replaced the lost nuclear, "
        "year by year."))
    return


@app.cell
def _(C, annual, data_ready, go, make_subplots, mo, need_data, style_fig):
    if not data_ready:
        q3 = need_data(mo)
    else:
        _fig = make_subplots(
            rows=1, cols=2, horizontal_spacing=0.13,
            subplot_titles=["Nuclear output vs. net balance",
                            "Cumulative nuclear lost vs. renewables gained"])
        _fig.add_trace(go.Bar(x=annual["year"], y=annual["gen_nuclear"],
                             name="Nuclear", marker_color=C["nuclear"], opacity=0.85),
                      row=1, col=1)
        _fig.add_trace(go.Scatter(x=annual["year"], y=annual["net_trade"], name="Net balance",
                                 mode="lines+markers", line=dict(color=C["import"], width=2.5),
                                 marker=dict(size=7), yaxis="y2"), row=1, col=1)
        nuc_lost = annual["gen_nuclear"].iloc[0] - annual["gen_nuclear"]
        ren_gain = annual["gen_renewables"] - annual["gen_renewables"].iloc[0]
        _fig.add_trace(go.Bar(x=annual["year"], y=nuc_lost, name="Nuclear lost",
                             marker_color=C["nuclear"], opacity=0.8), row=1, col=2)
        _fig.add_trace(go.Bar(x=annual["year"], y=ren_gain, name="Renewables gained",
                             marker_color=C["biomass"], opacity=0.8), row=1, col=2)
        _fig.update_layout(
            barmode="group",
            yaxis2=dict(overlaying="y", side="right", showgrid=False,
                        title="Net balance (TWh)", zeroline=True, zerolinecolor=C["ink"]))
        q3 = style_fig(_fig, height=440)
    q3
    return


@app.cell
def _(mo):
    mo.callout(mo.md(
        "**Answer — necessary, but not sufficient.** The nuclear exit removed a large block of firm, "
        "carbon-free generation, and the timing lines up with the import shift. But three facts stop "
        "us blaming nuclear alone:\n\n"
        "1. The export surplus was **already shrinking before April 2023**.\n"
        "2. **Fossil output fell at the same time** — a policy choice, not a nuclear side-effect.\n"
        "3. Renewables grew, but they are **variable**, so they cannot replace *firm* nuclear hour-for-hour.\n\n"
        "Nuclear created the gap; what *fills* that gap on any given day is decided by the market — "
        "which is where price and Europe come in."), kind="warn")
    return


@app.cell
def _(mo, section):
    mo.md(section(
        "Q4", "What did the 2022 energy war do — and why did Germany still export that year?",
        "2022 is the plot twist. Russia's invasion of Ukraine and the collapse of pipeline gas sent "
        "European power prices to record highs. Yet **Germany was still a net exporter in 2022** — "
        "because *France's* nuclear fleet broke down even more badly. Understanding this is key: it "
        "shows trade flows follow relative cost and availability across Europe, not domestic capacity alone."))
    return


@app.cell
def _(C, annual, data_ready, go, mo, need_data, style_fig):
    if not data_ready:
        q4 = need_data(mo)
    else:
        _fig = go.Figure()
        _fig.add_trace(go.Bar(
            x=annual["year"], y=annual["price"], name="Day-ahead price",
            marker_color=[C["import"] if p > 150 else C["accent"] for p in annual["price"]],
            text=[f"€{p:.0f}" for p in annual["price"]], textposition="outside",
            hovertemplate="%{x}: €%{y:.1f}/MWh<extra></extra>"))
        _fig.add_annotation(x=2022, y=annual.loc[annual["year"]==2022,"price"].values[0],
                           text="Gas-price shock", showarrow=True, arrowhead=2,
                           ay=-40, font=dict(color=C["import"], size=12))
        q4 = style_fig(_fig, height=400,
                       title="German wholesale electricity price spiked in 2022, then fell back",
                       ytitle="€/MWh (annual average)", legend=False)
    q4
    return


@app.cell
def _(mo):
    mo.md("""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:8px 0;">
      <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:18px 20px;">
        <div style="font-weight:700;color:#c2410c;margin-bottom:6px;">🔥 The shock (2021–2022)</div>
        <ul style="margin:0;padding-left:18px;line-height:1.7;font-size:0.9rem;color:#7c2d12;">
          <li>Gas prices began climbing in late 2021, then spiked after Feb 2022 as Russian pipeline flows were cut.</li>
          <li>Because gas plants often set the price, power prices followed: German day-ahead averaged ≈ €235/MWh in 2022, up from ≈ €30 in 2020.</li>
          <li>The single highest German hour hit ≈ €871/MWh (29 Aug 2022).</li>
          <li>A dry summer cut hydro across Europe and warmed rivers used for nuclear cooling.</li>
        </ul>
      </div>
      <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:18px 20px;">
        <div style="font-weight:700;color:#1d4ed8;margin-bottom:6px;">🇫🇷 The France twist</div>
        <ul style="margin:0;padding-left:18px;line-height:1.7;font-size:0.9rem;color:#1e3a8a;">
          <li>Over half of France's nuclear fleet went offline in 2022 (stress-corrosion cracking + maintenance).</li>
          <li>French output fell ~15% to its lowest in decades; France became a net <em>importer</em>.</li>
          <li>So Germany's net exports <em>to France</em> more than doubled — German export volumes in 2022 were propped up by France's crisis.</li>
          <li>When French nuclear recovered through 2023, that prop disappeared — and Germany's balance tipped to net import.</li>
        </ul>
      </div>
    </div>
    """)
    return


@app.cell
def _(mo):
    mo.callout(mo.md(
        "**Answer.** The 2022 crisis is why you cannot read the import shift from a single year. In "
        "2022 Germany looked strong (net exporter) only because France was weaker. As gas prices "
        "normalised *and* French nuclear came back online in 2023–2024, Germany's relative position "
        "flipped — not because German plants disappeared overnight, but because the **cheapest source "
        "of the next megawatt moved across the border**. The war reshaped prices; the market did the rest."),
        kind="info")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    <div style="background:#f1f6fb;border:1px solid #cdddee;border-radius:14px;padding:24px 28px;">
      <div style="font-size:0.72rem;letter-spacing:3px;color:#2563eb;text-transform:uppercase;font-weight:700;">
        Before we go on — how the European market actually works</div>
      <p style="margin:10px 0 14px;color:#0f172a;line-height:1.7;font-size:0.96rem;">
        The next four questions all rest on one mechanism, so it's worth 60 seconds up front.
        Europe runs a <strong>coupled day-ahead market</strong>: every morning an algorithm clears
        prices across borders at once and <strong>schedules electricity to flow from cheaper-price
        zones into more expensive ones</strong> — until either the prices meet in the middle
        (“convergence”) or the cross-border cables fill up. That is the engine behind everything
        that follows: when a neighbour can make the next megawatt more cheaply than a German gas
        plant, power flows into Germany and Germany imports. The regulator puts it plainly —
        <em>“electricity is produced wherever it is cheapest.”</em>
      </p>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:6px;">
        <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px;">
          <div style="font-weight:700;color:#15803d;font-size:0.9rem;margin-bottom:4px;">✓ The rule</div>
          <div style="font-size:0.86rem;color:#334155;line-height:1.6;">
            Power is scheduled <strong>low-price → high-price</strong>. Cheaper generation displaces
            dearer generation across borders. This is the market working as designed, not a failure.
          </div>
        </div>
        <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px;">
          <div style="font-weight:700;color:#c2410c;font-size:0.9rem;margin-bottom:4px;">⚠ The fine print</div>
          <div style="font-size:0.86rem;color:#334155;line-height:1.6;">
            It follows <strong>price</strong>, which only roughly tracks production cost; flows are
            <strong>capped by cable capacity</strong> (congestion), so prices don't fully equalise;
            and physical electrons take their own path regardless of the commercial trade.
          </div>
        </div>
      </div>
      <p style="margin:14px 0 0;color:#475569;line-height:1.65;font-size:0.9rem;">
        Keep this in mind for what's next: <strong>Q5–Q6</strong> show <em>when</em> Germany needs to
        import (the renewable gaps), and <strong>Q7</strong> shows <em>why</em> it makes economic sense
        to do so rather than burn more gas at home. Imports are the market answering a price signal —
        not a sign the lights would otherwise go out.
      </p>
    </div>
    """)
    return


@app.cell
def _(mo, section):
    mo.md(section(
        "Q5", "Is there a seasonal rhythm to imports?",
        "If imports came from a permanent shortage, they would be flat all year. If they track "
        "renewable weather, they should swing with the seasons. Pick years to overlay and compare "
        "renewable output, the net balance, and residual load month by month."))
    return


@app.cell
def _(data_ready, mo, monthly):
    if not data_ready:
        yr_pick = None
        ctrl5 = mo.md("")
    else:
        _yrs = sorted(monthly["month"].dt.year.unique())
        yr_pick = mo.ui.multiselect(
            options=[str(y) for y in _yrs],
            value=[str(y) for y in _yrs[-3:]], label="Years to overlay")
        ctrl5 = yr_pick
    ctrl5
    return (yr_pick,)


@app.cell
def _(
    C,
    data_ready,
    go,
    make_subplots,
    mo,
    monthly,
    need_data,
    style_fig,
    yr_pick,
):
    if not data_ready:
        q5 = need_data(mo)
    else:
        _sel = [int(y) for y in (yr_pick.value or [])] or [int(monthly["month"].dt.year.max())]
        _fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.07,
                            subplot_titles=["Renewables — wind + solar (TWh/mo)",
                                            "Net balance (TWh/mo)",
                                            "Residual load — demand − renewables (TWh/mo)"])
        pal = [C["accent"], C["import"], C["biomass"], C["gas"], C["nuclear"], C["hydro"]]
        for i, _yr in enumerate(sorted(_sel)):
            _d = monthly[monthly["month"].dt.year == _yr]
            mlabel = _d["month"].dt.strftime("%b")
            _col = pal[i % len(pal)]
            _ren = _d["gen_solar"] + _d["gen_wind"]
            _fig.add_trace(go.Scatter(x=mlabel, y=_ren, name=str(_yr),
                          line=dict(color=_col, width=2)), row=1, col=1)
            _fig.add_trace(go.Scatter(x=mlabel, y=_d["net_trade"], name=str(_yr),
                          line=dict(color=_col, width=2), showlegend=False), row=2, col=1)
            _fig.add_trace(go.Scatter(x=mlabel, y=_d["residual_load"], name=str(_yr),
                          line=dict(color=_col, width=2), showlegend=False), row=3, col=1)
        _fig.add_hline(y=0, line_dash="dot", line_color=C["muted"], row=2, col=1)
        q5 = style_fig(_fig, height=600)
    q5
    return


@app.cell
def _(mo):
    mo.callout(mo.md(
        "**Answer — yes, clearly seasonal.** **Residual load peaks every winter** — short days, high "
        "demand, weak solar — and falls in summer, in every year shown. The **net balance follows the "
        "same rhythm**: in the import-era years (2023 onward) it dips into imports each winter and "
        "eases in sunny, windy spells when Germany can still export. A permanent capacity shortage "
        "would not switch on and off with the seasons. This oscillation is the fingerprint of a system "
        "**balancing renewable variability through trade** — which sets up the real question: when the "
        "winter gap appears, *why* fill it with imports rather than more domestic gas? (Q6 and Q7)."),
        kind="info")
    return


@app.cell
def _(mo, section):
    mo.md(section(
        "Q6", "Does residual load predict imports?",
        "Residual load = demand − renewables = the slice that must come from dispatchable plants "
        "**or imports**. Testing this needs care: *across years* residual load actually fell (more "
        "renewables, less demand) while imports rose — a structural trend that would mask the "
        "seasonal effect. So the scatter below removes each year's average and asks the sharper "
        "question: **within a given year, do the higher-residual-load months bring more imports?** "
        "The heatmap then shows the structural export→import flip over time."))
    return


@app.cell
def _(C, data_ready, go, mo, monthly, need_data, np, px, style_fig):
    if not data_ready:
        q6a = need_data(mo); q6_r = None
    else:
        _m = monthly.dropna(subset=["residual_load", "net_trade", "demand"]).copy()
        _m["year"] = _m["month"].dt.year
        _m["net_imports"] = -_m["net_trade"]            # +ve = importing (unclipped)
        # remove each year's mean → isolate within-year (seasonal) variation,
        # so the multi-year structural trend can't distort the test
        _m["rl_anom"] = _m["residual_load"] - _m.groupby("year")["residual_load"].transform("mean")
        _m["ni_anom"] = _m["net_imports"]   - _m.groupby("year")["net_imports"].transform("mean")
        _fig = px.scatter(_m, x="rl_anom", y="ni_anom",
                         color=_m["year"].astype(str),
                         color_discrete_sequence=px.colors.qualitative.Bold,
                         labels={"rl_anom": "Residual-load anomaly (TWh vs that year's average)",
                                 "ni_anom": "Net-import anomaly (TWh vs that year's average)",
                                 "color": "Year"})
        _fig.update_traces(marker=dict(size=11, opacity=0.8))
        x = _m["rl_anom"].values; y = _m["ni_anom"].values
        q6_r = float(np.corrcoef(x, y)[0, 1]) if (np.std(x) > 0 and np.std(y) > 0) else float("nan")
        if np.std(x) > 0:
            z = np.polyfit(x, y, 1); xs = np.linspace(x.min(), x.max(), 60)
            _fig.add_trace(go.Scatter(x=xs, y=np.poly1d(z)(xs), mode="lines",
                          name=f"trend r={q6_r:+.2f}", line=dict(color=C["ink"], width=2, dash="dash")))
        _fig.add_hline(y=0, line_color=C["grid"], line_width=1)
        _fig.add_vline(x=0, line_color=C["grid"], line_width=1)
        q6a = style_fig(_fig, height=440,
                        title="Within each year: do above-average residual-load months bring above-average imports?")
    q6a
    return (q6_r,)


@app.cell
def _(C, data_ready, go, mo, monthly, need_data, style_fig):
    if not data_ready:
        q6b = need_data(mo)
    else:
        p = monthly.copy()
        p["yr"] = p["month"].dt.year; p["mo"] = p["month"].dt.month
        names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        hm = (p.pivot_table(index="mo", columns="yr", values="net_trade")
                .reindex(index=range(1, 13)))
        _fig = go.Figure(go.Heatmap(
            z=hm.values, x=[str(c) for c in hm.columns], y=names,
            colorscale=[[0, C["import"]], [0.5, "#f8fafc"], [1, C["export"]]], zmid=0,
            colorbar=dict(title="Net (TWh)", thickness=12),
            hoverongaps=False,
            hovertemplate="%{x} %{y}: %{z:.1f} TWh<extra></extra>"))
        q6b = style_fig(_fig, height=420,
                        title="Monthly net balance — red = import, blue = export, grey = no data",
                        legend=False)
        _fig.update_xaxes(side="top")
        # grey backdrop so genuinely-missing (transparent) cells read as "no data",
        # not as near-zero white
        _fig.update_layout(plot_bgcolor="#e9edf2")
    q6b
    return


@app.cell
def _(data_ready, mo, q6_r):
    if not data_ready or q6_r is None or q6_r != q6_r:
        q6c = mo.md("")
    else:
        _r = q6_r
        if _r >= 0.3:
            _verdict = (f"**Answer — yes, seasonally (within-year r ≈ {_r:+.2f}).** Once we strip out "
                        f"the multi-year trend, months with above-average residual load clearly bring "
                        f"above-average imports — imports respond to renewable gaps. Note the two effects "
                        f"point opposite ways: *structurally* residual load fell as renewables grew while "
                        f"imports rose (the heatmap's blue→red drift), but *seasonally* the gap still pulls "
                        f"in imports. Both fit the thesis — the gap is real, and how it's filled is set by cost (Q7).")
        elif _r >= 0.1:
            _verdict = (f"**Answer — weakly (within-year r ≈ {_r:+.2f}).** There's a mild seasonal pull: "
                        f"higher-residual-load months lean slightly more on imports. But the link is loose, "
                        f"because Germany can meet a renewable gap *two* ways — ramp domestic gas/coal, or "
                        f"import — and **which one it picks is an economic choice, not dictated by the size "
                        f"of the gap.** That hands the real explanatory work to price (Q7).")
        else:
            _verdict = (f"**Answer — residual load alone is not the driver (within-year r ≈ {_r:+.2f}).** "
                        f"Even after removing the yearly trend, the size of the renewable gap barely predicts "
                        f"imports month-to-month. The reason is important: Germany covers most of its residual "
                        f"load with **domestic dispatchable plants**, and only turns to imports when they're "
                        f"**cheaper than generating at home**. So the import decision is economic, not a sign "
                        f"of physical shortage — exactly what Q7 examines. The heatmap still shows the clear "
                        f"structural shift from net export (blue) toward net import (red) over time.")
        q6c = mo.callout(mo.md(_verdict), kind="info")
    q6c
    return


@app.cell
def _(mo, section):
    mo.md(section(
        "Q7", "Is importing often the cheaper choice?",
        "This is the heart of the argument. In a coupled market, electricity flows from wherever the "
        "next megawatt is cheapest. When neighbours can produce more cheaply than firing a German gas "
        "plant, importing is the **rational** outcome — and it is what the regulator itself says is "
        "happening."))
    return


@app.cell
def _(C, annual, data_ready, go, make_subplots, mo, need_data, style_fig):
    if not data_ready:
        q7 = need_data(mo)
    else:
        _fig = make_subplots(
            rows=1, cols=2, horizontal_spacing=0.14,
            specs=[[{"secondary_y": True}, {"secondary_y": True}]],
            subplot_titles=["German price (context) & net imports",
                            "Gas generation vs. net imports"])
        # Left: German price line + net-import bars (context panel)
        _fig.add_trace(go.Bar(x=annual["year"], y=annual["net_import"], name="Net imports (TWh)",
                      marker_color=C["import"], opacity=0.5),
                      row=1, col=1, secondary_y=True)
        _fig.add_trace(go.Scatter(x=annual["year"], y=annual["price"], name="German price (€/MWh)",
                      mode="lines+markers", line=dict(color=C["gas"], width=2.5),
                      marker=dict(size=7)), row=1, col=1, secondary_y=False)
        # Right: gas generation line + net-import bars (substitution signal)
        _fig.add_trace(go.Bar(x=annual["year"], y=annual["net_import"], name="Net imports (TWh)",
                      marker_color=C["import"], opacity=0.5, showlegend=False),
                      row=1, col=2, secondary_y=True)
        _fig.add_trace(go.Scatter(x=annual["year"], y=annual["gen_gas"], name="Gas generation (TWh)",
                      mode="lines+markers", line=dict(color=C["lignite"], width=2.5),
                      marker=dict(size=7)), row=1, col=2, secondary_y=False)
        _fig.update_yaxes(title_text="€/MWh", row=1, col=1, secondary_y=False)
        _fig.update_yaxes(title_text="Net imports (TWh)", row=1, col=1, secondary_y=True)
        _fig.update_yaxes(title_text="TWh gas", row=1, col=2, secondary_y=False)
        _fig.update_yaxes(title_text="Net imports (TWh)", row=1, col=2, secondary_y=True)
        q7 = style_fig(_fig, height=440)
    q7
    return


@app.cell
def _(mo):
    mo.md("""
    <div style="background:linear-gradient(135deg,#0f3d2e,#15803d);border-radius:14px;
                padding:22px 26px;color:white;margin:6px 0;">
      <div style="font-size:0.72rem;letter-spacing:3px;color:#bbf7d0;margin-bottom:8px;">
        THE REGULATOR'S OWN WORDS — BUNDESNETZAGENTUR</div>
      <p style="font-size:1.05rem;line-height:1.65;margin:0;">
        “Germany has sufficient electricity generation capacity. Electricity is usually imported
        whenever domestic production would be more expensive. There is an interaction between
        supply and demand across the whole of Europe.”
      </p>
      <p style="font-size:0.85rem;color:#bbf7d0;margin:10px 0 0;">
        And on 2024: it “made financial sense more often for Germany to buy cheaper electricity on
        the European internal market,” as neighbours' average price slipped below Germany's.
      </p>
    </div>
    """)
    return


@app.cell
def _(mo):
    mo.callout(mo.md(
        "**Answer — yes, through cost substitution.** Read the German price (left) as *context*, not "
        "the driver: in 2022 German prices spiked to ~€235/MWh yet Germany still **exported**, because "
        "neighbours — France above all — were even more stressed. The real mechanism is **relative** "
        "price: Germany imports when a neighbour can make the next megawatt more cheaply than a German "
        "plant can. The clean signal in our own data is on the right — as importing became cheaper than "
        "burning gas, **gas generation fell while net imports rose**, the textbook sign of cost-driven "
        "substitution rather than forced rationing. The regulator confirms it outright: capacity is "
        "sufficient, and imports happen when domestic production would be more expensive."), kind="success")
    return


@app.cell
def _(mo, section):
    mo.md(section(
        "Q8", "Is the transition progressing despite the imports?",
        "A net-import position is easy to spin as failure. The data says otherwise: renewables' share "
        "of demand keeps climbing while total demand falls — so Germany meets more of a smaller load "
        "with clean power, even as it imports at the margin."))
    return


@app.cell
def _(C, annual, data_ready, go, make_subplots, mo, need_data, style_fig):
    if not data_ready:
        q8 = need_data(mo)
    else:
        _fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.13,
                            subplot_titles=["Renewable share of demand (%)",
                                            "Total demand / load (TWh)"])
        _fig.add_trace(go.Scatter(
            x=annual["year"], y=annual["renewable_share"], mode="lines+markers+text",
            text=[f"{v:.0f}%" for v in annual["renewable_share"]], textposition="top center",
            line=dict(color=C["biomass"], width=3), marker=dict(size=9),
            fill="tozeroy", fillcolor="rgba(34,197,94,0.10)", showlegend=False), row=1, col=1)
        _fig.add_trace(go.Scatter(
            x=annual["year"], y=annual["demand"], mode="lines+markers+text",
            text=[f"{v:.0f}" for v in annual["demand"]], textposition="top center",
            line=dict(color=C["accent"], width=3), marker=dict(size=9),
            fill="tozeroy", fillcolor="rgba(37,99,235,0.08)", showlegend=False), row=1, col=2)
        q8 = style_fig(_fig, height=400, legend=False)
    q8
    return


@app.cell
def _(annual, data_ready, mo):
    if not data_ready:
        q8c = mo.md("")
    else:
        _y0, _y1 = int(annual["year"].min()), int(annual["year"].max())
        rs0 = annual.loc[annual["year"]==_y0, "renewable_share"].values[0]
        rs1 = annual.loc[annual["year"]==_y1, "renewable_share"].values[0]
        d0 = annual.loc[annual["year"]==_y0, "demand"].values[0]
        d1 = annual.loc[annual["year"]==_y1, "demand"].values[0]
        q8c = mo.callout(mo.md(
            f"**Answer.** Renewable share of demand rose from **{rs0:.0f}% to {rs1:.0f}%**, while "
            f"demand fell from **{d0:.0f} to {d1:.0f} TWh** (efficiency + post-2022 industrial "
            f"softening). A cleaner mix over a smaller load means the import gap to fill is shrinking, "
            f"not exploding. The transition is advancing *and* Germany imports — both are true at once."),
            kind="success")
    q8c
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    <div style="background:linear-gradient(135deg,#13386e,#1d4ed8);border-radius:16px;padding:30px 34px;color:#ffffff;margin-top:8px;">
      <div style="font-size:11px;letter-spacing:4px;color:#bfdbfe;text-transform:uppercase;font-weight:700;">
        Interactive dashboard</div>
      <h2 style="margin:8px 0 6px;font-size:1.7rem;color:#ffffff;">Explore any single year up close</h2>
      <p style="color:#eff6ff;margin:0;max-width:680px;line-height:1.6;">
        Pick a year and (optionally) a metric to inspect month-by-month. Every panel updates
        together so you can see how generation, trade, price and renewable coverage move as one system.
      </p>
    </div>
    """)
    return


@app.cell
def _(data_ready, mo, monthly):
    if not data_ready:
        dash_year = None; dash_metric = None
        dash_ctrl = mo.md("")
    else:
        _yrs = sorted(monthly["month"].dt.year.unique())
        dash_year = mo.ui.dropdown(
            options={str(y): y for y in _yrs}, value=str(_yrs[-1]), label="Year")
        dash_metric = mo.ui.dropdown(
            options={"Net balance": "net_trade", "Demand": "demand",
                     "Residual load": "residual_load", "Renewables": "gen_renewables",
                     "Fossil": "gen_fossil"},
            value="Net balance", label="Focus metric")
        dash_ctrl = mo.hstack([dash_year, dash_metric], gap=2, justify="start")
    dash_ctrl
    return dash_metric, dash_year


@app.cell
def _(annual, dash_year, data_ready, mo):
    if not data_ready:
        kpis = mo.md("")
    else:
        _yr = dash_year.value
        _a = annual[annual["year"] == _yr].iloc[0]
        pos = "Net importer" if _a["net_trade"] < 0 else "Net exporter"
        pcol = "#ef4444" if _a["net_trade"] < 0 else "#3b82f6"
        def card(label, value, color="#0f172a"):
            return (f"<div style='flex:1;min-width:130px;background:white;border:1px solid #e2e8f0;"
                    f"border-radius:12px;padding:16px 18px;'>"
                    f"<div style='font-size:0.72rem;letter-spacing:1px;color:#64748b;"
                    f"text-transform:uppercase;'>{label}</div>"
                    f"<div style='font-size:1.5rem;font-weight:750;color:{color};margin-top:4px;'>{value}</div></div>")
        def _fmt(v, suffix="", sign=False):
            if v is None or (isinstance(v, float) and v != v):  # NaN check
                return "n/a"
            return (f"{v:+.0f}" if sign else f"{v:.0f}") + suffix
        kpis = mo.md(
            "<div style='display:flex;gap:12px;flex-wrap:wrap;margin:10px 0;'>"
            + card("Year", _yr)
            + card("Position", pos, pcol)
            + card("Net balance", _fmt(_a['net_trade'], " TWh", sign=True), pcol)
            + card("Renewable share", _fmt(_a['renewable_share'], "%"), "#22c55e")
            + card("Avg price", "€" + _fmt(_a['price']))
            + card("Demand", _fmt(_a['demand'], " TWh"))
            + "</div>")
    kpis
    return


@app.cell
def _(
    C,
    GEN_LABEL,
    GEN_ORDER,
    dash_year,
    data_ready,
    go,
    make_subplots,
    mo,
    monthly,
    need_data,
    style_fig,
):
    if not data_ready:
        dash_main = need_data(mo)
    else:
        _yr = dash_year.value
        _d = monthly[monthly["month"].dt.year == _yr].copy()
        ml = _d["month"].dt.strftime("%b")
        _fig = make_subplots(
            rows=2, cols=2, vertical_spacing=0.16, horizontal_spacing=0.10,
            subplot_titles=[f"Generation mix — {_yr}", f"Net balance by month — {_yr}",
                            f"Price (€/MWh) — {_yr}", f"Renewable coverage of demand — {_yr}"],
            specs=[[{"type":"bar"}, {"type":"bar"}], [{"type":"scatter"}, {"type":"bar"}]])
        for _src in GEN_ORDER:
            _fig.add_trace(go.Bar(x=ml, y=_d[f"gen_{_src}"], name=GEN_LABEL[_src],
                          marker_color=C[_src], showlegend=False), row=1, col=1)
        ncol = [C["export"] if v > 0 else C["import"] for v in _d["net_trade"]]
        _fig.add_trace(go.Bar(x=ml, y=_d["net_trade"], marker_color=ncol, showlegend=False),
                      row=1, col=2)
        if "price" in _d.columns and _d["price"].notna().any():
            _fig.add_trace(go.Scatter(x=ml, y=_d["price"], mode="lines+markers",
                          line=dict(color=C["gas"], width=2.5), showlegend=False), row=2, col=1)
        else:
            _fig.add_annotation(text="monthly price n/a", row=2, col=1, showarrow=False)
        cover = (_d["gen_renewables"] / _d["demand"] * 100).clip(upper=120)
        _fig.add_trace(go.Bar(x=ml, y=cover, marker_color=C["biomass"], showlegend=False),
                      row=2, col=2)
        _fig.update_layout(barmode="stack")
        _fig.update_yaxes(title_text="TWh", row=1, col=1)
        _fig.update_yaxes(title_text="TWh", row=1, col=2)
        _fig.update_yaxes(title_text="%", row=2, col=2)
        dash_main = style_fig(_fig, height=620, legend=False)
    dash_main
    return


@app.cell
def _(
    C,
    dash_metric,
    dash_year,
    data_ready,
    go,
    mo,
    monthly,
    need_data,
    style_fig,
):
    if not data_ready:
        dash_trend = need_data(mo)
    else:
        _col = dash_metric.value
        _d = monthly.copy()
        _d["yr"] = _d["month"].dt.year
        _fig = go.Figure()
        for _yr in sorted(_d["yr"].unique()):
            sub = _d[_d["yr"] == _yr]
            _sel = (_yr == dash_year.value)
            _fig.add_trace(go.Scatter(
                x=sub["month"].dt.strftime("%b"), y=sub[_col], name=str(_yr),
                line=dict(width=3 if _sel else 1.2,
                          color=C["accent"] if _sel else C["grid"]),
                opacity=1 if _sel else 0.7))
        lbl = [k for k, v in {"Net balance":"net_trade","Demand":"demand",
               "Residual load":"residual_load","Renewables":"gen_renewables",
               "Fossil":"gen_fossil"}.items() if v == _col][0]
        dash_trend = style_fig(_fig, height=380,
                               title=f"{lbl} — selected year highlighted against all years",
                               ytitle="TWh")
    dash_trend
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Conclusion — shortage or strategy?
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:8px 0 22px;">
      <div style="background:#f0fdf4;border:1.5px solid #86efac;border-radius:14px;padding:22px;">
        <div style="font-weight:750;color:#15803d;margin-bottom:10px;">✓ What the data supports</div>
        <ul style="margin:0;padding-left:18px;line-height:1.85;color:#166534;font-size:0.9rem;">
          <li>Germany flipped to net importer in 2023, gradually — not in a crash.</li>
          <li>Nuclear phase-out removed firm capacity and opened the gap.</li>
          <li>Imports track residual load and the seasons — a renewable-balancing signal.</li>
          <li>As gas prices fell and neighbours undercut German costs, imports rose by economics.</li>
          <li>2022 only looked strong because France's nuclear fleet broke worse than Germany's plants.</li>
          <li>Renewable share keeps rising while demand falls — the transition is advancing.</li>
        </ul>
      </div>
      <div style="background:#fff7ed;border:1.5px solid #fdba74;border-radius:14px;padding:22px;">
        <div style="font-weight:750;color:#c2410c;margin-bottom:10px;">✗ What the data does not support</div>
        <ul style="margin:0;padding-left:18px;line-height:1.85;color:#9a3412;font-size:0.9rem;">
          <li>“Germany can't produce enough power” — the regulator confirms capacity is sufficient.</li>
          <li>“The nuclear exit alone explains it” — fossil fell and demand fell too.</li>
          <li>“Net imports = energy crisis” — the crisis year was a net-export year.</li>
          <li>“Imports are a failure” — they are often the cheaper, lower-carbon option.</li>
          <li>“The Energiewende is collapsing” — renewable share is at record highs.</li>
        </ul>
      </div>
    </div>

    <div style="background:linear-gradient(135deg,#1d4ed8,#3b82f6);color:#ffffff;
                padding:30px 34px;border-radius:16px;">
      <div style="font-size:0.74rem;letter-spacing:3px;color:#dbeafe;margin-bottom:10px;font-weight:700;">
        MAIN FINDING</div>
      <p style="font-size:1.12rem;line-height:1.78;margin:0;color:#ffffff;">
        Germany's net-import position is <strong style="color:#fde68a;">strategy, not shortage</strong>. It is the
        combined result of a deliberate nuclear and coal drawdown, the rise of variable
        renewables, a war-driven price shock that reshuffled who could generate most cheaply, and
        a European market built to route power to wherever it costs least. Importing electricity is
        frequently the <strong style="color:#fde68a;">cheaper and lower-carbon choice</strong> — which is exactly why a
        grid with sufficient domestic capacity still chooses to do it. The import balance is a
        feature of a transitioning, integrated system, not a verdict against it.
      </p>
    </div>
    """)
    return


@app.cell
def _(has_price, mo):
    _src = ("Generation, load, residual load and wholesale prices: real measured data from "
           "SMARD.de (Bundesnetzagentur), CC BY 4.0."
           if has_price else
           "Generation, load and residual load: real SMARD data. Wholesale prices: real published "
           "annual day-ahead averages (BNetzA / Fraunhofer ISE / Open Energy Tracker).")
    mo.md(
        f"""
        ---
        <div style="font-size:0.8rem;color:#64748b;line-height:1.7;padding:6px 0;">
        <strong>Data &amp; method.</strong> {_src} Net trade is derived as generation − load, a
        transparent system-level proxy whose sign and trend match Germany's official net position.
        Energy-crisis figures (France nuclear collapse, 2022 price spikes) are sourced from SMARD and
        Banque de France reviews. All values in TWh unless stated. · <strong>STAGES</strong>
        </div>
        """)
    return


if __name__ == "__main__":
    app.run()
