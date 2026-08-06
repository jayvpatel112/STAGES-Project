import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import altair as alt
    import requests
    from pathlib import Path

    # Some new charts plot the full 8760 hours of the year, which is more than
    # Altair's default 5000-row safety limit. Turn that limit off.
    alt.data_transformers.disable_max_rows()
    return Path, alt, mo, np, pd, requests


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the setup cell.**
    This just loads the tools: `pandas` (spreadsheets in code), `numpy` (maths),
    `altair` (charts), and `requests` (to download data). Nothing is calculated yet —
    think of it as laying out the utensils before cooking.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    # How Much Storage Does Germany Need? Evidence from 2025 SMARD Grid Data

    **Main question:** *How much electricity storage does Germany need, what type
    of storage is useful at each duration, and where do batteries stop being enough?*

    The honest answer is not a single number. Germany's storage need is a **layered
    duration problem**:

    1. **Intraday (2–6 h)** — evening ramp; lithium-ion territory.
    2. **Multi-day (12–100 h)** — wind lulls; pumped hydro and flow batteries.
    3. **Seasonal / Dunkelflaute (100–1000+ h)** — hydrogen and hydrogen-ready
       dispatchable backup are among the most plausible options; lithium-ion becomes
       economically unsuitable at this duration.

    The notebook builds the argument step by step: measure the import/export gap →
    check whether shortages are short or long → check whether there is surplus to
    charge from → simulate how much import batteries can displace → find where extra
    battery capacity stops paying off → stress-test the worst week of the year →
    finally match each technology to the duration it solves best.
    """)
    return


@app.cell
def _(Path, pd, requests):
    # === Built-in SMARD fetcher (no utils.py dependency) ===
    SMARD_BASE = "https://www.smard.de/app/chart_data"
    DEFAULT_REGION = "DE"
    PRICE_REGION = "DE-LU"
    RESOLUTION = "hour"

    # Correct SMARD filter ids.  The value is (output column, SMARD region).
    SERIES = {
        410:  ("load_mw", DEFAULT_REGION),
        4066: ("biomass_mw", DEFAULT_REGION),
        1226: ("hydro_mw", DEFAULT_REGION),
        1225: ("wind_offshore_mw", DEFAULT_REGION),
        4067: ("wind_onshore_mw", DEFAULT_REGION),
        4068: ("solar_mw", DEFAULT_REGION),
        1228: ("other_renewable_mw", DEFAULT_REGION),
        1224: ("nuclear_mw", DEFAULT_REGION),
        1223: ("lignite_mw", DEFAULT_REGION),
        4069: ("hard_coal_mw", DEFAULT_REGION),
        4071: ("gas_mw", DEFAULT_REGION),
        4070: ("pumped_storage_mw", DEFAULT_REGION),
        1227: ("other_conventional_mw", DEFAULT_REGION),
        4169: ("price_eur_mwh", PRICE_REGION),
        4629: ("net_export_mw", DEFAULT_REGION),
    }

    def _raise_for_smard_error(response, url):
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(f"SMARD request failed for {url}") from exc

    def _fetch_index(series_id, region):
        url = f"{SMARD_BASE}/{series_id}/{region}/index_{RESOLUTION}.json"
        r = requests.get(url, timeout=30)
        _raise_for_smard_error(r, url)
        return r.json()["timestamps"]

    def _fetch_chunk(series_id, region, ts_ms):
        url = (f"{SMARD_BASE}/{series_id}/{region}/"
               f"{series_id}_{region}_{RESOLUTION}_{ts_ms}.json")
        r = requests.get(url, timeout=30)
        _raise_for_smard_error(r, url)
        rows = r.json()["series"]
        d = pd.DataFrame(rows, columns=["ts_ms", "value"])
        d["ts"] = pd.to_datetime(d["ts_ms"], unit="ms", utc=True)
        return d[["ts", "value"]]

    def fetch_smard_series(series_id, start, end, region=DEFAULT_REGION):
        idx = _fetch_index(series_id, region)
        start_ms = int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)
        end_ms = int(pd.Timestamp(end, tz="UTC").timestamp() * 1000)
        week_ms = 7 * 24 * 3600 * 1000
        relevant = [t for t in idx if (t + week_ms) >= start_ms and t <= end_ms]
        if not relevant:
            return pd.Series(dtype=float)
        parts = [_fetch_chunk(series_id, region, t) for t in relevant]
        full = pd.concat(parts, ignore_index=True)
        mask = ((full["ts"] >= pd.Timestamp(start, tz="UTC")) &
                (full["ts"] <  pd.Timestamp(end, tz="UTC")))
        return full[mask].set_index("ts")["value"]

    def load_smard_hourly(start, end, cache_path="smard_cache.pkl"):
        cache = Path(cache_path) if cache_path else None
        if cache and cache.exists():
            print(f"Loading from cache: {cache}")
            return pd.read_pickle(cache)

        print("Fetching from SMARD (takes ~1–2 min the first time)…")
        out = {}
        for sid, (name, region) in SERIES.items():
            print(f"  {name} ({sid}/{region})…")
            out[name] = fetch_smard_series(sid, start, end, region)

        result = pd.DataFrame(out)
        # Force index back to tz-aware DatetimeIndex, then convert to Berlin time
        result.index = pd.to_datetime(result.index, utc=True).tz_convert("Europe/Berlin")
        result = result.sort_index()

        if cache:
            result.to_pickle(cache)
            print(f"Cached to {cache}")
        return result

    # Fetch a slightly wider UTC range, then filter to the exact Berlin local year.
    # This avoids losing/adding one hour around the year boundary after timezone conversion.
    # Delete smard_cache_2025_wide.pkl to force a refresh.
    _raw_df = load_smard_hourly(start="2024-12-31", end="2026-01-02",
                                cache_path="smard_cache_2025_wide.pkl")

    _start_berlin = pd.Timestamp("2025-01-01", tz="Europe/Berlin")
    _end_berlin = pd.Timestamp("2026-01-01", tz="Europe/Berlin")
    df = _raw_df.loc[(_raw_df.index >= _start_berlin) & (_raw_df.index < _end_berlin)].copy()

    print(f"\nRows after Berlin-year filter: {len(df):,}")
    print("Expected rows for 2025: 8,760")
    print(f"Date range: {df.index.min()} → {df.index.max()}")
    print(f"Columns: {list(df.columns)}")
    return (df,)


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the data cell.**
    This downloads one full year (2025) of German grid data from SMARD, the official
    Federal Network Agency portal, at **hourly** resolution — 8,760 rows, one per hour.
    For each hour we get how much electricity each source produced, total demand,
    the market price, and the **net export** (whether Germany sold power abroad or
    bought it). The first run takes a minute or two; after that it reads from a local
    cache file so it's instant.

    *Key variable to remember:* **net export** is positive when Germany exports
    (surplus) and negative when it imports (deficit).
    """)
    return


