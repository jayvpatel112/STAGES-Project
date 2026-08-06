# Germany's 2025 Electricity Trade

This Marimo notebook provides a focused analysis of Germany's cross-border
electricity imports and exports during 2025. It uses the repository-level
`utils.py` helpers and stores its downloaded cache in the shared
`data/cleaned/` directory.

## Run it

From the repository root:

```bash
uv sync
uv run marimo edit analyses/trade/trade_2025/trade_2025_analysis.py
```

The notebook creates `data/cleaned/smard_trade_2025_country_hourly.csv` on its
first successful SMARD download. That generated cache is excluded from Git.

## Scope

The notebook answers five questions:

1. Was Germany a net importer or exporter in 2025?
2. Which partners accounted for the largest imports and exports?
3. How did trade change month by month?
4. Were imports associated with high residual load or low renewable output?
5. Were exports associated with renewable-surplus periods?

For the longer historical and bilateral views, see the neighbouring
`bilateral_2019_2025/` and `shortage_or_strategy_2019_2025/` analyses.
