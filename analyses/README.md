# Report analyses

Each folder below is deliberately self-contained so that generic filenames such
as `notebook.py`, `pgf_export.py`, `data/`, and `figures/` do not collide.

| Analysis | Report purpose | Notebook |
|---|---|---|
| `quarterly_2025/q1/` | Detailed Q1 2025 generation, demand, residual load, and optional weather analysis | `q1_2025_detailed_analysis.py` |
| `net_importer_2019_2025/` | Tests whether Germany's net-import position is better explained by shortage or market strategy | `notebook.py` |
| `electricity_trade_2019_2025/` | Analyses bilateral electricity trade with neighbouring countries | `trade_notebook.py` |

Run a notebook from its own directory so that its local `data/` and `figures/`
paths resolve correctly. Each folder contains a detailed README and a standalone
`requirements.txt`; the repository-wide `pyproject.toml` can also be used.

The two 2019--2025 analyses contain PGF exporters and LaTeX replacement mappings.
Generated PNG, PGF, cache, and report files are not committed.