@app.cell
def _(df):
    storage_df = df.copy()
    storage_df["renewables_mw"] = (
        storage_df["wind_onshore_mw"].fillna(0)
        + storage_df["wind_offshore_mw"].fillna(0)
        + storage_df["solar_mw"].fillna(0)
        + storage_df["hydro_mw"].fillna(0)
        + storage_df["biomass_mw"].fillna(0)
        + storage_df["other_renewable_mw"].fillna(0)
    )
    storage_df["imports_mw"] = (-storage_df["net_export_mw"]).clip(lower=0)
    storage_df["exports_mw"] = storage_df["net_export_mw"].clip(lower=0)

    # --- added: GW versions (easier to read) and time helpers ---
    storage_df["net_export_gw"] = storage_df["net_export_mw"] / 1000
    storage_df["imports_gw"] = storage_df["imports_mw"] / 1000
    storage_df["exports_gw"] = storage_df["exports_mw"] / 1000
    storage_df["renewables_gw"] = storage_df["renewables_mw"] / 1000
    storage_df["hour"] = storage_df.index.hour
    storage_df["month"] = storage_df.index.month
    storage_df["date"] = storage_df.index.date

    _imp = storage_df["imports_mw"].sum() / 1e6
    _exp = storage_df["exports_mw"].sum() / 1e6
    print(f"Net-import deficit energy: {_imp:.1f} TWh")
    print(f"Net-export surplus energy: {_exp:.1f} TWh")
    print(f"Net-import balance:        {_imp - _exp:.1f} TWh")
    return (storage_df,)


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — building the working table.**
    We take the raw data and add a few convenience columns:

    - `renewables_mw` = wind + solar + hydro + biomass + other renewables (clean generation added up).
    - `imports_mw` = net-import deficit hours after Germany's cross-border position is netted.
    - `exports_mw` = net-export surplus hours after Germany's cross-border position is netted.
    - GW versions of each (just ÷1000 so the numbers are smaller and readable).

    *Quick unit reminder:* **MW/GW is a speed** (how fast power flows right now, like
    km/h on a car). **MWh/GWh is a distance** (how much energy piled up over time, like
    the odometer). Later, storage **size** is in GWh (a distance / a bucket size), and
    storage **power** is in GW (how fast the bucket fills or empties).

    *Caveat — net trade as a proxy for storage surplus/deficit.* This notebook uses
    Germany's **hourly net export position**. That means `imports_mw` and `exports_mw`
    are not official gross cross-border imports and exports. They are **net-import
    deficit energy** and **net-export surplus energy** after all simultaneous flows are
    netted into one hourly position. This is appropriate for storage balancing because
    a battery responds to the net system position, but these values should not be
    compared directly with official gross trade totals.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Data validation checks

    Before interpreting the charts, we run a few simple checks to make sure the dataset
    really represents the exact 2025 Berlin local year and that the core import/export
    variables behave correctly.
    """)
    return


@app.cell
def _(mo, pd, storage_df):
    _start_expected = pd.Timestamp("2025-01-01", tz="Europe/Berlin")
    _end_expected_exclusive = pd.Timestamp("2026-01-01", tz="Europe/Berlin")
    _last_expected = _end_expected_exclusive - pd.Timedelta(hours=1)

    _overlap_hours = int(((storage_df["imports_mw"] > 0) &
                          (storage_df["exports_mw"] > 0)).sum())

    _checks = [
        {
            "Check": "Rows in dataset",
            "Value": f"{len(storage_df):,}",
            "Expected": "8,760 for full non-leap year",
            "Status": "OK" if len(storage_df) == 8760 else "Check",
        },
        {
            "Check": "First timestamp",
            "Value": str(storage_df.index.min()),
            "Expected": str(_start_expected),
            "Status": "OK" if storage_df.index.min() == _start_expected else "Check",
        },
        {
            "Check": "Last timestamp",
            "Value": str(storage_df.index.max()),
            "Expected": str(_last_expected),
            "Status": "OK" if storage_df.index.max() == _last_expected else "Check",
        },
        {
            "Check": "Index is sorted",
            "Value": str(storage_df.index.is_monotonic_increasing),
            "Expected": "True",
            "Status": "OK" if storage_df.index.is_monotonic_increasing else "Check",
        },
        {
            "Check": "Duplicate timestamps",
            "Value": str(int(storage_df.index.duplicated().sum())),
            "Expected": "0",
            "Status": "OK" if storage_df.index.duplicated().sum() == 0 else "Check",
        },
        {
            "Check": "Months represented",
            "Value": str(storage_df.index.month.nunique()),
            "Expected": "12",
            "Status": "OK" if storage_df.index.month.nunique() == 12 else "Check",
        },
        {
            "Check": "Imports and exports overlap",
            "Value": str(_overlap_hours),
            "Expected": "0",
            "Status": "OK" if _overlap_hours == 0 else "Check",
        },
        {
            "Check": "Missing net-export values",
            "Value": str(int(storage_df["net_export_mw"].isna().sum())),
            "Expected": "0 or very low",
            "Status": "OK" if storage_df["net_export_mw"].isna().sum() == 0 else "Check",
        },
        {
            "Check": "Missing price values",
            "Value": str(int(storage_df["price_eur_mwh"].isna().sum())),
            "Expected": "0 or very low",
            "Status": "OK" if storage_df["price_eur_mwh"].isna().sum() == 0 else "Check",
        },
    ]

    validation_df = pd.DataFrame(_checks)
    mo.ui.table(validation_df, page_size=10)
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — validation.**
    These checks protect the analysis from hidden data problems. The most important
    checks are the row count and the first/last timestamp: they confirm that the data
    covers exactly the 2025 calendar year in **Europe/Berlin** time, not a UTC-shifted
    year. The overlap check confirms that an hour is never counted as both import and
    export after the split.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## The size of the net imbalance

    Before sizing storage, here is the annual **net trade-balance** picture: how much
    energy appeared as net-import deficit, how much appeared as net-export surplus, how
    many hours Germany spent in each state, and the largest single net-import and
    net-export hours.
    """)
    return


@app.cell
def _(mo, pd, storage_df):
    total_imports_twh = storage_df["imports_mw"].sum() / 1e6
    _total_exports_twh = storage_df["exports_mw"].sum() / 1e6
    _net_imports_twh = total_imports_twh - _total_exports_twh
    _import_hours = int((storage_df["imports_mw"] > 0).sum())
    _export_hours = int((storage_df["exports_mw"] > 0).sum())
    _peak_import_gw = storage_df["imports_gw"].max()
    _peak_export_gw = storage_df["exports_gw"].max()

    baseline_summary_df = pd.DataFrame([
        {"Metric": "Net-import deficit energy", "Value": f"{total_imports_twh:.1f} TWh"},
        {"Metric": "Net-export surplus energy", "Value": f"{_total_exports_twh:.1f} TWh"},
        {"Metric": "Net-import balance", "Value": f"{_net_imports_twh:.1f} TWh"},
        {"Metric": "Net-import hours", "Value": f"{_import_hours:,} h"},
        {"Metric": "Net-export hours", "Value": f"{_export_hours:,} h"},
        {"Metric": "Peak net import", "Value": f"{_peak_import_gw:.1f} GW"},
        {"Metric": "Peak net export", "Value": f"{_peak_export_gw:.1f} GW"},
    ])
    mo.ui.table(baseline_summary_df, page_size=7)
    return (total_imports_twh,)


@app.cell
def _(mo):
    mo.md(r"""
    ## External net-balance sanity check

    Official annual trade reports publish **gross** imports and exports. Because this
    notebook works from an hourly **net export** series, the directly comparable number
    is the annual **net-import balance**, not gross import and gross export separately.
    """)
    return


@app.cell
def _(mo, pd, storage_df):
    _official_net_imports_twh = 21.9
    _notebook_net_imports_twh = (
        storage_df["imports_mw"].sum() - storage_df["exports_mw"].sum()
    ) / 1e6
    _diff_twh = _notebook_net_imports_twh - _official_net_imports_twh

    external_net_validation_df = pd.DataFrame([
        {
            "Metric": "Net imports",
            "Notebook value": f"{_notebook_net_imports_twh:.1f} TWh",
            "Official 2025 reference": f"{_official_net_imports_twh:.1f} TWh",
            "Difference": f"{_diff_twh:+.1f} TWh",
            "Comment": "Compare net balance only; gross trade is not directly comparable",
        }
    ])
    mo.ui.table(external_net_validation_df, page_size=3)
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — external validation.**
    This table checks the notebook's net-import balance against the published 2025
    annual net-import reference. The official gross import/export totals are larger
    because they count simultaneous cross-border flows in both directions. This notebook
    nets those flows into one hourly balance, which is the correct object for the
    storage-dispatch analysis.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the baseline table.**
    Each row is one headline number for the year after cross-border flows are reduced
    to a single hourly net position. "Net-import deficit energy" means the hours where
    Germany was net importing; "net-export surplus energy" means the hours where it was
    net exporting. These are **not gross trade totals** because Germany can import from
    one country and export to another in the same hour.

    The important takeaway: annual totals alone **don't** tell you the storage need.
    A battery cares about *timing* — when net surplus shows up, how long each net
    deficit lasts, and whether it was charged **before** the deficit started. That's
    what the next sections dig into.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Is Germany short or surplus, and how often?

    A **duration curve** ranks all 8,760 hours from the biggest export hour on the
    left to the biggest import hour on the right. Positive = surplus, negative = deficit.
    It answers one question: is the storage problem a *total energy shortage*, or just
    a *timing mismatch* between surplus hours and deficit hours?
    """)
    return


@app.cell
def _(alt, np, storage_df):
    _ned = (storage_df[["net_export_gw"]]
            .dropna()
            .sort_values("net_export_gw", ascending=False)
            .reset_index(drop=True))
    _ned["ranked_hour"] = np.arange(1, len(_ned) + 1)

    _chart = alt.Chart(_ned).mark_area(color="#4C78A8", opacity=0.7).encode(
        x=alt.X("ranked_hour:Q",
                title="Ranked hour of the year (highest export → highest import)"),
        y=alt.Y("net_export_gw:Q", title="Net export position (GW)"),
        tooltip=["ranked_hour:Q", "net_export_gw:Q"],
    ).properties(width=680, height=380, title="Hourly net-export duration curve")
    _chart
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — reading this curve.**
    Walk left to right through the year, sorted best-to-worst. The **x-axis is a count
    of hours**, not calendar dates. Where the blue area is *above zero*, Germany had
    spare power (good for charging a battery). Where it dips *below zero*, Germany was
    importing (a chance to discharge).

    One glance tells the story: Germany spends time in **both** states. That's exactly
    the condition storage needs — it can only move energy through time, filling up
    during the left (surplus) part and emptying during the right (deficit) part. It
    cannot invent energy during a long deficit if nothing was stored first.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Are the net-deficit periods short or long?

    A 2-hour evening net-deficit and a 5-day winter lull need completely different
    storage. Here we glue consecutive net-import hours together into distinct
    **net-deficit events** and measure how long each one lasts and how much energy it
    involves.
    """)
    return


@app.cell
def _(np, pd, storage_df):
    def _build_deficit_events(data):
        _d = data.copy()
        _d["is_deficit"] = _d["imports_mw"] > 0
        # a new "group" starts every time the deficit on/off state flips
        _d["event_group"] = (_d["is_deficit"] != _d["is_deficit"].shift()).cumsum()

        _events = []
        for _gid, _g in _d[_d["is_deficit"]].groupby("event_group"):
            _events.append({
                "start": _g.index.min(),
                "end": _g.index.max(),
                "duration_h": len(_g),
                "total_deficit_gwh": _g["imports_mw"].sum() / 1000,
                "peak_deficit_gw": _g["imports_mw"].max() / 1000,
                "avg_deficit_gw": _g["imports_mw"].mean() / 1000,
            })
        return pd.DataFrame(_events)

    deficit_events_df = _build_deficit_events(storage_df)
    deficit_events_df["duration_bucket"] = pd.cut(
        deficit_events_df["duration_h"],
        bins=[0, 3, 6, 12, 24, 72, 168, np.inf],
        labels=["1–3 h", "4–6 h", "7–12 h", "13–24 h",
                "1–3 days", "3–7 days", "7+ days"],
        right=True,
    )

    print(f"Number of separate net-deficit events: {len(deficit_events_df)}")
    print(f"Longest single net-deficit: {deficit_events_df['duration_h'].max()} h")
    print(f"Biggest single net-deficit: {deficit_events_df['total_deficit_gwh'].max():.0f} GWh")
    deficit_events_df.head()
    return (deficit_events_df,)


