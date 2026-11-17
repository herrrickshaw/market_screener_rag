"""Tests for screener_rag (bundled snapshot data only, no network)."""
import re

import pandas as pd
import pytest

import screener_rag as R


@pytest.mark.parametrize("s,code", [("IN", "IN"), ("india", "IN"), ("KR", "KR"), ("korea", "KR"),
                                    ("us", "US"), ("Japan", "JP"), ("eu", "EU"), ("CN", "CN"),
                                    ("why long-only in india", "IN")])
def test_market_parser(s, code):
    assert R._mk(s) == code


@pytest.mark.parametrize("s", ["singapore", "russia", "argentina", "spain"])
def test_market_parser_does_not_match_inside_words(s):
    # "singapore"/"spain" contain "in", "russia" contains "us": they are not India / US
    assert R._mk(s) is None


def test_strategy_known_and_unknown():
    txt = R.strategy("KR")
    assert "FULL LONG-SHORT" in txt and "+4.83% / 6M" in txt
    assert R.strategy("XX").startswith("Unknown market")


def test_earnings_table_matches_knowledge_base():
    # earnings() hardcodes its table; every headline number must also be in the KB it summarises
    kb = R.KB["markets"]
    pairs = {"IN": ["5.3%", "2.34"], "US": ["1.72%", "2.32"], "KR": ["4.83%", "4.17"],
             "EU": ["1.39", "0.985"], "JP": ["6.6", "4.84"], "CN": ["0.04"]}
    table = R.earnings()
    for mk, nums in pairs.items():
        blob = " ".join(kb[mk]["backtest_earnings"].values())
        for n in nums:
            assert n in table and n in blob, (mk, n)


def test_screen_india_applies_long_only_rule():
    out = R.screen("IN", n=5)
    cl = R._clusters("IN")
    expect = cl[(cl.valuation_z < -0.8) & (cl.roe > 0.15)].sort_values("valuation_z").head(5)
    for name in expect["name"]:
        assert str(name) in out
    assert "No short book" in out and "SHORT" not in out.split("No short book")[0]


def test_screen_korea_has_both_books():
    out = R.screen("KR", n=3)
    assert "LONG cheap∩hi-ROE (3)" in out and "SHORT expensive∩lo-ROE" in out


def test_screen_markets_without_data_or_strategy():
    assert "no bundled fundamentals" in R.screen("EU")
    # CN: KB lists value-reversion as TESTED-and-FAILS; with no bundled CN data no picks are printed
    assert "Screen (" not in R.screen("CN")
    assert R.screen("XX").startswith("Unknown market")


def test_playbook_all_and_one():
    allp = R.playbook()
    for name in R.NAMES.values():
        assert f"## {name}" in allp
    one = R.playbook("korea")
    assert "## Korea" in one and "## India" not in one


def test_playbook_unknown_market_does_not_crash():
    out = R.playbook("UK")
    assert "Unknown market" in out


def test_ask_retrieves_relevant_doc():
    assert "(best match: Korea)" in R.ask("korea long short hollow overpriced")
    assert "(best match: earnings)" in R.ask("historical earnings significance table")
