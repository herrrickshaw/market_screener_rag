#!/usr/bin/env python3
"""
edge_matrix.py — the Ted Williams / Buffett "fat-pitch" grid: filter/strategy × market,
coloured by where the real edge is, so you only SWING where your batting average is high.

Each cell = the backtested (or paper-track) edge for running that filter in that market,
with its significance. Green = the happy zone (swing); red = cold corner (take the pitch);
grey = not enough data to call. Sources: this repo's committed backtests + the paper-track.

Output: reports/edge_matrix.csv + reports/edge_matrix.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (backend must be set before this import)

HERE = Path(__file__).resolve().parent
REPORTS_DIR = HERE / "reports"
MKTS = ["IN", "US", "KR", "JP", "EU", "CN"]

SCORE_STRONG = 2        # validated edge: swing
SCORE_MIN, SCORE_MAX = -2, 2
GREY = "#d9d9d9"
GREY_PREFIX = "—"       # labels starting with this are "not enough data" -> grey cell

# each cell: (score in [-2..+2] for colour, short label with the number + significance)
# score: +2 strong validated edge · +1 positive · 0 underpowered/untested/neutral ·
#        -1 validated-negative / fails · (grey when label starts with '—')
G = lambda s, t: (s, t)  # noqa: E731  (kept: the table below reads as a grid)
MATRIX = {
 "Value-reversion (cheap−rich, 6M)": {
   "IN": G(2, "+5.3% t2.5"), "US": G(2, "+1.7%/3M t2.3"), "KR": G(1, "+3.9% t1.5"),
   "JP": G(2, "+6.6% t4.8"), "EU": G(0, "— underpwr"), "CN": G(-1, "≈0 t0.0 FAILS")},
 "Value+Quality L/S (cheap∩hiROE − rich∩loROE)": {
   "IN": G(-1, "−1.0% FAILS"), "US": G(1, "+1.7% t1.0"), "KR": G(2, "+4.8% t4.2"),
   "JP": G(0, "— untested"), "EU": G(0, "— no fund"), "CN": G(0, "— untested")},
 "Momentum / Trend (bull, Deflated-Sharpe)": {
   "IN": G(2, "trend DSR.99"), "US": G(1, "mom DSR.90 frag"), "KR": G(2, "breakout DSR.99"),
   "JP": G(-1, "no DSR survivor"), "EU": G(2, "mom DSR.99"), "CN": G(0, "— untested")},
 "Mean-reversion (bear regime)": {
   "IN": G(-1, "weak"), "US": G(0, "fails DSR"), "KR": G(0, "fails DSR"),
   "JP": G(0, "fails DSR"), "EU": G(0, "fails DSR"), "CN": G(0, "—")},
 "Darvas breakout (paper-track excess)": {
   "IN": G(-1, "−0.29%"), "US": G(1, "+1.11%"), "KR": G(0, "— thin"),
   "JP": G(0, "— thin"), "EU": G(1, "+1.58%"), "CN": G(0, "—")},
 "Golden cross 50>200 (paper-track)": {
   "IN": G(1, "+0.61%"), "US": G(0, "— thin"), "KR": G(0, "— thin"),
   "JP": G(0, "— thin"), "EU": G(0, "— thin"), "CN": G(0, "—")},
 "Piotroski F-score / quality": {
   "IN": G(0, "liq-gated"), "US": G(-1, "INVERTED"), "KR": G(0, "—"),
   "JP": G(0, "—"), "EU": G(0, "—"), "CN": G(0, "—")},
}


# ─────────────────────────── pure builders ───────────────────────────
def score_grid(matrix: dict = MATRIX) -> np.ndarray:
    """Scores as a float array, shape (strategies, markets)."""
    return np.array([[matrix[r][m][0] for m in MKTS] for r in matrix], float)


def label_grid(matrix: dict = MATRIX) -> list[list[str]]:
    """Cell labels, shape (strategies, markets)."""
    return [[matrix[r][m][1] for m in MKTS] for r in matrix]


def grey_mask(matrix: dict = MATRIX) -> np.ndarray:
    """True where a cell is 'not enough data' (label starts with GREY_PREFIX)."""
    return np.array([[matrix[r][m][1].strip().startswith(GREY_PREFIX) for m in MKTS] for r in matrix])


def matrix_frame(matrix: dict = MATRIX) -> pd.DataFrame:
    """Label table with a `strategy` column plus one column per market (the CSV layout)."""
    return pd.DataFrame([{"strategy": r, **{m: matrix[r][m][1] for m in MKTS}} for r in matrix])


def fat_pitches(matrix: dict = MATRIX) -> list[str]:
    """'<market>: <strategy> (<label>)' for every cell scored SCORE_STRONG, row-major."""
    return [f"{m}: {r.split('(')[0].strip()} ({matrix[r][m][1]})"
            for r in matrix for m in MKTS if matrix[r][m][0] == SCORE_STRONG]


# ─────────────────────────── rendering / I/O ───────────────────────────
def render_heatmap(matrix: dict = MATRIX) -> matplotlib.figure.Figure:
    """Ted-Williams-style heatmap figure (green = swing, red = take, grey = no call)."""
    rows = list(matrix)
    labels = label_grid(matrix)
    disp = np.where(grey_mask(matrix), np.nan, score_grid(matrix))
    fig, ax = plt.subplots(figsize=(11, 6.5))
    cmap = plt.cm.RdYlGn.with_extremes(bad=GREY)
    ax.imshow(disp, cmap=cmap, vmin=SCORE_MIN, vmax=SCORE_MAX, aspect="auto")
    ax.set_xticks(range(len(MKTS)))
    ax.set_xticklabels(MKTS, fontsize=13, fontweight="bold")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontsize=9)
    ax.set_xlabel("market", fontsize=11)
    ax.xaxis.set_label_position("top")
    ax.xaxis.tick_top()
    for i in range(len(rows)):
        for j in range(len(MKTS)):
            ax.text(j, i, labels[i][j], ha="center", va="center", fontsize=7.5,
                    color="black", wrap=True)
    ax.set_title("Where's the edge? Filter × Market  —  swing only at the fat pitch\n"
                 "(Ted Williams / Buffett: green = your .400 zone, red = the .230 corner, grey = not enough data)",
                 fontsize=11, pad=30)
    ax.set_xticks(np.arange(-.5, len(MKTS), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(rows), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    fig.tight_layout()
    return fig


def write_outputs(out_dir: Path = REPORTS_DIR, matrix: dict = MATRIX) -> tuple[Path, Path]:
    """Write edge_matrix.csv and edge_matrix.png into `out_dir`; return their paths."""
    csv_path, png_path = out_dir / "edge_matrix.csv", out_dir / "edge_matrix.png"
    matrix_frame(matrix).to_csv(csv_path, index=False)
    fig = render_heatmap(matrix)
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return csv_path, png_path


def main() -> int:
    _, png_path = write_outputs()
    print(f"wrote {png_path} + reports/edge_matrix.csv")
    print("\nFAT PITCHES (swing — score +2):")
    for line in fat_pitches():
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