@app.cell
def _(alt, deficit_events_df):
    _bucket_order = ["1–3 h", "4–6 h", "7–12 h", "13–24 h",
                     "1–3 days", "3–7 days", "7+ days"]
    _cnt = (deficit_events_df
            .groupby("duration_bucket", observed=True)
            .size().reset_index(name="event_count"))

    _chart = alt.Chart(_cnt).mark_bar(color="#E45756").encode(
        x=alt.X("duration_bucket:N", sort=_bucket_order, title="Net-deficit event length"),
        y=alt.Y("event_count:Q", title="Number of events"),
        tooltip=["duration_bucket:N", "event_count:Q"],
    ).properties(width=650, height=350, title="How many net-deficit events of each length?")
    _chart
    return


@app.cell
def _(alt, deficit_events_df):
    _bucket_order = ["1–3 h", "4–6 h", "7–12 h", "13–24 h",
                     "1–3 days", "3–7 days", "7+ days"]
    _en = (deficit_events_df
           .groupby("duration_bucket", observed=True)["total_deficit_gwh"]
           .sum().reset_index())

    _chart = alt.Chart(_en).mark_bar(color="#F58518").encode(
        x=alt.X("duration_bucket:N", sort=_bucket_order, title="Net-deficit event length"),
        y=alt.Y("total_deficit_gwh:Q", title="Total net-deficit energy (GWh)"),
        tooltip=["duration_bucket:N", "total_deficit_gwh:Q"],
    ).properties(width=650, height=350,
                 title="Where the net-deficit *energy* actually piles up")
    _chart
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the two deficit charts.**
    The **first chart (count)** asks *how often* each kind of shortage happens — most
    events are short, so batteries get frequent work. The **second chart (energy)**
    asks *where the real burden is* — even if long events are rare, they can hold a
    big chunk of the total energy that has to be covered.

    Reading them together is the point: if lots of the energy sits in the long buckets
    ("1–3 days", "7+ days"), then no amount of short-duration battery fully solves the
    problem — you also need long-duration flexibility. It's the difference between a
    water bottle (handles a quick thirst many times a day) and a reservoir (handles a
    drought).
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Is the problem seasonal?

    Storage gets much harder when surplus and deficit are separated by *months*
    instead of *hours*. A lithium-ion battery can shift energy across a day or a few
    days — it cannot economically move a summer surplus into a winter deficit. This
    chart puts each month's export energy (up) against its import energy (down).
    """)
    return


@app.cell
def _(alt, pd, storage_df):
    _imp_m = storage_df["imports_mw"].resample("ME").sum() / 1000   # GWh
    _exp_m = storage_df["exports_mw"].resample("ME").sum() / 1000   # GWh
    _mb = pd.DataFrame({
        "month_label": _imp_m.index.strftime("%b"),
        "exports_gwh": _exp_m.values,
        "imports_gwh": _imp_m.values,
    })

    _long = pd.concat([
        _mb[["month_label", "exports_gwh"]]
            .rename(columns={"exports_gwh": "gwh"}).assign(kind="Net surplus / export"),
        _mb[["month_label", "imports_gwh"]]
            .rename(columns={"imports_gwh": "gwh"}).assign(kind="Net deficit / import"),
    ])
    # draw imports downward so surplus and deficit face opposite directions
    _long.loc[_long["kind"] == "Net deficit / import", "gwh"] *= -1

    _chart = alt.Chart(_long).mark_bar().encode(
        x=alt.X("month_label:N", sort=list(_mb["month_label"]), title="Month"),
        y=alt.Y("gwh:Q", title="Monthly net balance (GWh)  —  up = net surplus, down = net deficit"),
        color=alt.Color("kind:N", title=""),
        tooltip=["month_label:N", "kind:N", "gwh:Q"],
    ).properties(width=680, height=380, title="Monthly net surplus vs net deficit")
    _chart
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the monthly bars.**
    Each month has two bars: a **surplus bar pointing up** (energy Germany could have
    stored) and a **deficit bar pointing down** (energy it was short). If the up-bars
    cluster in the sunny/windy months and the down-bars cluster in the dark months,
    the mismatch is *seasonal* — and a daily-cycling battery can't bridge that gap.

    This is the visual reason the conclusion ends up recommending a **portfolio**
    (batteries + long-duration storage + hydrogen + interconnection) rather than "just
    build more batteries."
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Daily surplus duration curve — how often can a battery fill up?

    The monthly view shows the seasonal shape; batteries also depend on **daily**
    surplus. This ranks every full day from the highest surplus to the lowest, with
    reference lines for 100, 200 and 500 GWh battery sizes.
    """)
    return


