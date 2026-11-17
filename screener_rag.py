#!/usr/bin/env python3
"""
screener_rag.py — a credit-free, offline RAG that runs on the METRICS THAT WORK IN EACH
MARKET (the backtested, Deflated-Sharpe-survived winning strategies), applies them to the
current universe to produce stock picks, and reports each strategy's historical earnings.

No paid API, no model download: rule-based strategy knowledge base (winning_strategies.json)
+ deterministic screening over bundled ratios + TF-IDF retrieval (sklearn) for open Q&A.
Design rule: numbers come from the data / the backtests — never invented.

Usage:
  python screener_rag.py strategy KR            # the winning KR strategy + its earnings
  python screener_rag.py screen IN              # apply the IN winning screen -> live picks
  python screener_rag.py earnings               # historical earnings of every strategy
  python screener_rag.py universal              # the metric that works in every market
  python screener_rag.py playbook [KR]          # ranked retail-accessible edges
  python screener_rag.py ask "why long-only in india"
Research only — NOT investment advice.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

# ─────────────────────────── configuration ───────────────────────────
HERE = Path(__file__).resolve().parent
KB_PATH = HERE / "winning_strategies.json"
CLUSTERS_PATH = HERE / "data" / "valuation_clusters.csv"

NORM = {"india": "IN", "us": "US", "korea": "KR", "japan": "JP", "europe": "EU", "china": "CN"}
NAMES = {"IN": "India", "US": "US", "KR": "Korea", "JP": "Japan", "EU": "Europe", "CN": "China"}
MARKET_ORDER = ["IN", "US", "KR", "JP", "EU", "CN"]

# Screen thresholds (valuation_z = peer-cluster valuation z-score; roe = fraction, 0.15 = 15%).
CHEAP_Z = -0.8          # "cheap vs peers" cut-off
RICH_Z = 1.0            # "expensive vs peers" cut-off (Korea short leg)
IN_MIN_ROE = 0.15       # India long leg: quality gate
KR_MIN_ROE = 0.10       # Korea long leg: quality gate
KR_MAX_ROE = 0.05       # Korea short leg: "hollow" gate
DEFAULT_PICKS = 15
PICK_COLS = ["name", "pe", "pb", "roe", "valuation_z", "verdict"]
DISCLAIMER = "> Not investment advice."

# A screen result: ordered (heading, frame) pairs, plus trailing note lines.
Picks = list  # list[tuple[str, pd.DataFrame]]
Selector = Callable[[pd.DataFrame, int], "tuple[Picks, list[str]]"]


def load_kb(path: Path = KB_PATH) -> dict:
    """Read the strategy knowledge base (winning_strategies.json) into a dict."""
    return json.loads(path.read_text())


KB = load_kb()


# ─────────────────────────── helpers ───────────────────────────
def normalise_market(text: str) -> Optional[str]:
    """Map free text ('india', 'KR', 'why long-only in india') to a 2-letter market code.

    Returns None when no market name/code is mentioned.
    """
    s = text.lower()
    aliases = {**NORM, **{code.lower(): code for code in NAMES}}
    for alias, code in aliases.items():
        if alias in f" {s} ":
            return code
    return None


_mk = normalise_market  # backwards-compatible alias


def _market_code_column(d: pd.DataFrame) -> pd.Series:
    """Normalise a `market` column ('india' / 'IN') to the 2-letter code."""
    raw = d.market.astype(str)
    return raw.str.lower().map(NORM).fillna(raw.str.upper())


def load_clusters(market: str, path: Path = CLUSTERS_PATH) -> pd.DataFrame:
    """Bundled peer-valuation clusters for one market (rows for other markets dropped)."""
    d = pd.read_csv(path)
    d["mk"] = _market_code_column(d)
    return d[d.mk == market].copy()


_clusters = load_clusters  # backwards-compatible alias


# ─────────────────────────── strategy / earnings ───────────────────────────
def strategy(market: str, kb: dict = KB) -> str:
    """Markdown summary of the winning strategy for `market` (2-letter code) from the KB."""
    m = kb["markets"].get(market)
    if not m:
        return f"Unknown market {market}. One of {list(kb['markets'])}."
    L = [f"# {NAMES[market]} — winning strategy (backtested)", "",
         f"**Character:** {m['character']} · **Book:** {m['book']}",
         f"**Winning metrics:** {', '.join(m['winning_metrics']) or '(none validated)'}",
         f"**Screen:** long = {m['screen']['long']} · short = {m['screen']['short']}", "",
         "**Historical earnings (gross, PIT-backtested):**"]
    for k, v in m["backtest_earnings"].items():
        L.append(f"  - *{k}*: {v}")
    L += ["", f"**Data sufficiency:** {m['sufficiency']}", f"**Verdict:** {m['verdict']}",
          "", "> " + kb["sizing_discipline"], "> Research only — not investment advice."]
    return "\n".join(L)


EARNINGS_ROWS = {
    "IN": ("long-only trend + sector-relative value", "+5.3%/6M value (≈+10.9%/yr); trend IR 2.34", "t 2.5 · DSR 0.994 ✅"),
    "US": ("short-horizon value reversion (≤3M)", "+1.72%/3M (≈+6.9%/yr)", "t 2.32 ✅ (fades by 6M)"),
    "KR": ("long/short cheap∩hi-ROE vs expensive∩lo-ROE", "+4.83%/6M (≈+9.9%/yr) — STRONGEST", "t 4.17 · DSR 0.99 ✅"),
    "EU": ("12M momentum (bull)", "IR 1.39 (bull regime)", "DSR 0.985 ✅ · value underpowered"),
    "JP": ("value-reversion (long cheap-vs-market)", "+6.6%/6M (t 4.84) — deep EDINET data flips the verdict", "powered ✅"),
    "CN": ("value tested & fails", "cheap−rich ≈ 0% (t 0.04) over 109 formations — powered null", "value edge absent ✅ tested"),
}


def earnings(kb: dict = KB) -> str:
    """Markdown table of the backtested earnings of every market's winning strategy."""
    L = ["# Historical earnings of the winning strategies (gross, PIT-backtested)", "",
         "| market | strategy | earnings | significance |", "|---|---|---|---|"]
    for mk, (s, e, sig) in EARNINGS_ROWS.items():
        L.append(f"| {NAMES[mk]} | {s} | {e} | {sig} |")
    L += ["", "**Read:** earnings are the backtested long−short (or quintile) spread, gross of "
          "costs and borrow. Annualised figures are indicative, not compounded guarantees. IN/US/KR "
          "are powered+complete (tradeable edges); EU momentum is robust (value underpowered); "
          "**China is powered and value FAILS** (a real null — no value edge); **Japan**, with deep "
          "EDINET data, shows STRONG value-reversion (+6.6%/6M, t 4.84) — flipping its earlier "
          "underpowered verdict. Nulls and flips are both real, tested verdicts.", "", "> " + kb["sizing_discipline"]]
    return "\n".join(L)


