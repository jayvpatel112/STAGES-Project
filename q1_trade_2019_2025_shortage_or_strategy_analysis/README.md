# Report analyses

The analyses are grouped by subject so that the repository is easy to navigate
without mixing report notebooks into the project root.

| Analysis | Report purpose | Notebook |
|---|---|---|
| `quarterly_2025/q1/` | Detailed Q1 2025 generation, demand, residual load, and optional weather analysis | `q1_2025_detailed_analysis.py` |
| `trade/trade_2025/` | Focused 2025 import/export analysis using the shared SMARD helpers | `trade_2025_analysis.py` |
| `trade/bilateral_2019_2025/` | Bilateral electricity trade with neighbouring countries | `bilateral_trade_analysis.py` |
| `trade/shortage_or_strategy_2019_2025/` | Tests whether Germany's net-import position is better explained by shortage or market strategy | `net_importer_analysis.py` |

Run each notebook using the instructions in its own README. The Q1 and two
2019--2025 trade folders keep their data caches and generated figures locally.
The focused 2025 notebook deliberately reads the shared `data/cleaned/` dataset
and imports the repository-level `utils.py` helpers.

The two 2019--2025 trade analyses contain PGF exporters and LaTeX replacement
mappings. Generated PNG, PGF, cache, and report files are not committed.
