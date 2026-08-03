# STAGES — Germany's Electricity Import Shift

> *A self-contained Marimo notebook that asks: did Germany become a net electricity
> importer because of a production shortage — or because importing is the rational
> choice in an integrated European market?*
>
> **100% real data. No synthetic numbers.** Everything is fetched live from SMARD.de
> (the Bundesnetzagentur's official electricity market platform) by the notebook itself.

---

## Quick start

```bash
cd analyses/net_importer_2019_2025
pip install -r requirements.txt
python -m marimo edit notebook.py
```

Then, in the notebook, click the green **“Fetch / refresh real data from SMARD.de”**
button near the top. The first fetch takes a minute and is cached to
`data/_cache/`, so every later run is instant. Until you click it, the analysis
sections politely wait — no placeholder/synthetic data is ever shown.

## Export the thesis figures as PGF

The notebook now includes an **“Export the eight thesis plots as PGF”** button.
Use it after the SMARD data has loaded. It creates these files in `figures/`:

```text
net_balance_annual.pgf
generation_mix_annual.pgf
nuclear_phaseout.pgf
price_2022.pgf
seasonal_rhythm.pgf
residual_anomaly.pgf
cost_substitution.pgf
renewable_share_demand.pgf
```

Matching PNG previews are created beside them for visual checking. The Plotly
dashboard remains interactive and is intentionally not exported.

PGF generation requires a working `lualatex` command. In Overleaf, upload the
eight `.pgf` files to the `figures` folder, select **LuaLaTeX**, and replace each
PNG inclusion with the matching `\safepgfinput{...}` command shown in
`latex_pgf_replacements.tex`.

(Use `python -m marimo` if the bare `marimo` command isn't on your PATH — common with Anaconda.)

The API cache and generated figure files are intentionally ignored by Git and
are recreated by the notebook.

---

## What's inside

The notebook is fully self-contained: the SMARD fetching logic, the data processing,
the plot styling helpers, and every chart are all defined in `notebook.py` itself.
There are no separate data scripts to run.

It answers nine connected questions, then ends with an interactive dashboard:

| # | Question |
|---|----------|
| Q1 | When did Germany cross from exporter to importer? |
| Q2 | How did the generation mix change? |
| Q3 | How much did the nuclear phase-out matter? |
| Q4 | What did the 2022 energy war do — and why did Germany still export that year? |
| Q5 | Is there a seasonal rhythm to imports? |
| Q6 | Does residual load predict imports? |
| Q7 | Is importing often the cheaper choice? |
| Q8 | Is the transition progressing despite the imports? |
| 📊 | **Interactive dashboard** — pick any year and inspect it month by month |
| — | Conclusion: shortage or strategy? |

---

## Data & method

- **Generation, load, residual load** — real measured values from SMARD's public
  `chart_data` JSON API (filters for every source, region `DE`, monthly resolution).
- **Net trade** is derived as `total generation − load`, a transparent system-level
  proxy whose sign and trend match Germany's official net position. The notebook
  states this openly and cross-checks against the Bundesnetzagentur's published
  commercial-trade figures.
- **Wholesale prices** — the notebook tries to fetch them live; if that endpoint is
  unavailable it falls back to real, published annual day-ahead averages
  (BNetzA / Fraunhofer ISE / Open Energy Tracker). Either way the numbers are real.
- **Energy-crisis context** (2022 gas shock, French nuclear collapse) is sourced from
  SMARD and Banque de France reviews and cited in the relevant section.

SMARD data is published under CC BY 4.0.

### Optional: per-country trade

SMARD's simple API doesn't expose gross bilateral flows. If you want a country-level
breakdown, download a "Commercial foreign trade" CSV from
<https://www.smard.de/en/downloadcenter/download-market-data> — but the nine core
questions and the dashboard work fully without it.

---

## Project context

Part of the **STAGES** project on whether renewable energy can meet Germany's
electricity demands. The conclusion the data supports: Germany's net-import position
is **strategy, not shortage** — a feature of a transitioning, integrated electricity
system in which importing is frequently the cheaper and lower-carbon choice.
