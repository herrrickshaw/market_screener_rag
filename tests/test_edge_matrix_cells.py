"""Extra edge_matrix checks: grey masking of '—' cells and the printed fat-pitch list."""
import pandas as pd

import edge_matrix as E


def test_main_prints_every_score_two_cell_and_no_others(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(E, "HERE", tmp_path)
    assert E.main() == 0
    out = capsys.readouterr().out
    lines = [ln for ln in out.splitlines() if ln.startswith("  ")]
    expected = sum(1 for cells in E.MATRIX.values() for s, _ in cells.values() if s == 2)
    assert len(lines) == expected > 0
    assert "  IN: Momentum / Trend " in out and "(trend DSR.99)" in out
    assert "  JP: Value-reversion" in out and "JP: Momentum" not in out   # JP momentum scores -1
    assert out.splitlines()[0].startswith("wrote ") and out.splitlines()[0].endswith("reports/edge_matrix.csv")
    assert "FAT PITCHES (swing — score +2):" in out


def test_csv_round_trips_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(E, "HERE", tmp_path)
    E.main()
    df = pd.read_csv(tmp_path / "reports" / "edge_matrix.csv")
    first = next(iter(E.MATRIX))
    assert df.loc[0, "strategy"] == first
    for m in E.MKTS:
        assert df.loc[0, m] == E.MATRIX[first][m][1]


def test_scores_are_integers_and_dash_cells_are_neutral():
    for row, cells in E.MATRIX.items():
        for m, (score, label) in cells.items():
            assert isinstance(score, int), (row, m)
            if label.strip().startswith("—"):
                assert score in (0, 1), (row, m)   # grey cells never claim a negative or strong edge