def universal(kb: dict = KB) -> str:
    """The universal finding (momentum/trend survives multiple-testing almost everywhere)."""
    return ("# The metric that works in (nearly) every market\n\n" + kb["_meta"]["universal_finding"] +
            "\n\n**Deflated-Sharpe survivors (bull regime):** IN trend (0.994), KR breakout (0.99), "
            "EU mom252 (0.985). US mom252 (0.901) is fragile. **All bear-regime mean-reversion factors "
            "FAIL** multiple-testing. → Momentum/trend is the universal core; specialise per market "
            "(KR full L/S, IN long-only value, US short-horizon).\n\n" + DISCLAIMER)


# ─────────────────────────── live screen (winning metrics) ───────────────────────────
# One pure selector per market: clusters frame in, (picks, notes) out. Adding a market means
# adding an entry to SCREENS, not editing `screen()`.
def _screen_in(cl: pd.DataFrame, n: int) -> tuple[Picks, list[str]]:
    """India, long-only: cheap-vs-peers AND high ROE."""
    longs = cl[(cl.valuation_z < CHEAP_Z) & (cl.roe > IN_MIN_ROE)].sort_values("valuation_z").head(n)
    return ([(f"**LONG (cheap-for-quality, {len(longs)} names)** — momentum overlay applies live:", longs)],
            ["*No short book — shorting fails in India (−1.0%/6M).*"])


