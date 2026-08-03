r"""Shared PNG and PGF export helpers for the trade-analysis notebook.

The notebook continues to display Matplotlib figures and save PNG previews, but
each fixed report figure is also written as a LuaLaTeX-compatible ``.pgf`` file
with the same stem.  The PGF output can be imported into the thesis with
``\input`` (or the thesis' ``\safepgfinput`` helper).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl


PGF_SETTINGS = {
    "pgf.texsystem": "lualatex",
    "pgf.rcfonts": False,
    "text.usetex": False,
}


def save_png_and_pgf(fig, png_name: str, output_dir: Path):
    """Save one Matplotlib figure as both PNG and PGF.

    Parameters
    ----------
    fig:
        The completed Matplotlib figure.
    png_name:
        Existing PNG filename used by the original notebook.  The PGF filename
        is derived automatically by replacing the suffix with ``.pgf``.
    output_dir:
        Destination directory for both files.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / png_name
    pgf_path = png_path.with_suffix(".pgf")

    fig.savefig(png_path, dpi=220, bbox_inches="tight", facecolor="white")
    try:
        with mpl.rc_context(PGF_SETTINGS):
            fig.savefig(
                pgf_path,
                format="pgf",
                backend="pgf",
                bbox_inches="tight",
                facecolor="white",
            )
    except Exception as exc:
        raise RuntimeError(
            "PGF export failed. Install TeX Live or MiKTeX with LuaLaTeX, "
            "then make sure the 'lualatex' command is available on PATH."
        ) from exc

    # A self-contained PGF must not reference Matplotlib's optional raster
    # sidecars. The notebook heatmaps use vector cells and colour scales to
    # guarantee this property.
    if "\\includegraphics" in pgf_path.read_text(encoding="utf-8"):
        raise RuntimeError(
            f"{pgf_path.name} unexpectedly references an auxiliary image."
        )

    return fig