@app.cell
def _(alt, pd, storage_df):
    # Daily surplus = sum of hourly exports per local Berlin calendar day, in GWh.
    # Use resample("D") instead of dropping non-24-hour days so valid DST days
    # with 23 or 25 hours are kept.
    _hourly_surplus_gwh = storage_df["exports_mw"].fillna(0) / 1000

    _daily_stats = _hourly_surplus_gwh.resample("D").agg(["sum", "count"]).reset_index()
    _daily_stats.columns = ["date", "surplus_gwh", "hours_in_day"]

    daily_surplus_df = _daily_stats[
        (_daily_stats["date"] >= pd.Timestamp("2025-01-01", tz="Europe/Berlin"))
        & (_daily_stats["date"] < pd.Timestamp("2026-01-01", tz="Europe/Berlin"))
    ].copy()

    # Sort highest-to-lowest for the duration curve
    daily_surplus_sorted = (daily_surplus_df
                            .sort_values("surplus_gwh", ascending=False)
                            .reset_index(drop=True))
    daily_surplus_sorted["day_rank"] = range(1, len(daily_surplus_sorted) + 1)

    # Print the key stats
    print(f"Total local days kept: {len(daily_surplus_df)}")
    print("DST-aware daily hour counts:")
    print(daily_surplus_df["hours_in_day"].value_counts().sort_index().to_string())
    print(f"Max daily surplus:    {daily_surplus_df['surplus_gwh'].max():.0f} GWh")
    print(f"Mean daily surplus:   {daily_surplus_df['surplus_gwh'].mean():.0f} GWh")
    print(f"Median daily surplus: {daily_surplus_df['surplus_gwh'].median():.0f} GWh")
    _total_gwh = daily_surplus_df['surplus_gwh'].sum()
    print(f"TOTAL annual surplus: {_total_gwh:,.0f} GWh  ({_total_gwh/1000:.2f} TWh)")
    print()
    for _threshold in [50, 100, 200, 400, 800]:
        _n = (daily_surplus_df['surplus_gwh'] > _threshold).sum()
        print(f"Days with surplus > {_threshold:>4} GWh: {_n:>3} "
              f"({100 * _n / len(daily_surplus_df):.0f}% of the year)")

    # Main duration curve
    _area = alt.Chart(daily_surplus_sorted).mark_area(opacity=0.6, color="#4C78A8").encode(
        x=alt.X("day_rank:Q",
                scale=alt.Scale(domain=[0, len(daily_surplus_sorted)]),
                title="Day of year (ranked from highest surplus to lowest)"),
        y=alt.Y("surplus_gwh:Q", title="Daily surplus (GWh)"),
        tooltip=["day_rank", "surplus_gwh:Q", "date:T", "hours_in_day:Q"],
    )

    # Reference lines for different battery sizes
    _refs = pd.DataFrame({
        "battery_size_gwh": [100, 200, 500],
        "label": ["100 GWh battery capacity",
                  "200 GWh battery capacity",
                  "500 GWh battery capacity"],
    })
    _ref_lines = alt.Chart(_refs).mark_rule(strokeDash=[6, 4]).encode(
        y="battery_size_gwh:Q",
        color=alt.Color("label:N", title="Reference"),
    )

    chart_daily_surplus = (_area + _ref_lines).properties(
        width=680, height=400,
        title="Daily surplus duration curve — how many days produce enough to fill a battery",
    )
    chart_daily_surplus
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the daily surplus curve.**
    The **y-axis is how much spare energy a local Berlin day produced (GWh)**; the
    **x-axis is days, ranked best to worst**. The daily aggregation is DST-aware, so
    Germany's valid 23-hour and 25-hour clock-change days are kept instead of being
    dropped. The dashed lines are battery sizes. Wherever the blue area sits *above* a
    dashed line, that day made enough surplus to completely fill that battery.

    Read one line: the **500 GWh** line is only crossed on a handful of extreme
    summer days, while the **100 GWh** line is crossed on far more days. That's the
    core reason big batteries underperform — a giant bucket only fills on rare days,
    so most of the year it sits half-empty.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Duration-cost curve

    For each duration, find the worst rolling net-deficit stretch and multiply by
    storage cost per kWh. Log-log scale shows the regime change clearly.

    CAPEX assumptions (2025 €/kWh of storage capacity):
    Li-ion 4 h battery €140 · Pumped hydro €70 · Hydrogen P2G2P €50.
    """)
    return


@app.cell
def _(alt, np, pd, storage_df):
    _COST_BATTERY = 140
    _COST_PHS = 70
    _COST_H2 = 50

    _durations_h = np.array([1, 2, 4, 6, 8, 12, 24, 48, 72, 120, 168, 336, 720])
    _imports_gw = storage_df["imports_mw"].fillna(0) / 1000
    _shortfall_gwh = [
        _imports_gw.rolling(window=int(_d), min_periods=int(_d)).sum().max()
        for _d in _durations_h
    ]

    _rows = []
    for _d, _gwh in zip(_durations_h, _shortfall_gwh):
        _rows.append({"duration_h": _d, "energy_gwh": _gwh,
                      "technology": "Lithium-ion battery",
                      "cost_beur": _gwh * 1e6 * _COST_BATTERY / 1e9})
        _rows.append({"duration_h": _d, "energy_gwh": _gwh,
                      "technology": "Pumped hydro",
                      "cost_beur": _gwh * 1e6 * _COST_PHS / 1e9})
        _rows.append({"duration_h": _d, "energy_gwh": _gwh,
                      "technology": "Hydrogen (P2G2P)",
                      "cost_beur": _gwh * 1e6 * _COST_H2 / 1e9})
    duration_cost_df = pd.DataFrame(_rows)

    chart_duration_cost = alt.Chart(duration_cost_df).mark_line(point=True).encode(
        x=alt.X("duration_h:Q", scale=alt.Scale(type="log"),
                title="Storage duration (hours, log scale)"),
        y=alt.Y("cost_beur:Q", scale=alt.Scale(type="log"),
                title="Total investment required (€ billion, log scale)"),
        color=alt.Color("technology:N", title="Technology"),
        tooltip=["duration_h", "energy_gwh:Q", "technology", "cost_beur:Q"],
    ).properties(width=650, height=420,
                 title="Cost to bridge worst observed shortfall, by duration")
    chart_duration_cost
    return


@app.cell
def _(mo):
    mo.md(r"""
    Pick a duration (say 24 h); the y-value is the cost
    in each technology to bridge the worst 24-hour deficit observed. The lines
    diverge dramatically as duration grows — this is why batteries cannot solve
    the Dunkelflaute problem.

    For short storage, batteries win. For very long storage, hydrogen wins. There is no single "best" storage — it depends on how long you need to store.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the duration-cost curve.**
    Both axes are on a **log scale** (each gridline is ×10), so straight-ish lines
    that pull apart actually mean *huge* real-world gaps. The x-axis is how many hours
    of shortage you want to cover; the y-axis is the total bill for each technology.

    The message: for a short (say 4-hour) gap, lithium-ion is cheap and fine. As the
    required duration stretches into days, batteries shoot up in cost while hydrogen
    stays affordable per unit of energy. There is no single "best" storage — the winner
    changes with duration.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Net-import deficit displacement curve

    Greedy dispatch: charge on surplus, discharge on deficit, 85 % RTE.
    The curve bends flat where additional storage stops helping.
    """)
    return


@app.cell
def _(alt, np, pd, storage_df):
    def _simulate_battery(net_export_mw, capacity_gwh, power_gw, rte=0.85):
        _cap_mwh = capacity_gwh * 1000
        _pow_mw = power_gw * 1000
        _eta = np.sqrt(rte)
        _soc = 0.0
        _displaced_mwh = 0.0
        for _ne in net_export_mw.values:
            if _ne > 0:
                _charge_in = min(_ne, _pow_mw, (_cap_mwh - _soc) / _eta)
                _soc += _charge_in * _eta
            elif _ne < 0:
                _deficit = -_ne
                _discharge_out = min(_deficit, _pow_mw, _soc * _eta)
                _soc -= _discharge_out / _eta
                _displaced_mwh += _discharge_out
        return _displaced_mwh / 1e6

    _capacities_gwh = [0, 10, 25, 50, 100, 200, 400, 800, 1600, 3200]
    _net_export = storage_df["net_export_mw"].fillna(0)

    _results = []
    for _cap in _capacities_gwh:
        _power = _cap / 4 if _cap > 0 else 0
        _disp = _simulate_battery(_net_export, _cap, _power)
        _results.append({"capacity_gwh": _cap, "power_gw": _power,
                         "imports_displaced_twh": _disp})
    displacement_df = pd.DataFrame(_results)

    _total = storage_df["imports_mw"].sum() / 1e6
    print(f"Baseline imports: {_total:.1f} TWh")
    print(displacement_df)

    chart_displacement = alt.Chart(displacement_df).mark_line(point=True).encode(
        x=alt.X("capacity_gwh:Q", title="Battery storage capacity (GWh, 4 h system)"),
        y=alt.Y("imports_displaced_twh:Q", title="Net-import deficit displaced (TWh)"),
        tooltip=["capacity_gwh", "power_gw", "imports_displaced_twh"],
    ).properties(width=650, height=400,
                 title="Diminishing returns: net-import deficit displaced vs battery size")
    chart_displacement
    return (displacement_df,)


@app.cell
def _(mo):
    mo.md(r"""
    net-import deficit displaced = TWh of net-import deficit energy that the battery could cover because it had stored net-export surplus earlier.

    The first ~100 GWh of batteries does most of the
    work — roughly Fraunhofer ISE's 2030 estimate. After that, each additional
    GWh displaces less because storage can only help when there's surplus to
    charge from.

    Germany's biggest daily surplus is around 200–400 GWh on the very sunniest, windiest summer days.
    The typical daily surplus is much smaller — maybe 50–150 GWh.
    A 100 GWh battery captures the typical daily surplus well, and even most of the big ones.
    A 500 GWh battery would only fill up on the extreme days — maybe 20–30 times per year.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — how the simulation works.**
    We run a simple robot battery hour by hour through the whole year: **when there's
    a surplus it charges, when there's a deficit it discharges**, losing 15% to
    round-trip inefficiency (85% RTE). We repeat this for bigger and bigger batteries
    and record how much import each size avoided.

    The x-axis is battery size (GWh), the y-axis is imports avoided (TWh). The curve
    **rises steeply then flattens** — the first slice of storage is very valuable, and
    each extra slice does less. That bend is the whole economic argument in one line.

    *Two modelling caveats worth stating:*

    - **4-hour power assumption.** Power is set to `capacity / 4`, i.e. every battery is
      a 4-hour system. For the very large sizes this implies unrealistic power ratings
      (a 1600 GWh battery becomes a 400 GW system — far beyond any realistic German
      grid-scale need), so the large-capacity results should be read as an **optimistic
      upper bound**, not a literal deployment.
    - **Starts empty.** The battery begins the year at 0% charge. Annual results depend
      slightly on that starting point; starting half- or fully-charged would nudge the
      first weeks. A robustness check would be to run the year twice and keep only the
      second pass, or to test 0% / 50% / 100% starts — the shape of the curve is stable
      either way, but the exact TWh can shift a little.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Where do diminishing returns actually begin?

    The total curve shows bigger batteries help more. But investors care about the
    **marginal** value: how much *extra* import does each additional GWh remove? This
    computes the slope between consecutive battery sizes.
    """)
    return


@app.cell
def _(alt, displacement_df):
    _m = displacement_df.copy()
    _m["prev_cap"] = _m["capacity_gwh"].shift()
    _m["prev_disp"] = _m["imports_displaced_twh"].shift()
    _m["added_cap_gwh"] = _m["capacity_gwh"] - _m["prev_cap"]
    _m["extra_disp_twh"] = _m["imports_displaced_twh"] - _m["prev_disp"]
    _m["mwh_per_added_gwh"] = _m["extra_disp_twh"] * 1_000_000 / _m["added_cap_gwh"]
    _m = _m.dropna()

    _chart = alt.Chart(_m).mark_line(point=True, color="#54A24B").encode(
        x=alt.X("capacity_gwh:Q", title="Battery capacity (GWh)"),
        y=alt.Y("mwh_per_added_gwh:Q",
                title="MWh of net-import deficit displaced per extra GWh of battery"),
        tooltip=["capacity_gwh:Q", "added_cap_gwh:Q",
                 "extra_disp_twh:Q", "mwh_per_added_gwh:Q"],
    ).properties(width=650, height=380,
                 title="Marginal value of storage falls as you add more")
    _chart
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the marginal curve.**
    This is the "bang per buck" chart. The y-axis is *how much extra import each new
    GWh of battery removes*. It **slides downward** as you move right.

    Why: the first batteries catch the frequent, easy day-night cycles. Later batteries
    are left waiting for rarer big-surplus days and longer deficits, so every added GWh
    earns less. Somewhere on this curve the extra battery stops being worth its price —
    that's the practical "stop here" signal for lithium-ion.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## How much net-import deficit is left over?

    Displacement shows how much batteries *help*. The reliability question is the
    flip side: how much import need **remains** after each battery size is installed?
    """)
    return


