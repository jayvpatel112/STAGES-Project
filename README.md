# STAGES Project

Marimo-based analyses for the STAGES project on Germany's electricity system,
renewable generation, cross-border trade, and storage.

## Existing project notebooks

- `stages_analysis.py` — main electricity and weather analysis
- `storage.py` — storage and self-sufficiency analysis
- `utils.py` — shared data-loading helpers

## Additional report analyses

The `analyses/` directory contains the detailed quarterly and trade
investigations that support specific chapters of the report. This includes the
2025 trade notebook, which previously lived at the repository root. See
`analyses/README.md` for the complete notebook map and run commands.

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
