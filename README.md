# STAGES Project

Marimo-based analyses for the STAGES project on Germany's electricity system,
renewable generation, cross-border trade, and storage.

## Existing project notebooks

- `stages_analysis.py` — main electricity and weather analysis
- `storage.py` — storage and self-sufficiency analysis
- `trade_analysis_2025.py` — existing 2025 trade analysis
- `utils.py` — shared data-loading helpers

## Additional report analyses

The `analyses/` directory contains self-contained investigations that support
specific chapters of the report. See `analyses/README.md` for their purpose and
run commands.

## Environment

The shared environment is defined by `pyproject.toml` and `uv.lock`.

```bash
uv sync
```

Open a notebook with, for example:

```bash
uv run marimo edit stages_analysis.py
```

Downloaded API caches and generated analysis figures are excluded from version
control. They are recreated by the notebooks.
