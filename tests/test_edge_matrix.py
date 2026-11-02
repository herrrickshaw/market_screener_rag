"""Unit + smoke tests for edge_matrix.py (pure grid builders, CSV parity, rendering)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import edge_matrix as em

ROOT = Path(__file__).resolve().parent.parent

TINY = {
    "Strat A (x)": {"IN": (2, "+1%"), "US": (0, "— thin"), "KR": (-1, "fails"),
                    "JP": (0, "—"), "EU": (2, "+2%"), "CN": (0, "— untested")},
    "Strat B": {"IN": (1, "+0.5%"), "US": (2, "+3%"), "KR": (0, "—"),
                "JP": (0, "—"), "EU": (0, "—"), "CN": (0, "—")},
}


def test_grids_have_strategy_by_market_shape():
    assert em.score_grid(TINY).shape == (2, len(em.MKTS))
    assert em.score_grid(TINY)[0].tolist() == [2, 0, -1, 0, 2, 0]
    assert em.label_grid(TINY)[1][1] == "+3%"
    assert em.grey_mask(TINY)[0].tolist() == [False, True, False, True, False, True]


def test_fat_pitches_row_major_strong_only():
    assert em.fat_pitches(TINY) == ["IN: Strat A (+1%)", "EU: Strat A (+2%)", "US: Strat B (+3%)"]


def test_matrix_frame_layout():
    df = em.matrix_frame(TINY)
    assert df.columns.tolist() == ["strategy", *em.MKTS]
    assert df.strategy.tolist() == list(TINY)


def test_committed_csv_matches_matrix():
    """The committed edge_matrix.csv is exactly what MATRIX renders (no drift)."""
    committed = pd.read_csv(ROOT / "edge_matrix.csv")
    pd.testing.assert_frame_equal(committed, em.matrix_frame())


def test_write_outputs_smoke(tmp_path):
    csv_path, png_path = em.write_outputs(tmp_path, TINY)
    assert csv_path.exists() and png_path.stat().st_size > 0
    assert pd.read_csv(csv_path).shape == (2, 1 + len(em.MKTS))
