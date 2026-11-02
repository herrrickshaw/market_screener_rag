"""Unit + smoke tests for screener_rag.py (pure functions, KB-backed text, CLI dispatch)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

import screener_rag as sr

ROOT = Path(__file__).resolve().parent.parent


# ─────────────────────────── market normalisation ───────────────────────────
@pytest.mark.parametrize("text, expected", [
    ("KR", "KR"), ("kr", "KR"), ("india", "IN"), ("why long-only in india", "IN"),
    ("Korea long/short", "KR"), ("JAPAN", "JP"), ("europe", "EU"), ("china", "CN"),
    ("hello world", None), ("", None),
    # characterisation: matching is by substring, so "nothing" is read as "IN"
    ("nothing here", "IN"),
])
def test_normalise_market(text, expected):
    assert sr.normalise_market(text) == expected
    assert sr._mk(text) == expected  # backwards-compatible alias


def test_market_code_column_accepts_names_and_codes():
    d = pd.DataFrame({"market": ["india", "KR", "Us", "unknown"]})
    assert sr._market_code_column(d).tolist() == ["IN", "KR", "US", "UNKNOWN"]


# ─────────────────────────── pure screen selectors ───────────────────────────
@pytest.fixture
def clusters() -> pd.DataFrame:
    return pd.DataFrame({
        "name": ["cheapQ", "cheapNoQ", "fair", "richHollow", "richQ"],
        "pe": [5, 6, 15, 60, 50],
        "pb": [0.5, 0.6, 2, 8, 7],
        "roe": [0.20, 0.05, 0.12, 0.01, 0.30],
        "valuation_z": [-1.5, -1.2, 0.0, 1.5, 1.2],
        "verdict": ["UNDERPRICED", "UNDERPRICED", "fair", "OVERPRICED", "OVERPRICED"],
    })


def test_select_picks_india_is_long_only_with_quality_gate(clusters):
    picks, notes = sr.select_picks(clusters, "IN")
    assert len(picks) == 1
    heading, frame = picks[0]
    assert frame.name.tolist() == ["cheapQ"]
    assert "LONG" in heading and "1 names" in heading
    assert notes and "No short book" in notes[0]


def test_select_picks_korea_has_long_and_short_legs(clusters):
    picks, notes = sr.select_picks(clusters, "KR")
    assert [h.split(" ")[0] for h, _ in picks] == ["**LONG", "**SHORT"]
    assert picks[0][1].name.tolist() == ["cheapQ"]        # roe 0.05 fails KR_MIN_ROE
    assert picks[1][1].name.tolist() == ["richHollow"]    # richQ fails KR_MAX_ROE
    assert notes == []


def test_select_picks_us_has_no_quality_gate_and_respects_n(clusters):
    picks, _ = sr.select_picks(clusters, "US", n=1)
    assert picks[0][1].name.tolist() == ["cheapQ"]
    picks, _ = sr.select_picks(clusters, "US", n=5)
    assert picks[0][1].name.tolist() == ["cheapQ", "cheapNoQ"]


def test_select_picks_default_sorts_cheapest_first(clusters):
    picks, _ = sr.select_picks(clusters, "EU", n=2)
    assert picks[0][1].name.tolist() == ["cheapQ", "cheapNoQ"]


# ─────────────────────────── KB-backed text ───────────────────────────
def test_strategy_text_for_every_market_in_kb():
    for mk in sr.KB["markets"]:
        text = sr.strategy(mk)
        assert text.startswith(f"# {sr.NAMES[mk]} — winning strategy")
        assert "not investment advice" in text.lower()


def test_strategy_unknown_market():
    assert sr.strategy("XX").startswith("Unknown market XX")


def test_earnings_table_has_one_row_per_market():
    text = sr.earnings()
    rows = [line for line in text.splitlines() if line.startswith("| ") and "|---" not in line]
    assert len(rows) == 1 + len(sr.EARNINGS_ROWS)  # header + markets
    for mk in sr.EARNINGS_ROWS:
        assert f"| {sr.NAMES[mk]} |" in text


def test_universal_mentions_kb_finding():
    assert sr.KB["_meta"]["universal_finding"] in sr.universal()


def test_playbook_all_and_single():
    full = sr.playbook()
    assert all(f"## {sr.NAMES[m]}" in full for m in sr.MARKET_ORDER)
    assert "## Rules everywhere" in full
    single = sr.playbook("korea")
    assert "## Korea" in single and "## India" not in single and "Rules everywhere" not in single


def test_build_corpus_shape():
    docs = sr.build_corpus()
    assert [d["src"] for d in docs][-2:] == ["universal", "earnings"]
    assert len(docs) == len(sr.KB["markets"]) + 2


def test_ask_returns_best_match_header():
    assert sr.ask("why long-only in india").startswith("*(best match: ")


# ─────────────────────────── screen() against bundled data ───────────────────────────
def test_screen_bundled_markets():
    assert sr.screen("IN").startswith("# India — live picks")
    assert "**SHORT expensive∩lo-ROE" in sr.screen("KR")
    assert sr.screen("EU").startswith("Europe: no bundled fundamentals")
    assert sr.screen("XX") == "Unknown market XX."


def test_screen_with_injected_clusters(tmp_path, clusters):
    path = tmp_path / "clusters.csv"
    clusters.assign(market="india").to_csv(path, index=False)
    text = sr.screen("IN", clusters_path=path)
    assert "cheapQ" in text and "richHollow" not in text


# ─────────────────────────── CLI ───────────────────────────
def test_dispatch_routes_commands():
    assert sr.dispatch([]).lstrip().startswith("screener_rag.py")
    assert sr.dispatch(["strategy", "korea"]) == sr.strategy("KR")
    assert sr.dispatch(["earnings"]) == sr.earnings()
    assert sr.dispatch(["universal"]) == sr.universal()
    assert sr.dispatch(["playbook", "IN"]) == sr.playbook("IN")


def test_cli_smoke():
    out = subprocess.run([sys.executable, str(ROOT / "screener_rag.py"), "strategy", "KR"],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    assert out.stdout.startswith("# Korea — winning strategy")