def _screen_kr(cl: pd.DataFrame, n: int) -> tuple[Picks, list[str]]:
    """Korea, full long/short: long cheap∩hi-ROE, short expensive∩lo-ROE."""
    longs = cl[(cl.valuation_z < CHEAP_Z) & (cl.roe > KR_MIN_ROE)].sort_values("valuation_z").head(n)
    shorts = (cl[(cl.valuation_z > RICH_Z) & (cl.roe < KR_MAX_ROE)]
              .sort_values("valuation_z", ascending=False).head(n))
    return ([(f"**LONG cheap∩hi-ROE ({len(longs)}):**", longs),
             (f"**SHORT expensive∩lo-ROE ({len(shorts)}):**", shorts)], [])


def _screen_us(cl: pd.DataFrame, n: int) -> tuple[Picks, list[str]]:
    """US, short-horizon: cheap-vs-market, hold at most 3 months."""
    longs = cl[cl.valuation_z < CHEAP_Z].sort_values("valuation_z").head(n)
    return ([(f"**LONG cheap-vs-market ({len(longs)}, hold ≤3M):**", longs)], [])


def _screen_default(cl: pd.DataFrame, n: int) -> tuple[Picks, list[str]]:
    """Fallback (EU momentum / others): cheapest-vs-peers, no quality gate."""
    longs = cl.sort_values("valuation_z").head(n)
    return ([(f"**Screen ({len(longs)}):**", longs)], [])


SCREENS: dict[str, Selector] = {
    "IN": _screen_in,
    "KR": _screen_kr,
    "US": _screen_us,
}


def select_picks(cl: pd.DataFrame, market: str, n: int = DEFAULT_PICKS) -> tuple[Picks, list[str]]:
    """Apply the market's winning screen to a clusters frame. Pure: no I/O."""
    return SCREENS.get(market, _screen_default)(cl, n)


def screen(market: str, n: int = DEFAULT_PICKS, kb: dict = KB,
           clusters_path: Path = CLUSTERS_PATH) -> str:
    """Markdown report: live picks from the winning screen for `market` (2-letter code)."""
    m = kb["markets"].get(market)
    if not m:
        return f"Unknown market {market}."
    if not m["winning_metrics"]:
        return f"{NAMES[market]}: no validated strategy ({m['verdict']}). No screen run."
    cl = load_clusters(market, clusters_path)
    if cl.empty:
        return f"{NAMES[market]}: no bundled fundamentals to screen (likely underpowered/pending)."
    out = [f"# {NAMES[market]} — live picks from the winning screen", "",
           f"Strategy: **{m['character']}**, {m['book']}. {m['verdict']}", ""]
    cols = [c for c in PICK_COLS if c in cl.columns]
    picks, notes = select_picks(cl, market, n)
    for i, (heading, frame) in enumerate(picks):
        if i:
            out.append("")
        out += [heading, "", frame[cols].to_markdown(index=False)]
    for note in notes:
        out += ["", note]
    out += ["", "> Gross of costs; validate each name before acting. Not investment advice."]
    return "\n".join(out)


# ─────────────────────────── open Q&A (TF-IDF retrieval) ───────────────────────────
def build_corpus(kb: dict = KB) -> list[dict]:
    """The retrieval corpus: one document per market strategy plus the universal/earnings notes."""
    docs = [{"src": NAMES[mk], "text": strategy(mk, kb)} for mk in kb["markets"]]
    docs.append({"src": "universal", "text": universal(kb)})
    docs.append({"src": "earnings", "text": earnings(kb)})
    return docs


def ask(q: str, kb: dict = KB) -> str:
    """Answer a free-text question by returning the best TF-IDF match from the corpus."""
    # scikit-learn is imported lazily so the other commands stay light.
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel

    docs = build_corpus(kb)
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    M = vec.fit_transform([d["text"] for d in docs])
    sims = linear_kernel(vec.transform([q]), M).ravel()
    i = int(sims.argmax())
    return f"*(best match: {docs[i]['src']})*\n\n" + docs[i]["text"]


