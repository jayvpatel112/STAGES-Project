# STAGES Project

Marimo-based analyses of Germany's electricity system, with a focus on
renewable generation, electricity demand, weather, cross-border trade, storage,
and self-sufficiency.

The repository combines reusable project-level notebooks with focused analyses
that support individual sections of the STAGES report. Source code and
environment definitions are version-controlled; downloaded API data, caches,
and generated figures are recreated locally.

## Research scope

The project investigates:

- Germany's electricity generation mix and demand;
- the contribution and variability of wind and solar generation;
- relationships between weather and renewable output;
- quarterly electricity-system behaviour in 2025;
- Germany's cross-border electricity trade in 2025 and from 2019 to 2025;
- the shift from net exporter to net importer;
- whether the import shift is consistent with shortage or market-based
  operation in an interconnected European electricity system; and
- the role of storage in renewable self-sufficiency.

## Repository structure

```text
STAGES-Project/
├── data/                           # Shared downloaded and processed data
├── layouts/                        # Shared notebook layout resources
├── q1_trade_2019_2025_shortage_or_strategy_analysis/
│   ├── quarterly_2025/
│   │   └── q1/                     # Detailed Q1 2025 analysis
│   ├── trade/
│   │   ├── trade_2025/             # Focused 2025 trade analysis
│   │   ├── bilateral_2019_2025/    # Bilateral trade by neighbour
│   │   └── shortage_or_strategy_2019_2025/
│   └── README.md                   # Detailed analysis map
├── q3_and_storage_analysis/        # Supporting Q3 and storage work
├── q4_and_storage_analysis/        # Supporting Q4 and storage work
├── stages_analysis.py              # Main electricity and weather notebook
├── storage.py                      # Storage and self-sufficiency notebook
├── utils.py                        # Shared data-loading helpers
├── pyproject.toml                  # Project metadata and dependencies
└── uv.lock                         # Locked Python environment
```

## Notebook map

| Notebook or directory | Purpose |
|---|---|
| `stages_analysis.py` | Main electricity-generation, demand, renewable, and weather analysis |
| `storage.py` | Storage requirements and renewable self-sufficiency analysis |
| `q1_trade_2019_2025_shortage_or_strategy_analysis/quarterly_2025/q1/q1_2025_detailed_analysis.py` | Detailed Q1 2025 generation, demand, residual-load, and optional weather analysis |
| `q1_trade_2019_2025_shortage_or_strategy_analysis/trade/trade_2025/trade_2025_analysis.py` | Focused country-level import and export analysis for 2025 |
| `q1_trade_2019_2025_shortage_or_strategy_analysis/trade/bilateral_2019_2025/bilateral_trade_analysis.py` | Bilateral commercial electricity exchanges between Germany and neighbouring countries, 2019–2025 |
| `q1_trade_2019_2025_shortage_or_strategy_analysis/trade/shortage_or_strategy_2019_2025/net_importer_analysis.py` | Analysis of the factors associated with Germany's shift to net imports |
| `q3_and_storage_analysis/` | Supporting Q3 and storage analyses used in the report |
| `q4_and_storage_analysis/` | Supporting Q4 and storage analyses used in the report |

Each focused analysis directory contains its own README with additional data,
output, and execution details.

## Environment setup

The repository-level environment is defined by `pyproject.toml` and `uv.lock`.
Install the locked dependencies from the repository root:

```bash
uv sync
```

The root `uv` environment is the canonical project environment. Some focused
analysis directories also contain a `requirements.txt` so that they can be run
independently, but these files do not replace the repository lockfile.

## Running the notebooks

Run all commands from the repository root.

Main electricity and weather analysis:

```bash
uv run marimo edit stages_analysis.py
```

Storage and self-sufficiency analysis:

```bash
uv run marimo edit storage.py
```

Detailed Q1 2025 analysis:

```bash
uv run marimo edit q1_trade_2019_2025_shortage_or_strategy_analysis/quarterly_2025/q1/q1_2025_detailed_analysis.py
```

Focused 2025 trade analysis:

```bash
uv run marimo edit q1_trade_2019_2025_shortage_or_strategy_analysis/trade/trade_2025/trade_2025_analysis.py
```

Bilateral trade analysis for 2019–2025:

```bash
uv run marimo edit q1_trade_2019_2025_shortage_or_strategy_analysis/trade/bilateral_2019_2025/bilateral_trade_analysis.py
```

Shortage-or-strategy analysis:

```bash
uv run marimo edit q1_trade_2019_2025_shortage_or_strategy_analysis/trade/shortage_or_strategy_2019_2025/net_importer_analysis.py
```

Marimo opens an interactive editor in the browser. Run a notebook from top to
bottom before using its tables or figures in the report.

## Data sources

The analyses use public electricity-system and weather data, primarily from:

- **SMARD / Bundesnetzagentur** for German generation, demand, prices, and
  commercial foreign-trade data;
- **Energy-Charts / Fraunhofer ISE** for bilateral cross-border commercial
  exchanges; and
- **Bright Sky / DWD** for optional weather observations used in the detailed
  Q1 analysis.

The individual notebooks document their requested variables, time resolution,
transformations, and cache locations.

## Trade definitions and sign convention

The bilateral notebook uses the Energy-Charts `/cbet` endpoint. This endpoint
contains scheduled commercial exchanges, not physical cross-border flows.

| Stage | Positive value | Negative value |
|---|---|---|
| Raw Energy-Charts `/cbet` response | Import into Germany | Export from Germany |
| Project net-balance convention | Net export from Germany | Net import into Germany |

The project reports net trade as:

```text
net trade = gross exports - gross imports
```

Accordingly, a positive annual balance means Germany was a net exporter and a
negative annual balance means Germany was a net importer. The bilateral
notebook converts the API signs before aggregation and validates that net trade
equals gross exports minus gross imports.

## Generated data and outputs

The notebooks create their required directories and cache files on first use.
Depending on the analysis, generated outputs include:

- downloaded API responses and cleaned CSV files;
- PNG previews;
- PGF figures for the LaTeX report;
- summary tables and report-ready metrics; and
- interactive Marimo views.

Downloaded caches and generated outputs are intentionally excluded from version
control. If an output is missing, rerun the corresponding notebook rather than
committing a local cache. PGF export requires a working LuaLaTeX installation.

## Reproducibility notes

- Use the locked `uv` environment when reproducing results.
- Keep raw API responses separate from processed data.
- Record the data period, resolution, endpoint, and sign convention used by
  each analysis.
- Review notebook data-quality checks before accepting generated values.
- Regenerate figures after changing data processing or trade-sign handling.
- Treat causal explanations cautiously: observed trade patterns alone do not
  identify prices, congestion, generation availability, or market strategy as
  the sole cause.

## Contributing

Before committing changes:

```bash
git status
git diff --check
```

Do not commit virtual environments, API caches, Marimo session files, Python
bytecode, or generated figures unless a particular report workflow explicitly
requires a versioned output.
