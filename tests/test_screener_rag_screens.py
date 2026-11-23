"""Offline tests for screener_rag screen branches, data loaders and the CLI (synthetic CSVs in tmp_path)."""
import pandas as pd
import pytest

import screener_rag as R


@pytest.fixture()
def datadir(tmp_path, monkeypatch):
    """Point the module at a tmp tree holding small synthetic ratio/cluster files."""
    (tmp_path / "data").mkdir()
    monkeypatch.setattr(R, "HERE", tmp_path)
    return tmp_path / "data"


def _write(datadir, name, rows):
    pd.DataFrame(rows).to_csv(datadir / name, index=False)


def _cl(market, name, z, roe):
    return {"market": market, "name": name, "pe": 10.0, "pb": 1.0, "roe": roe, "valuation_z": z, "verdict": "x"}


def test_ratios_normalises_market_names_and_filters(datadir):
    _write(datadir, "all_ratios.csv", [
        {"market": "india", "name": "a"}, {"market": "IN", "name": "b"},
        {"market": "Korea", "name": "c"}, {"market": "KR", "name": "d"}, {"market": "ZZ", "name": "e"}])
    assert sorted(R._ratios("IN")["name"]) == ["a", "b"]
    assert sorted(R._ratios("KR")["name"]) == ["c", "d"]
    assert list(R._ratios("ZZ")["name"]) == ["e"]       # unknown labels are upper-cased, kept as-is
    assert R._ratios("US").empty


def test_clusters_normalises_market_names_and_filters(datadir):
    _write(datadir, "valuation_clusters.csv", [_cl("japan", "j1", 0, 0), _cl("JP", "j2", 0, 0), _cl("us", "u", 0, 0)])
    assert sorted(R._clusters("JP")["name"]) == ["j1", "j2"]
    assert list(R._clusters("US")["name"]) == ["u"]
    assert R._clusters("IN").empty


def test_screen_india_thresholds_are_strict(datadir):
    _write(datadir, "valuation_clusters.csv", [
        _cl("IN", "pass", -0.9, 0.20),
        _cl("IN", "z_edge", -0.8, 0.20),      # valuation_z must be strictly < -0.8
        _cl("IN", "roe_edge", -0.9, 0.15),    # roe must be strictly > 0.15
        _cl("IN", "pricey", 0.5, 0.30)])
    out = R.screen("IN")
    assert "cheap-for-quality, 1 names)" in out and "pass" in out
    for n in ("z_edge", "roe_edge", "pricey"):
        assert n not in out


def test_screen_india_orders_cheapest_first_and_honours_n(datadir):
    _write(datadir, "valuation_clusters.csv", [_cl("IN", f"s{i}", -1.0 - i, 0.3) for i in range(4)])
    out = R.screen("IN", n=2)
    assert "cheap-for-quality, 2 names)" in out
    assert out.index("s3") < out.index("s2")   # most negative z first
    assert "s0" not in out and "s1" not in out


def test_screen_korea_both_books_with_thresholds(datadir):
    _write(datadir, "valuation_clusters.csv", [
        _cl("KR", "L1", -0.9, 0.11), _cl("KR", "Lroe_edge", -0.9, 0.10), _cl("KR", "Lz_edge", -0.8, 0.5),
        _cl("KR", "S1", 1.5, 0.01), _cl("KR", "S2", 2.5, 0.04), _cl("KR", "Sz_edge", 1.0, 0.0),
        _cl("KR", "Sroe_edge", 2.0, 0.05)])
    out = R.screen("KR")
    longs, shorts = out.split("**SHORT")
    assert "LONG cheap∩hi-ROE (1)" in longs and "L1" in longs
    assert "Lroe_edge" not in out and "Lz_edge" not in out
    assert "(2):**" in shorts
    assert shorts.index("S2") < shorts.index("S1")        # most expensive first
    assert "Sz_edge" not in out and "Sroe_edge" not in out


def test_screen_us_cheap_vs_market_only(datadir):
    _write(datadir, "valuation_clusters.csv", [
        _cl("US", "cheap", -1.0, -0.5), _cl("US", "edge", -0.8, 0.9), _cl("US", "rich", 2.0, 0.9)])
    out = R.screen("US")
    assert "LONG cheap-vs-market (1, hold ≤3M)" in out and "cheap" in out
    assert "edge" not in out and "rich" not in out and "SHORT" not in out