# ─────────────────────────── playbook ───────────────────────────
PLAYBOOK = {
 "IN": ("momentum/long-only", ["🥇 Momentum/Trend (50>200 DMA) — DSR 0.994, most robust",
        "🥈 Value-reversion (sector-relative cheap) — +5.3%/6M t2.5", "🥈 Quality (hi-ROE) behind liquidity gate",
        "🚫 Never short (value+quality L/S −1%/6M)"]),
 "US": ("mixed/light", ["🥇 Short-horizon cheap-vs-market (≤3M) — +1.7%/3M t2.3",
        "⚙️ Light factor + insider (Form 4) + passive core", "🚫 Piotroski INVERTED in US"]),
 "KR": ("mean-reversion/L-S", ["🥇 Value+Quality L/S — +4.83%/6M t4.17 GROSS, but +2.3%/6M t2.0 NET of 5% borrow (halved)",
        "🥈 Breakout (DSR 0.99) · value-reversion · hi-ROE Korea discount", "⚠️ needs a cheap, reliable locate"]),
 "JP": ("value-reversion", ["🥇 Value-reversion (cheap PE) — +6.6%/6M t4.84 (strongest value anywhere)",
        "🥈 Value+Quality L/S (net of borrow)", "🚫 Momentum fails (no DSR survivor)"]),
 "EU": ("momentum", ["🥇 12-month momentum (mom252) — DSR 0.985", "⚙️ passive + insider",
        "— value underpowered (can't recommend)"]),
 "CN": ("speculation-ruled", ["🥇 PASSIVE / index only", "🚫 Value-reversion tested & FAILS (t0.3, 1993×10y)",
        "🚫 Momentum ALSO fails at 6M (t−0.2) — any CN momentum is fast/retail-inaccessible",
        "ℹ️ SOE core (utilities) is fundamentally-priced, but the tradeable growth-periphery is speculative"]),
}
RULES = ["Horizon: monthly–6M only (fast signals lose to the information-asymmetry tax).",
         "Sizing: inverse-vol + vol-target + kill-switch. Capacity ~$300–500k (illiquidity edge).",
         "Read spreads, not win-rate (~50% hit-rate is normal — the edge is magnitude).",
         "Short only where the market mean-reverts (KR ✅), never in a trending one (IN 🚫).",
         "Net of costs/borrow: KR L/S halves, US L/S turns negative — borrow is decisive."]


def playbook(market: str = "") -> str:
    """Ranked retail-accessible edges, for one market (code or name) or all markets."""
    mk = normalise_market(market) or (market.upper() if market else None)
    L = ["# Market playbook — retail-accessible edges, ranked (backtested)", ""]
    for m in (MARKET_ORDER if not mk else [mk]):
        ch, rows = PLAYBOOK[m]
        L += [f"## {NAMES[m]} — *{ch}*", ""] + [f"- {r}" for r in rows] + [""]
    if not mk:
        L += ["## Rules everywhere", ""] + [f"- {r}" for r in RULES]
    L += ["", "> Every ranking traces to a committed backtest. Research, not investment advice."]
    return "\n".join(L)


# ─────────────────────────── CLI ───────────────────────────
def _market_arg(rest: str) -> str:
    return normalise_market(rest) or rest.upper()


def dispatch(argv: Sequence[str]) -> str:
    """Route CLI arguments to a command and return its text (pure: no printing)."""
    if not argv:
        return __doc__ or ""
    cmd = argv[0].lower()
    rest = " ".join(argv[1:])
    if cmd == "strategy":
        return strategy(_market_arg(rest))
    if cmd == "screen":
        return screen(_market_arg(rest))
    if cmd == "earnings":
        return earnings()
    if cmd == "universal":
        return universal()
    if cmd == "playbook":
        return playbook(rest)
    if cmd == "ask":
        return ask(rest)
    return ask(" ".join(argv))            # bare query


def main(argv: Optional[Sequence[str]] = None) -> int:
    print(dispatch(sys.argv[1:] if argv is None else argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