@app.cell
def _(alt, displacement_df, total_imports_twh):
    _r = displacement_df.copy()
    _r["imports_remaining_twh"] = total_imports_twh - _r["imports_displaced_twh"]
    _r["import_reduction_pct"] = _r["imports_displaced_twh"] / total_imports_twh * 100

    _chart = alt.Chart(_r).mark_line(point=True, color="#B279A2").encode(
        x=alt.X("capacity_gwh:Q", title="Battery capacity (GWh)"),
        y=alt.Y("imports_remaining_twh:Q", title="Net-import deficit still needed (TWh)"),
        tooltip=["capacity_gwh:Q", "imports_displaced_twh:Q",
                 "imports_remaining_twh:Q", "import_reduction_pct:Q"],
    ).properties(width=650, height=380,
                 title="Batteries shrink net-import deficit but never reach zero")
    _chart
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — imports remaining.**
    Same battery sizes on the x-axis, but now the y-axis is the import that's **still
    left** after the battery has done its job. The line drops fast at first, then
    levels off well **above zero**.

    The reason it never hits zero: a battery can only give back energy it stored
    earlier. If a long deficit arrives with no fresh surplus beforehand, the battery is
    empty and imports are unavoidable. This is the honest limit of storage — it reduces
    dependence on imports and firm backup, but does not remove it.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Do bigger batteries actually get used?

    A battery's value depends not just on energy displaced but on **how often it
    cycles**. Here we track equivalent full cycles per year and average state of
    charge for a range of sizes. (We also keep the full hour-by-hour charge history
    for the timeline and stress-test that follow.)
    """)
    return


@app.cell
def _(np, pd, storage_df):
    def _simulate_battery_detailed(net_export_mw, capacity_gwh, power_gw, rte=0.85):
        _cap_mwh = capacity_gwh * 1000
        _pow_mw = power_gw * 1000
        _eta = np.sqrt(rte)
        _soc = 0.0
        _displaced = 0.0
        _discharged = 0.0
        _recs = []
        for _ts, _ne in net_export_mw.items():
            if _ne > 0:
                _cin = min(_ne, _pow_mw, (_cap_mwh - _soc) / _eta)
                _soc += _cin * _eta
            elif _ne < 0:
                _out = min(-_ne, _pow_mw, _soc * _eta)
                _soc -= _out / _eta
                _displaced += _out
                _discharged += _out
            _recs.append({
                "timestamp": _ts,
                "capacity_gwh": capacity_gwh,
                "soc_gwh": _soc / 1000,
                "soc_pct": (_soc / _cap_mwh * 100) if _cap_mwh > 0 else 0.0,
            })
        _sdf = pd.DataFrame(_recs)
        _metrics = {
            "capacity_gwh": capacity_gwh,
            "power_gw": power_gw,
            "imports_displaced_twh": _displaced / 1e6,
            "full_cycles_per_year": _discharged / _cap_mwh if _cap_mwh > 0 else 0.0,
            "avg_soc_pct": _sdf["soc_pct"].mean() if _cap_mwh > 0 else 0.0,
        }
        return _metrics, _sdf

    _caps = [10, 25, 50, 100, 200, 400, 500, 800, 1600]
    _ne_series = storage_df["net_export_mw"].fillna(0)

    _metrics_list = []
    _soc_parts = []
    for _cap in _caps:
        _mt, _sd = _simulate_battery_detailed(_ne_series, _cap, _cap / 4)
        _metrics_list.append(_mt)
        _soc_parts.append(_sd)

    battery_utilization_df = pd.DataFrame(_metrics_list)
    battery_soc_df = pd.concat(_soc_parts, ignore_index=True)

    print(battery_utilization_df[
        ["capacity_gwh", "full_cycles_per_year", "avg_soc_pct", "imports_displaced_twh"]
    ].round(2).to_string(index=False))
    return battery_soc_df, battery_utilization_df


@app.cell
def _(alt, battery_utilization_df):
    _chart = alt.Chart(battery_utilization_df).mark_line(point=True, color="#4C78A8").encode(
        x=alt.X("capacity_gwh:Q", title="Battery capacity (GWh)"),
        y=alt.Y("full_cycles_per_year:Q", title="Equivalent full cycles per year"),
        tooltip=["capacity_gwh:Q", "full_cycles_per_year:Q", "imports_displaced_twh:Q"],
    ).properties(width=650, height=380,
                 title="Big batteries sit idle: full cycles per year fall with size")
    _chart
    return


@app.cell
def _(alt, battery_utilization_df):
    _chart = alt.Chart(battery_utilization_df).mark_line(point=True, color="#72B7B2").encode(
        x=alt.X("capacity_gwh:Q", title="Battery capacity (GWh)"),
        y=alt.Y("avg_soc_pct:Q", title="Average state of charge (%)"),
        tooltip=["capacity_gwh:Q", "avg_soc_pct:Q"],
    ).properties(width=650, height=380,
                 title="Average fill level of the battery across the year")
    _chart
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — utilization.**
    "**Equivalent full cycles per year**" = how many complete empty→full→empty trips
    the battery effectively makes in a year. A small battery might cycle hundreds of
    times (great economics); a huge one cycles only a handful of times (poor economics).

    The **average state of charge** chart tells a similar story: small batteries live
    near a healthy working range, while very large ones spend most of the year barely
    filled. Same idea as before, from the utilization angle — a bucket you rarely fill
    or empty is a bucket you overpaid for.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## What does the battery actually do all year?

    The previous section summarised behaviour with numbers. This makes it visible:
    the 7-day-average state of charge across the whole year for three battery sizes.
    """)
    return


@app.cell
def _(alt, battery_soc_df):
    _sel = battery_soc_df[battery_soc_df["capacity_gwh"].isin([100, 200, 500])].copy()
    _sel = _sel.set_index("timestamp")
    _daily = (_sel.groupby("capacity_gwh")["soc_pct"]
              .resample("D").mean().reset_index())
    _daily["soc_pct_7d_avg"] = (
        _daily.groupby("capacity_gwh")["soc_pct"]
        .transform(lambda s: s.rolling(window=7, min_periods=1).mean())
    )

    _chart = alt.Chart(_daily).mark_line().encode(
        x=alt.X("timestamp:T", title="Date"),
        y=alt.Y("soc_pct_7d_avg:Q", title="State of charge (%), 7-day average"),
        color=alt.Color("capacity_gwh:N", title="Battery size (GWh)"),
        tooltip=["timestamp:T", "capacity_gwh:N", "soc_pct:Q", "soc_pct_7d_avg:Q"],
    ).properties(width=700, height=400,
                 title="How full each battery sits across the year (7-day average)")
    _chart
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the SOC timeline.**
    Each colored line is one battery size; the y-axis is how full it is (0–100%) after
    smoothing with a 7-day average. The smoothing removes some daily noise so the
    seasonal pattern is easier to read. A line that stays flat and low means that
    battery rarely fills — it's behaving like an oversized reserve, not a working
    storage unit.

    If the 500 GWh line spends the year mostly empty while the 100 GWh line swings
    healthily, that visually confirms lithium-ion is a *daily* tool, not a *seasonal*
    one.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## The worst net-deficit week — a Dunkelflaute stress test

    Averages hide the hard moments. Here we find the worst rolling **7-day** net-deficit
    stretch of 2025 and watch how batteries cope during it.
    """)
    return


@app.cell
def _(pd, storage_df):
    _imp_gwh = storage_df["imports_mw"].fillna(0) / 1000
    _roll = _imp_gwh.rolling(window=168, min_periods=168).sum()   # 168 h = 7 days
    worst_7d_end = _roll.idxmax()
    worst_7d_start = worst_7d_end - pd.Timedelta(hours=167)

    worst_event_df = storage_df.loc[worst_7d_start:worst_7d_end].copy()
    worst_event_df["timestamp"] = worst_event_df.index
    worst_event_df["imports_gw"] = worst_event_df["imports_mw"] / 1000
    worst_event_df["renewables_gw"] = worst_event_df["renewables_mw"] / 1000

    print(f"Worst 7-day net-deficit window: {worst_7d_start:%Y-%m-%d} → {worst_7d_end:%Y-%m-%d}")
    print(f"Total deficit in window: {worst_event_df['imports_mw'].sum()/1000:.0f} GWh")
    print(f"Peak import: {worst_event_df['imports_gw'].max():.1f} GW")
    print(f"Avg renewables in window: {worst_event_df['renewables_gw'].mean():.1f} GW")
    return worst_7d_end, worst_7d_start, worst_event_df


@app.cell
def _(alt, worst_event_df):
    _chart = alt.Chart(worst_event_df).mark_area(color="#E45756", opacity=0.7).encode(
        x=alt.X("timestamp:T", title="Hour"),
        y=alt.Y("imports_gw:Q", title="Net-import deficit (GW)"),
        tooltip=["timestamp:T", "imports_gw:Q", "renewables_gw:Q"],
    ).properties(width=700, height=350,
                 title="The worst 7-day net-deficit stretch of the year")
    _chart
    return


@app.cell
def _(alt, battery_soc_df, worst_7d_end, worst_7d_start):
    _w = battery_soc_df[
        (battery_soc_df["timestamp"] >= worst_7d_start)
        & (battery_soc_df["timestamp"] <= worst_7d_end)
        & (battery_soc_df["capacity_gwh"].isin([100, 200, 500]))
    ].copy()

    _chart = alt.Chart(_w).mark_line().encode(
        x=alt.X("timestamp:T", title="Hour"),
        y=alt.Y("soc_pct:Q", title="State of charge (%)"),
        color=alt.Color("capacity_gwh:N", title="Battery size (GWh)"),
        tooltip=["timestamp:T", "capacity_gwh:N", "soc_pct:Q"],
    ).properties(width=700, height=350,
                 title="Battery SOC remains near empty during the worst net-deficit week")
    _chart
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the stress test.**
    The **red chart** is the import deficit hour by hour during the single worst week —
    tall red means Germany was leaning hard on imports. The **SOC chart** shows the
    batteries during that same week: they help at the start, then **slide toward empty**
    and stay there because there's little surplus to recharge from mid-crisis.

    This is the clinching argument for the three-tier conclusion: batteries shave the
    first part of a long shortage, but they cannot carry the system through a multi-day
    Dunkelflaute. That job needs hydrogen, dispatchable backup, demand flexibility, and
    European interconnection.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Price arbitrage backtest

    Charge during 4 cheapest hours, discharge during 4 most expensive. Sum
    annual profit, compare to CAPEX (~€560 k per MW for a 4 h battery at
    €140/kWh).
    """)
    return