def test_screen_other_market_sorted_ascending_and_limited(datadir):
    _write(datadir, "valuation_clusters.csv", [_cl("JP", f"j{i}", float(i), 0.1) for i in range(5)])
    out = R.screen("JP", n=3)
    assert "**Screen (3):**" in out
    assert "j0" in out and "j2" in out and "j3" not in out
    assert out.rstrip().endswith("Not investment advice.")


def test_screen_skips_missing_columns(datadir):
    _write(datadir, "valuation_clusters.csv", [{"market": "US", "name": "x", "valuation_z": -2.0}])
    out = R.screen("US")
    assert "| name" in out and "pe" not in out.split("|---")[0]


def test_screen_includes_strategy_header(datadir):
    _write(datadir, "valuation_clusters.csv", [_cl("KR", "L1", -0.9, 0.11)])
    out = R.screen("KR")
    m = R.KB["markets"]["KR"]
    assert out.startswith("# Korea — live picks from the winning screen")
    assert f"Strategy: **{m['character']}**, {m['book']}. {m['verdict']}" in out


def test_screen_market_with_no_bundled_rows_reports_it(datadir):
    _write(datadir, "valuation_clusters.csv", [_cl("IN", "x", -1.0, 0.3)])
    assert R.screen("CN") == "China: no bundled fundamentals to screen (likely underpowered/pending)."


def test_screen_empty_winning_metrics_short_circuits_before_data(datadir, monkeypatch):
    # no CSV exists in the tmp tree: the early return must come before any file access
    monkeypatch.setitem(R.KB["markets"], "CN", {**R.KB["markets"]["CN"], "winning_metrics": []})
    out = R.screen("CN")
    assert out == f"China: no validated strategy ({R.KB['markets']['CN']['verdict']}). No screen run."


def test_universal_mentions_survivors_and_disclaimer():
    out = R.universal()
    assert out.startswith("# The metric that works in (nearly) every market")
    assert R.KB["_meta"]["universal_finding"] in out
    assert "IN trend (0.994)" in out and out.rstrip().endswith("Not investment advice.")


def test_earnings_ignores_argument_and_has_six_rows():
    assert R.earnings("whatever") == R.earnings()
    rows = [ln for ln in R.earnings().splitlines() if ln.startswith("| ") and "---" not in ln]
    assert len(rows) == 7        # header + six markets


def test_playbook_lowercase_code_and_rules_only_for_full_book():
    one = R.playbook("kr")
    assert "## Korea" in one and "Rules everywhere" not in one
    assert "Rules everywhere" in R.playbook()
    assert "Rules everywhere" in R.playbook("")


def test_playbook_unknown_lists_valid_markets():
    out = R.playbook("zz")
    assert out.startswith("Unknown market zz. One of ['IN', 'US', 'KR', 'JP', 'EU', 'CN']")


def test_strategy_uses_none_validated_placeholder():
    assert "(none validated)" not in R.strategy("IN")
    assert "**Winning metrics:** (value-reversion TESTED and FAILS)" in R.strategy("CN")


def test_ask_picks_best_document():
    assert "(best match: India)" in R.ask("india long only trend breakout golden cross")


@pytest.fixture()
def cli(monkeypatch, capsys, datadir):
    _write(datadir, "valuation_clusters.csv", [_cl("IN", "indname", -1.0, 0.3)])

    def run(*argv):
        monkeypatch.setattr(R.sys, "argv", ["screener_rag.py", *argv])
        rc = R.main()
        return rc, capsys.readouterr().out
    return run


def test_main_without_args_prints_usage(cli):
    rc, out = cli()
    assert rc == 0 and "Usage:" in out and "screener_rag.py strategy KR" in out


@pytest.mark.parametrize("argv,needle", [
    (("strategy", "korea"), "Korea — winning strategy"),
    (("strategy", "KR"), "Korea — winning strategy"),
    (("STRATEGY", "ZZ"), "Unknown market ZZ"),
    (("screen", "india"), "indname"),
    (("screen", "ZZ"), "Unknown market ZZ."),
    (("earnings",), "Historical earnings of the winning strategies"),
    (("universal",), "The metric that works"),
    (("playbook", "japan"), "## Japan"),
    (("playbook",), "Rules everywhere"),
    (("ask", "why", "long-only", "in", "india"), "best match"),
    (("korea", "long", "short", "hollow", "overpriced"), "(best match: Korea)"),
])
def test_main_dispatch(cli, argv, needle):
    rc, out = cli(*argv)
    assert rc == 0 and needle in out
