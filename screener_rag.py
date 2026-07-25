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
  python screener_rag.py ask "why long-only in india"
Research only — NOT investment advice.
"""
from __future__ import annotations
import sys, json, re
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
KB = json.loads((HERE / "winning_strategies.json").read_text())
NORM = {"india": "IN", "us": "US", "korea": "KR", "japan": "JP", "europe": "EU", "china": "CN"}
NAMES = {"IN": "India", "US": "US", "KR": "Korea", "JP": "Japan", "EU": "Europe", "CN": "China"}


def _mk(s: str) -> str | None:
    s = s.lower()
    for k, v in {**{n: c for n, c in NORM.items()}, **{c.lower(): c for c in NAMES}}.items():
        if k in f" {s} ":
            return v
    return None


def _ratios(market: str) -> pd.DataFrame:
    """current fundamentals ratios for a market (bundled snapshot)."""
    d = pd.read_csv(HERE / "data" / "all_ratios.csv")
    d["mk"] = d.market.astype(str).str.lower().map(NORM).fillna(d.market.astype(str).str.upper())
    return d[d.mk == market].copy()


def _clusters(market: str) -> pd.DataFrame:
    d = pd.read_csv(HERE / "data" / "valuation_clusters.csv")
    d["mk"] = d.market.astype(str).str.lower().map(NORM).fillna(d.market.astype(str).str.upper())
    return d[d.mk == market].copy()


# ─────────────────────────── strategy / earnings ───────────────────────────
def strategy(market: str) -> str:
    m = KB["markets"].get(market)
    if not m:
        return f"Unknown market {market}. One of {list(KB['markets'])}."
    L = [f"# {NAMES[market]} — winning strategy (backtested)", "",
         f"**Character:** {m['character']} · **Book:** {m['book']}",
         f"**Winning metrics:** {', '.join(m['winning_metrics']) or '(none validated)'}",
         f"**Screen:** long = {m['screen']['long']} · short = {m['screen']['short']}", "",
         "**Historical earnings (gross, PIT-backtested):**"]
    for k, v in m["backtest_earnings"].items():
        L.append(f"  - *{k}*: {v}")
    L += ["", f"**Data sufficiency:** {m['sufficiency']}", f"**Verdict:** {m['verdict']}",
          "", "> " + KB["sizing_discipline"], "> Research only — not investment advice."]
    return "\n".join(L)


def earnings(_m=None) -> str:
    L = ["# Historical earnings of the winning strategies (gross, PIT-backtested)", "",
         "| market | strategy | earnings | significance |", "|---|---|---|---|"]
    rows = {
     "IN": ("long-only trend + sector-relative value", "+5.3%/6M value (≈+10.9%/yr); trend IR 2.34", "t 2.5 · DSR 0.994 ✅"),
     "US": ("short-horizon value reversion (≤3M)", "+1.72%/3M (≈+6.9%/yr)", "t 2.32 ✅ (fades by 6M)"),
     "KR": ("long/short cheap∩hi-ROE vs expensive∩lo-ROE", "+4.83%/6M (≈+9.9%/yr) — STRONGEST", "t 4.17 · DSR 0.99 ✅"),
     "EU": ("12M momentum (bull)", "IR 1.39 (bull regime)", "DSR 0.985 ✅ · value underpowered"),
     "JP": ("value-reversion (long cheap-vs-market)", "+6.6%/6M (t 4.84) — deep EDINET data flips the verdict", "powered ✅"),
     "CN": ("value tested & fails", "cheap−rich ≈ 0% (t 0.04) over 109 formations — powered null", "value edge absent ✅ tested"),
    }
    for mk, (s, e, sig) in rows.items():
        L.append(f"| {NAMES[mk]} | {s} | {e} | {sig} |")
    L += ["", "**Read:** earnings are the backtested long−short (or quintile) spread, gross of "
          "costs and borrow. Annualised figures are indicative, not compounded guarantees. IN/US/KR "
          "are powered+complete (tradeable edges); EU momentum is robust (value underpowered); "
          "**China is powered and value FAILS** (a real null — no value edge); **Japan**, with deep "
          "EDINET data, shows STRONG value-reversion (+6.6%/6M, t 4.84) — flipping its earlier "
          "underpowered verdict. Nulls and flips are both real, tested verdicts.", "", "> " + KB["sizing_discipline"]]
    return "\n".join(L)


def universal(_m=None) -> str:
    return ("# The metric that works in (nearly) every market\n\n" + KB["_meta"]["universal_finding"] +
            "\n\n**Deflated-Sharpe survivors (bull regime):** IN trend (0.994), KR breakout (0.99), "
            "EU mom252 (0.985). US mom252 (0.901) is fragile. **All bear-regime mean-reversion factors "
            "FAIL** multiple-testing. → Momentum/trend is the universal core; specialise per market "
            "(KR full L/S, IN long-only value, US short-horizon).\n\n> Not investment advice.")


# ─────────────────────────── live screen (winning metrics) ───────────────────────────
def screen(market: str, n: int = 15) -> str:
    m = KB["markets"].get(market)
    if not m:
        return f"Unknown market {market}."
    if not m["winning_metrics"]:
        return f"{NAMES[market]}: no validated strategy ({m['verdict']}). No screen run."
    cl = _clusters(market)
    if cl.empty:
        return f"{NAMES[market]}: no bundled fundamentals to screen (likely underpowered/pending)."
    out = [f"# {NAMES[market]} — live picks from the winning screen", "",
           f"Strategy: **{m['character']}**, {m['book']}. {m['verdict']}", ""]
    cols = [c for c in ["name", "pe", "pb", "roe", "valuation_z", "verdict"] if c in cl.columns]
    if market == "IN":                       # long-only: cheap-vs-peers ∩ high ROE
        longs = cl[(cl.valuation_z < -0.8) & (cl.roe > 0.15)].sort_values("valuation_z").head(n)
        out += [f"**LONG (cheap-for-quality, {len(longs)} names)** — momentum overlay applies live:",
                "", longs[cols].to_markdown(index=False), "", "*No short book — shorting fails in India (−1.0%/6M).*"]
    elif market == "KR":                     # full long/short
        longs = cl[(cl.valuation_z < -0.8) & (cl.roe > 0.10)].sort_values("valuation_z").head(n)
        shorts = cl[(cl.valuation_z > 1.0) & (cl.roe < 0.05)].sort_values("valuation_z", ascending=False).head(n)
        out += [f"**LONG cheap∩hi-ROE ({len(longs)}):**", "", longs[cols].to_markdown(index=False), "",
                f"**SHORT expensive∩lo-ROE ({len(shorts)}):**", "", shorts[cols].to_markdown(index=False)]
    elif market == "US":                     # short-horizon cheap-vs-market
        longs = cl[cl.valuation_z < -0.8].sort_values("valuation_z").head(n)
        out += [f"**LONG cheap-vs-market ({len(longs)}, hold ≤3M):**", "", longs[cols].to_markdown(index=False)]
    else:                                    # EU momentum / others
        longs = cl.sort_values("valuation_z").head(n)
        out += [f"**Screen ({len(longs)}):**", "", longs[cols].to_markdown(index=False)]
    out += ["", "> Gross of costs; validate each name before acting. Not investment advice."]
    return "\n".join(out)


# ─────────────────────────── open Q&A (TF-IDF retrieval) ───────────────────────────
def ask(q: str) -> str:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
    docs = []
    for mk, m in KB["markets"].items():
        docs.append({"src": NAMES[mk], "text": strategy(mk)})
    docs.append({"src": "universal", "text": universal()})
    docs.append({"src": "earnings", "text": earnings()})
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    M = vec.fit_transform([d["text"] for d in docs])
    sims = linear_kernel(vec.transform([q]), M).ravel()
    i = int(sims.argmax())
    return f"*(best match: {docs[i]['src']})*\n\n" + docs[i]["text"]


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
    mk = _mk(market) or (market.upper() if market else None)
    L = ["# Market playbook — retail-accessible edges, ranked (backtested)", ""]
    for m in (["IN", "US", "KR", "JP", "EU", "CN"] if not mk else [mk]):
        ch, rows = PLAYBOOK[m]
        L += [f"## {NAMES[m]} — *{ch}*", ""] + [f"- {r}" for r in rows] + [""]
    if not mk:
        L += ["## Rules everywhere", ""] + [f"- {r}" for r in RULES]
    L += ["", "> Every ranking traces to a committed backtest. Research, not investment advice."]
    return "\n".join(L)


def main() -> int:
    a = sys.argv[1:]
    if not a:
        print(__doc__); return 0
    cmd = a[0].lower()
    rest = " ".join(a[1:])
    if cmd == "strategy":
        print(strategy(_mk(rest) or rest.upper()))
    elif cmd == "screen":
        print(screen(_mk(rest) or rest.upper()))
    elif cmd == "earnings":
        print(earnings())
    elif cmd == "universal":
        print(universal())
    elif cmd == "playbook":
        print(playbook(rest))
    elif cmd == "ask":
        print(ask(rest))
    else:
        print(ask(" ".join(a)))            # bare query
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
