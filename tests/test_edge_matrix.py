"""Tests for edge_matrix (writes into a temporary tree)."""
import pandas as pd

import edge_matrix as E


def test_matrix_is_complete_and_scored_in_range():
    for row, cells in E.MATRIX.items():
        assert list(cells) == E.MKTS, row
        for m, (score, label) in cells.items():
            assert -2 <= score <= 2 and label


def test_main_runs_on_a_fresh_checkout(tmp_path, monkeypatch):
    # reports/ is not tracked in the repo, so a fresh clone has no such directory
    monkeypatch.setattr(E, "HERE", tmp_path)
    assert E.main() == 0
    df = pd.read_csv(tmp_path / "reports" / "edge_matrix.csv")
    assert list(df.columns) == ["strategy"] + E.MKTS and len(df) == len(E.MATRIX)
    assert (tmp_path / "reports" / "edge_matrix.png").exists()
