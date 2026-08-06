# Germany's Cross-Border Electricity Trade — 2019 to 2025

Marimo notebook analysing Germany's electricity trade with every neighbour
across seven years. Data comes from the **Energy-Charts API** (Fraunhofer ISE),
which aggregates the official ENTSO-E transparency records. Free, CC BY 4.0,
no API key.

## Run it

```
cd analyses/trade/bilateral_2019_2025
pip install -r requirements.txt
python -m marimo edit bilateral_trade_analysis.py
```

Click **Fetch data and export PNG + PGF figures**. The first run downloads seven
yearly files and caches them under `data/_cache/`; re-runs are instant. Every
figure is shown inline and written to `figures/` in two forms:

- `.png` — 220-dpi preview
- `.pgf` — vector figure for the LaTeX thesis

PGF export uses `lualatex`, so a local TeX Live or MiKTeX installation with
LuaLaTeX must be available on your system path.

The downloaded API cache and generated figure files are intentionally ignored
by Git and are recreated by the notebook.

## What was wrong before, and what's fixed

Two bugs in the previous version:

1. **Silent zeros.** The parser looked for two-letter codes (`FR`, `NL`) but
   Energy-Charts returns full English names, often with a bidding-zone suffix
   (`"Denmark 1"`, `"Norway 2"`, `"Sweden 4"`). Almost every column ended up
   empty and the balances came out as +0 across the board.

2. **Marimo cell wiring.** Names like `mo`, `Path`, `plt` were defined in one
   cell but never returned, so downstream cells could not see them and threw
   `NameError`. Marimo requires every shared name to be an explicit `return`
   from a cell and an explicit parameter of every cell that uses it.

Both are fixed in the new notebook:

- The parser matches every real name variant against a canonical neighbour
  label, collapses bidding zones (Denmark 1 + Denmark 2 → Denmark), drops
  aggregate rows like `sum`, detects the response resolution (15 min) and
  converts power (GW or MW) to energy (TWh) automatically.
- Every cell's imports and shared values are explicitly returned; every
  consumer cell takes them as parameters. Cell functions have proper names,
  not underscore-prefixed names.
- A **Data loaded** banner appears right after the fetch, listing row count,
  resolution, matched neighbours, and ignored rows — so you can sanity-check
  in one glance.

## The nine figures

Each stem below is exported as both `.png` and `.pgf`.

| File stem | Shows |
|------|-------|
| `trade_01_annual_net_balance`     | The export→import flip, per year |
| `trade_02_gross_imp_exp`          | Gross imports vs gross exports each year |
| `trade_03_stacked_by_neighbour`   | Which neighbours drove the swing |
| `trade_04_partners_imp_exp`       | Import partners vs export partners |
| `trade_05_net_per_neighbour`      | Net position by neighbour, sorted |
| `trade_06_heatmap`                | Year × neighbour matrix with numbers |
| `trade_07_monthly_seasonal`       | Monthly net balance — seasonal rhythm |
| `trade_08_month_year_heatmap`     | Month × year matrix (seasonality + trend) |
| `trade_09_relationship_evolution` | Line per neighbour, 2019 → 2025 |

Plus an interactive year picker for per-neighbour breakdown of any single year.

The two heatmaps use vector cells and vector colour scales. Their `.pgf` files
therefore do not depend on hidden `-img0.png` sidecar files.

## Put the PGF figures into Overleaf

1. Run the notebook and upload the nine generated `.pgf` files to Overleaf's
   `figures/` folder.
2. Compile the thesis using LuaLaTeX.
3. Follow `latex_pgf_replacements.tex`: add its small PGF figure macro before
   `\begin{document}`, then replace the nine old PNG calls with the supplied
   PGF calls. The existing captions and labels are already included there.

For example:

```latex
\begin{figure}[!htbp]
    \centering
    \safepgfinput{figures/trade_01_annual_net_balance.pgf}
    \caption{Annual net electricity balance for Germany, 2019--2025.}
    \label{fig:trade_annual_net}
\end{figure}
```

The thesis already defines `\safepgfinput`, so no new macro is required.

## Optional export check

```bash
python validate_pgf_export.py
```

This creates representative versions of all nine figure types in a temporary
directory and imports them into one LuaLaTeX test document. It does not download
or alter the real Energy-Charts data.

## Sign convention (verify on first run)

**Positive = net export from Germany. Negative = net import into Germany.**

On the first chart, 2019 should be positive (Germany was a large net exporter)
and 2024–2025 should be negative (net importer). If the signs look inverted,
tell me and I will adjust — but Energy-Charts follows the same convention as
this notebook, so this should match.

## Where it feeds the report

These figures populate the **Electricity Trade** chapter, which documents
*what* happened. The following chapter (already drafted) — *Net Importer:
Strategy or Shortage?* — answers *why*.