@app.cell
def _(alt, np, pd, storage_df):
    _RTE = 0.85
    _CAPEX_PER_MW = 4 * 1000 * 140

    _prices = storage_df["price_eur_mwh"].dropna()
    _daily_groups = _prices.groupby(_prices.index.date)

    _daily = []
    for _date, _day_prices in _daily_groups:
        if len(_day_prices) < 24:
            continue
        _sorted = _day_prices.sort_values()
        _cc = _sorted.iloc[:4].mean()
        _dr = _sorted.iloc[-4:].mean()
        # a rational operator only trades when the spread beats efficiency losses
        _profit = max(0.0, (_dr - _cc / _RTE) * 4)
        _daily.append({"date": _date, "profit_eur": _profit,
                       "charge_price": _cc, "discharge_price": _dr})

    arbitrage_df = pd.DataFrame(_daily)
    arbitrage_df["date"] = pd.to_datetime(arbitrage_df["date"])
    arbitrage_df["cumulative_eur"] = arbitrage_df["profit_eur"].cumsum()

    _rev = arbitrage_df["profit_eur"].sum()
    _payback = _CAPEX_PER_MW / _rev if _rev > 0 else np.inf
    _spread = (arbitrage_df["discharge_price"]
               - arbitrage_df["charge_price"]).mean()

    print(f"Annual arbitrage revenue per MW: €{_rev:,.0f}")
    print(f"Battery CAPEX per MW (4 h, €140/kWh): €{_CAPEX_PER_MW:,.0f}")
    print(f"Simple payback: {_payback:.1f} years")
    print(f"Avg daily spread (top 4 − bottom 4): €{_spread:.1f}/MWh")

    chart_arbitrage = alt.Chart(arbitrage_df).mark_line().encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("cumulative_eur:Q", title="Cumulative arbitrage revenue (€/MW)"),
        tooltip=["date:T", "profit_eur:Q", "cumulative_eur:Q"],
    ).properties(
        width=650, height=350,
        title=f"Battery arbitrage cumulative revenue (payback ≈ {_payback:.1f} years)",
    )
    chart_arbitrage
    return (arbitrage_df,)


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the arbitrage backtest.**
    This asks the private-investor question: can a battery *pay for itself* just by
    buying cheap and selling dear? Each day it "charges" in the 4 cheapest hours and
    "discharges" in the 4 most expensive, keeping the price gap minus efficiency losses.

    The line is cumulative euros earned per MW over the year; the title turns that into
    a simple payback. If payback is reasonable, short-duration batteries can scale on
    market incentives alone — no subsidy required.

    The model now **skips days where the spread wouldn't cover efficiency losses**
    (`max(0, …)`), so it estimates revenue under simple profit-maximizing daily dispatch
    rather than forcing a trade every day. **Caveat:** it still uses *perfect foresight*
    (it knows each day's cheapest and priciest hours in advance), so the result remains
    an optimistic upper bound on real revenue.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## How robust is that payback?

    A single payback number hides its assumptions. Here we split arbitrage revenue by
    month, then test payback across a grid of battery costs (CAPEX) and efficiencies.
    """)
    return


@app.cell
def _(alt, arbitrage_df):
    _ma = arbitrage_df.copy()
    _ma["month_label"] = _ma["date"].dt.strftime("%b")
    _order = _ma.drop_duplicates("month_label").sort_values("date")["month_label"].tolist()
    _ms = _ma.groupby("month_label", sort=False)["profit_eur"].sum().reset_index()

    _chart = alt.Chart(_ms).mark_bar(color="#4C78A8").encode(
        x=alt.X("month_label:N", sort=_order, title="Month"),
        y=alt.Y("profit_eur:Q", title="Monthly arbitrage revenue (€/MW-month)"),
        tooltip=["month_label:N", "profit_eur:Q"],
    ).properties(width=650, height=350,
                 title="When in the year does arbitrage earn the most?")
    _chart
    return


@app.cell
def _(alt, np, pd, storage_df):
    def _annual_arbitrage_revenue(prices, rte):
        _tot = 0.0
        for _date, _dp in prices.groupby(prices.index.date):
            if len(_dp) < 24:
                continue
            _s = _dp.sort_values()
            _cc = _s.iloc[:4].mean()
            _dr = _s.iloc[-4:].mean()
            _tot += max(0.0, (_dr - _cc / rte) * 4)   # skip days that would lose money
        return _tot

    _prices = storage_df["price_eur_mwh"].dropna()
    _rows = []
    for _capex in [100, 140, 200, 300]:
        for _rte in [0.75, 0.80, 0.85, 0.90]:
            _rev = _annual_arbitrage_revenue(_prices, _rte)
            _capex_per_mw = 4 * 1000 * _capex
            _payback = _capex_per_mw / _rev if _rev > 0 else np.inf
            _rows.append({
                "capex_eur_kwh": _capex,
                "rte_label": f"{int(_rte * 100)}%",
                "annual_revenue_eur_mw": _rev,
                "payback_years": _payback,
            })
    _sens = pd.DataFrame(_rows)

    _chart = alt.Chart(_sens).mark_rect().encode(
        x=alt.X("rte_label:N", title="Round-trip efficiency"),
        y=alt.Y("capex_eur_kwh:O", title="CAPEX (€/kWh)"),
        color=alt.Color("payback_years:Q", title="Payback (years)",
                        scale=alt.Scale(scheme="redyellowgreen", reverse=True)),
        tooltip=["capex_eur_kwh:O", "rte_label:N",
                 "annual_revenue_eur_mw:Q", "payback_years:Q"],
    ).properties(width=520, height=350,
                 title="Battery payback under different cost & efficiency assumptions")
    _chart
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the sensitivity heatmap.**
    Each square is one "what if" combination: a battery cost (rows, €/kWh) and an
    efficiency (columns). The color is the payback time — **greener = pays back faster,
    redder = slower**. Cheaper batteries and higher efficiency push you toward the green
    corner (top-right); expensive, lossy ones sit in the red corner.

    It shows the business case isn't a single fact — it's a range that hinges on cost
    and efficiency. The monthly bar chart above adds the seasonal angle: arbitrage
    tends to earn more in months with wilder price swings.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Which technology fits which duration?

    No single technology wins everywhere. The right choice depends on duration,
    cycling frequency, efficiency, and cost per unit of energy stored.
    """)
    return


@app.cell
def _(mo, pd):
    _technology_fit_df = pd.DataFrame([
        {"Technology": "Lithium-ion battery", "2–6 h intraday": "Excellent",
         "12–100 h multi-day": "Weak", "100 h+ seasonal": "Poor",
         "Main strength": "High efficiency, fast response",
         "Main weakness": "Expensive for long duration"},
        {"Technology": "Pumped hydro", "2–6 h intraday": "Good",
         "12–100 h multi-day": "Good", "100 h+ seasonal": "Limited",
         "Main strength": "Mature, long life",
         "Main weakness": "Geographically constrained"},
        {"Technology": "Flow battery / LDES", "2–6 h intraday": "Good",
         "12–100 h multi-day": "Good", "100 h+ seasonal": "Weak",
         "Main strength": "Long cycle life", "Main weakness": "Still scaling"},
        {"Technology": "Hydrogen P2G2P", "2–6 h intraday": "Poor",
         "12–100 h multi-day": "Moderate", "100 h+ seasonal": "Excellent",
         "Main strength": "Seasonal energy storage",
         "Main weakness": "Low round-trip efficiency"},
        {"Technology": "Grid interconnection", "2–6 h intraday": "Excellent",
         "12–100 h multi-day": "Good", "100 h+ seasonal": "Moderate",
         "Main strength": "Geographic smoothing",
         "Main weakness": "Depends on neighboring systems"},
        {"Technology": "Demand response", "2–6 h intraday": "Good",
         "12–100 h multi-day": "Moderate", "100 h+ seasonal": "Weak",
         "Main strength": "Low-cost flexibility",
         "Main weakness": "Limited duration and availability"},
    ])
    mo.ui.table(_technology_fit_df, page_size=10)
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the technology matrix.**
    Read across a row to see where one technology shines and where it struggles. The
    three middle columns are the three time horizons; the last two columns give its
    headline strength and weakness.

    The pattern: lithium-ion owns the **short** column, hydrogen owns the **seasonal**
    column, and pumped hydro / flow batteries / interconnection / demand response fill
    the **middle**. No single row is "Excellent" everywhere — which is exactly why the
    answer is a portfolio.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Three-tier cost summary
    """)
    return


@app.cell
def _(mo, pd):
    storage_tiers_df = pd.DataFrame([
        {
            "Tier": "1. Intraday (daily ramp)",
            "Time horizon": "2–6 hours",
            "Technology": "Lithium-ion BESS",
            "Capacity needed by 2030": "100–170 GWh (Fraunhofer ISE)",
            "CAPEX (€/kWh)": "~140",
            "Total investment (€ bn)": "15–25",
            "Status": "Economic without subsidy; scaling fast",
        },
        {
            "Tier": "2. Multi-day (wind lulls)",
            "Time horizon": "12–100 hours",
            "Technology": "PHS + long-duration batteries",
            "Capacity needed by 2030": "~500 GWh equivalent",
            "CAPEX (€/kWh)": "70–200",
            "Total investment (€ bn)": "50–100",
            "Status": "PHS capped; flow batteries early stage",
        },
        {
            "Tier": "3. Seasonal / Dunkelflaute",
            "Time horizon": "100–1000+ hours",
            "Technology": "Hydrogen P2G2P + H2-CCGT",
            "Capacity needed by 2045": "30–130 TWh (Fraunhofer / EWI)",
            "CAPEX (€/kWh)": "20–50",
            "Total investment (€ bn)": "100–300+",
            "Status": "Strategic bet; needs full H2 economy build-out",
        },
    ])
    mo.ui.table(storage_tiers_df, page_size=5)
    return


@app.cell
def _(mo):
    mo.md(r"""
    **In plain words — the three-tier table.**
    This is the whole notebook boiled into one table. Each row is a *time horizon* the
    grid has to cover, the technology that fits it, roughly how much is needed, what it
    costs, and how mature it is. Tier 1 is here and economic today; Tier 2 is harder and
    partly still developing; Tier 3 is a long-term hydrogen bet. It sets up the
    conclusion directly.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Saving the numbers for the written report

    The charts above live in this notebook, but the group report is written in
    LaTeX. This step saves the exact numbers behind each chart as plain CSV
    files, so the report can draw the same charts directly from real data
    instead of a picture.
    """)
    return


@app.cell
def _(
    arbitrage_df,
    battery_soc_df,
    displacement_df,
    np,
    pd,
    storage_df,
    worst_7d_end,
    worst_7d_start,
    worst_event_df,
):
    # --- 1. Net-export duration curve ---
    _ned = (storage_df[["net_export_gw"]]
            .dropna()
            .sort_values("net_export_gw", ascending=False)
            .reset_index(drop=True))
    _ned["ranked_hour"] = np.arange(1, len(_ned) + 1)
    _ned.to_csv("storage_net_export_duration.csv", index=False)

    # --- 2. Monthly net surplus vs deficit ---
    _imp_m = storage_df["imports_mw"].resample("ME").sum() / 1000
    _exp_m = storage_df["exports_mw"].resample("ME").sum() / 1000
    _mb = pd.DataFrame({
        "month_label": _imp_m.index.strftime("%b"),
        "exports_gwh": _exp_m.values,
        "imports_gwh": _imp_m.values,
    })
    _mb.to_csv("storage_monthly_balance.csv", index=False)

    # --- 3. Daily surplus duration curve ---
    _hourly_surplus_gwh = storage_df["exports_mw"].fillna(0) / 1000
    _daily_stats = _hourly_surplus_gwh.resample("D").sum().reset_index()
    _daily_stats.columns = ["date", "surplus_gwh"]
    _daily_stats = _daily_stats.sort_values("surplus_gwh", ascending=False).reset_index(drop=True)
    _daily_stats["day_rank"] = np.arange(1, len(_daily_stats) + 1)
    _daily_stats.to_csv("storage_daily_surplus_duration.csv", index=False)

    # --- 4. Duration-cost curve (one CSV per technology, avoids filtering in LaTeX) ---
    _COST_BATTERY, _COST_PHS, _COST_H2 = 140, 70, 50
    _durations_h = np.array([1, 2, 4, 6, 8, 12, 24, 48, 72, 120, 168, 336, 720])
    _imports_gw = storage_df["imports_mw"].fillna(0) / 1000
    _shortfall_gwh = [
        _imports_gw.rolling(window=int(_d), min_periods=int(_d)).sum().max()
        for _d in _durations_h
    ]
    _dc = pd.DataFrame({
        "duration_h": _durations_h,
        "cost_liion_beur": [g * 1e6 * _COST_BATTERY / 1e9 for g in _shortfall_gwh],
        "cost_phs_beur": [g * 1e6 * _COST_PHS / 1e9 for g in _shortfall_gwh],
        "cost_h2_beur": [g * 1e6 * _COST_H2 / 1e9 for g in _shortfall_gwh],
    })
    _dc.to_csv("storage_duration_cost.csv", index=False)

    # --- 5. Import displacement curve ---
    displacement_df.to_csv("storage_import_displacement.csv", index=False)

    # --- 6. Worst week: import gap and battery state of charge ---
    _wk_import = worst_event_df[["timestamp", "imports_gw"]].copy()
    _wk_import.to_csv("storage_worst_week_import.csv", index=False)

    _wk_soc = battery_soc_df[
        (battery_soc_df["timestamp"] >= worst_7d_start)
        & (battery_soc_df["timestamp"] <= worst_7d_end)
        & (battery_soc_df["capacity_gwh"].isin([100, 200, 500]))
    ].copy()
    _wk_soc_wide = _wk_soc.pivot(index="timestamp", columns="capacity_gwh", values="soc_pct").reset_index()
    _wk_soc_wide.columns = ["timestamp", "soc_100", "soc_200", "soc_500"]
    _wk_soc_wide.to_csv("storage_worst_week_soc.csv", index=False)

    # --- 7. Arbitrage cumulative revenue ---
    arbitrage_df[["date", "cumulative_eur"]].to_csv("storage_arbitrage_cumulative.csv", index=False)

    print("Written 8 CSV files:")
    print("  storage_net_export_duration.csv")
    print("  storage_monthly_balance.csv")
    print("  storage_daily_surplus_duration.csv")
    print("  storage_duration_cost.csv")
    print("  storage_import_displacement.csv")
    print("  storage_worst_week_import.csv")
    print("  storage_worst_week_soc.csv")
    print("  storage_arbitrage_cumulative.csv")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Saving four more sets of numbers for the written report

    These cover the deficit-event lengths, the marginal value of extra storage,
    imports remaining after storage, battery utilization, and the arbitrage
    sensitivity grid.
    """)
    return


@app.cell
def _(
    arbitrage_df,
    battery_soc_df,
    battery_utilization_df,
    deficit_events_df,
    displacement_df,
    np,
    pd,
    storage_df,
    total_imports_twh,
):
    # --- 9. Deficit event duration: event count and total energy per bucket ---
    _bucket_order = ["1–3 h", "4–6 h", "7–12 h", "13–24 h",
                     "1–3 days", "3–7 days", "7+ days"]
    _cnt = (deficit_events_df
            .groupby("duration_bucket", observed=True)
            .size().reset_index(name="event_count"))
    _en = (deficit_events_df
           .groupby("duration_bucket", observed=True)["total_deficit_gwh"]
           .sum().reset_index())
    _events_export = _cnt.merge(_en, on="duration_bucket")
    _events_export["duration_bucket"] = pd.Categorical(
        _events_export["duration_bucket"], categories=_bucket_order, ordered=True
    )
    _events_export = _events_export.sort_values("duration_bucket")
    _events_export["bucket_index"] = range(1, len(_events_export) + 1)
    _events_export.to_csv("storage_deficit_events.csv", index=False)

    # --- 10. Marginal import displacement (slope between consecutive battery sizes) ---
    _m = displacement_df.copy()
    _m["prev_cap"] = _m["capacity_gwh"].shift()
    _m["prev_disp"] = _m["imports_displaced_twh"].shift()
    _m["added_cap_gwh"] = _m["capacity_gwh"] - _m["prev_cap"]
    _m["extra_disp_twh"] = _m["imports_displaced_twh"] - _m["prev_disp"]
    _m["mwh_per_added_gwh"] = _m["extra_disp_twh"] * 1_000_000 / _m["added_cap_gwh"]
    _m = _m.dropna()
    _m[["capacity_gwh", "mwh_per_added_gwh"]].to_csv("storage_marginal_displacement.csv", index=False)

    # --- 11. Imports remaining after storage ---
    _r = displacement_df.copy()
    _r["imports_remaining_twh"] = total_imports_twh - _r["imports_displaced_twh"]
    _r[["capacity_gwh", "imports_remaining_twh"]].to_csv("storage_imports_remaining.csv", index=False)

    # --- 12. Battery utilization: full cycles per year vs capacity ---
    battery_utilization_df[["capacity_gwh", "full_cycles_per_year", "avg_soc_pct"]].to_csv(
        "storage_battery_utilization.csv", index=False
    )

    # --- 13. Monthly arbitrage revenue ---
    _ma = arbitrage_df.copy()
    _ma["month_label"] = _ma["date"].dt.strftime("%b")
    _month_order = _ma.drop_duplicates("month_label").sort_values("date")["month_label"].tolist()
    _ms = _ma.groupby("month_label", sort=False)["profit_eur"].sum().reset_index()
    _ms["month_label"] = pd.Categorical(_ms["month_label"], categories=_month_order, ordered=True)
    _ms = _ms.sort_values("month_label")
    _ms["month_index"] = range(1, len(_ms) + 1)
    _ms.to_csv("storage_monthly_arbitrage.csv", index=False)

    # --- 14. Payback sensitivity grid (CAPEX x round-trip efficiency) ---
    def _annual_arbitrage_revenue(prices, rte):
        _tot = 0.0
        for _date, _dp in prices.groupby(prices.index.date):
            if len(_dp) < 24:
                continue
            _s = _dp.sort_values()
            _cc = _s.iloc[:4].mean()
            _dr = _s.iloc[-4:].mean()
            _tot += max(0.0, (_dr - _cc / rte) * 4)
        return _tot

    _prices = storage_df["price_eur_mwh"].dropna()
    _sens_rows = []
    for _capex in [100, 140, 200, 300]:
        for _rte in [0.75, 0.80, 0.85, 0.90]:
            _rev = _annual_arbitrage_revenue(_prices, _rte)
            _capex_per_mw = 4 * 1000 * _capex
            _payback = _capex_per_mw / _rev if _rev > 0 else np.inf
            _sens_rows.append({
                "capex_eur_kwh": _capex,
                "rte_pct": int(_rte * 100),
                "payback_years": _payback,
            })
    _sens_long = pd.DataFrame(_sens_rows)
    _sens_wide = _sens_long.pivot(index="capex_eur_kwh", columns="rte_pct", values="payback_years")
    _sens_wide.columns = [f"payback_{c}pct" for c in _sens_wide.columns]
    _sens_wide = _sens_wide.reset_index()
    _sens_wide.to_csv("storage_payback_sensitivity.csv", index=False)

    # --- 15. Full-year battery state of charge, 7-day average, for 3 sizes ---
    _sel = battery_soc_df[battery_soc_df["capacity_gwh"].isin([100, 200, 500])].copy()
    _sel = _sel.set_index("timestamp")
    _daily = (_sel.groupby("capacity_gwh")["soc_pct"]
              .resample("D").mean().reset_index())
    _daily["soc_pct_7d_avg"] = (
        _daily.groupby("capacity_gwh")["soc_pct"]
        .transform(lambda s: s.rolling(window=7, min_periods=1).mean())
    )
    _soc_wide = _daily.pivot(index="timestamp", columns="capacity_gwh", values="soc_pct_7d_avg").reset_index()
    _soc_wide.columns = ["date", "soc_100", "soc_200", "soc_500"]
    _soc_wide.to_csv("storage_soc_full_year.csv", index=False)

    print("Written 7 additional CSV files:")
    print("  storage_deficit_events.csv")
    print("  storage_marginal_displacement.csv")
    print("  storage_imports_remaining.csv")
    print("  storage_battery_utilization.csv")
    print("  storage_monthly_arbitrage.csv")
    print("  storage_payback_sensitivity.csv")
    print("  storage_soc_full_year.csv")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## What did we learn? — evidence at a glance

    | Evidence | What it shows |
    | --- | --- |
    | Net-export duration curve | Germany has both surplus and deficit hours — a timing mismatch, not just a total shortage |
    | Net-deficit-event duration | Some net-deficit periods are short (battery-friendly); others are multi-day and need long-duration flexibility |
    | Monthly net surplus/deficit | The mismatch has a seasonal structure batteries can't bridge |
    | Daily surplus curve | Only a handful of days produce enough surplus to fill a very large battery |
    | Net-import displacement curve | Batteries reduce net-import deficit, but the benefit flattens as size grows |
    | Marginal displacement | Each extra GWh removes less net-import deficit than the last |
    | Utilization / full cycles | Larger batteries cycle less and sit mostly idle |
    | Worst-week stress test | Batteries drain to empty during long Dunkelflaute-style periods |
    | Duration-cost curve | Battery cost rises sharply with duration; hydrogen becomes more suitable for long-duration storage |
    | Arbitrage backtest | Short-duration batteries can have a standalone market case |

    Read top to bottom, the table is the whole argument: storage is very useful at short
    duration and near its first ~100 GWh, then runs into diminishing returns and a hard
    seasonal wall.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Sources, assumptions, and caveats

    **Primary data.** All grid data used in this notebook is downloaded from **SMARD**,
    the German Federal Network Agency / Bundesnetzagentur market-data platform:
    <https://www.smard.de>. The notebook uses hourly 2025 data for generation by
    source, load, day-ahead price, and Germany's net export position.

    **External reference checks for 2025.** Fraunhofer ISE's page **"German Public
    Electricity Generation in 2025: Wind and Solar Power Take the Lead For the First
    Time"** reports that renewables accounted for **55.9% of Germany's net public
    electricity generation in 2025**. The same Fraunhofer ISE page states that
    Germany's large-scale battery storage capacity increased from **2.3 GWh to
    3.7 GWh** during 2025, that total installed battery storage was **just under
    25 GWh**, and that Fraunhofer ISE model results show a **100–170 GWh battery
    storage requirement by 2030**, depending on the scenario:
    <https://www.ise.fraunhofer.de/en/press-media/press-releases/2026/german-public-electricity-generation-in-2025-wind-and-solar-power-take-the-lead.html>

    Bundesnetzagentur's 2025 SMARD market-data release reports Germany's **gross**
    commercial electricity trade at **76.2 TWh imports** and **54.3 TWh exports**,
    giving **21.9 TWh net imports** in 2025:
    <https://www.bundesnetzagentur.de/SharedDocs/Pressemitteilungen/EN/2026/20260104_SMARD.html>

    Important distinction: those gross import/export totals are **not directly
    comparable** to this notebook's hourly net-import deficit and net-export surplus
    sums. Germany can import from one neighbor and export to another in the same hour;
    official gross trade counts both flows, while the `net_export_mw` series collapses
    them into one net hourly position. The directly comparable external check is the
    annual **net-import balance**.

    **Storage capacity references used in the interpretation.**

    - **Intraday batteries.** The **100–170 GWh by 2030** range is taken from the
      Fraunhofer ISE 2025 electricity-generation analysis above. In this notebook it is
      used as an external reference point, not as a result produced by the model.
    - **Seasonal hydrogen storage.** German hydrogen-storage estimates vary by scenario.
      A dena analysis of Germany's long-term scenarios reports hydrogen storage demand
      of about **2 TWh in 2030** and up to **72–74 TWh in 2045**. BMWK's hydrogen-storage
      white paper is reported as estimating **76–80 TWh by 2045**. Because published
      values vary by model boundary and sector coverage, the three-tier table should be
      read as an **indicative range**, not a precise forecast.

    **Cost assumptions.** The duration-cost curve uses simplified storage-energy CAPEX
    assumptions for comparison across durations: **Li-ion 4 h battery ≈ €140/kWh,
    pumped hydro ≈ €70/kWh, and hydrogen P2G2P ≈ €50/kWh** of storage capacity.
    These are modelling inputs, not measured values. Results scale linearly with these
    inputs, so the most important insight is the **shape** of the curve: battery cost
    rises sharply as duration increases, while lower energy-capacity-cost technologies
    become more suitable for long-duration storage. These values should be replaced with
    the final cited assumptions used in the written report.

    **How to compare this notebook with the external reports.** The notebook calculates
    its own net-import deficit, net-export surplus, and storage-displacement results
    directly from hourly SMARD net-export data. Compare the notebook's **net-import
    balance** with the official 21.9 TWh net-import reference. Do not compare the
    notebook's net-deficit and net-surplus sums directly with official gross imports
    and gross exports. Small differences can still happen because of data corrections,
    market-region definitions, timestamp handling, and whether values are provisional
    or final. Large differences would indicate that the SMARD series ID, region, cache,
    or local-year filtering should be checked.

    **Modelling caveats.**

    1. **Net exports as a proxy for storage surplus/deficit.** The notebook uses hourly
       net trade, not gross flows; some trade is price-driven rather than physical.
    2. **4-hour power scaling.** Battery power is `capacity / 4`, which over-rates very
       large systems — treat large-capacity displacement as an optimistic upper bound.
    3. **Battery starts empty**, so annual totals shift slightly with the initial state
       of charge.
    4. **Single weather year (2025).** A different weather year could change the
       worst-week numbers and the seasonal picture.
    5. **Perfect-foresight arbitrage.** The backtest knows each day's cheapest and most
       expensive hours in advance, so its revenue is an optimistic ceiling.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Conclusion

    Germany's storage requirement is not one number — it is a **layered flexibility
    problem**.

    **Short-duration lithium-ion is already useful today.** It charges on surplus
    hours, discharges on net-deficit hours, and can earn its keep from daily price spreads.
    The first block of capacity (~100 GWh, near Fraunhofer ISE's 2030 estimate) does
    most of the work because it cycles often and displaces the common net-deficit hours.

    **But the returns diminish fast.** The displacement curve, the marginal-value
    curve, and the utilization metrics all point the same way: each extra GWh displaces
    less net-import deficit and cycles less often. Very large battery fleets add resilience but sit
    mostly idle — an expensive way to buy the last few percent.

    **Long-duration reliability is a different problem.** The net-deficit-event analysis
    and the worst-week stress test show batteries draining to empty during multi-day,
    Dunkelflaute-style lulls. They shave the first part of a long shortage but cannot
    economically carry the system through it unless built at enormous, underused scale.

    So the strategy is layered:

    1. **Intraday:** lithium-ion for 2–6 h balancing and price arbitrage — ~€20 bn for
       Tier 1 by 2030.
    2. **Multi-day:** pumped hydro (geographically capped in Germany), long-duration
       batteries, demand response, and interconnection — €50–100 bn through the 2030s.
    3. **Seasonal:** hydrogen, dispatchable H2-ready backup, and strategic reserves —
       hundreds of billions over decades.

    **Bottom line:** storage is a *complement* to the grid, not a substitute. Batteries
    reduce net-import dependence but cannot eliminate it, because storage only shifts energy
    that already existed as surplus. Germany's future system needs a **portfolio** of
    flexibility, each technology matched to the duration it solves best — with European
    grid interconnection remaining structurally necessary throughout.

    ---
    *Two honest caveats:* this is a **single weather year (2025)** — a different year
    could shift the worst-week numbers — and the **arbitrage backtest assumes perfect
    foresight**, so its revenue is an optimistic ceiling rather than a realistic
    expectation.
    """)
    return


if __name__ == "__main__":
    app.run()
