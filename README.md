# market-screener-rag

A **credit-free, offline** retrieval + screening tool that runs on the **metrics that
actually work in each market** — the backtested, multiple-testing-survived winning
strategies from a multi-market systematic research platform (India, US, Korea, Japan,
Europe, China). It answers what the winning strategy is per market, reports each
strategy's **historical earnings**, and applies the winning screen to a current-universe
snapshot to produce **stock picks and buy/sell signals**.

No paid API, no model download: rule-based strategy knowledge base + deterministic
screening over bundled ratios + TF-IDF retrieval (scikit-learn). **Numbers come from the
backtests / the data — never invented.**

> ⚠️ **Research and education only — NOT investment advice.** All earnings are gross of
> costs and short-borrow, on survivorship-biased universes; read spreads, not levels.

## The winning strategy per market (backtested, point-in-time)

| market | character | book | winning metric | historical earnings | significance |
|---|---|---|---|---|---|
| **India** | momentum/trend | **long-only** | trend + sector-relative cheapness | value **+5.3%/6M** (≈+10.9%/yr); trend IR 2.34 | t 2.5 · DSR **0.994** ✅ |
| **Korea** | mean-reversion | **full long/short** | cheap∩hi-ROE − expensive∩lo-ROE | **+4.83%/6M** (≈+9.9%/yr) — strongest | t **4.17** · DSR 0.99 ✅ |
| **US** | mixed/light | long-tilt | short-horizon cheap-vs-market | **+1.72%/3M** (≈+6.9%/yr) | t 2.32 ✅ (fades by 6M) |
| **Europe** | momentum (bull) | directional | 12-month momentum | IR 1.39 (bull) | DSR 0.985 ✅ · value underpowered |
| **Japan** | no robust factor | — | *(none survives)* | technical: real null; value underpowered | no DSR survivor 🔴 · value needs EDINET key |
| **China** | momentum/retail | — | value **tested & fails** | cheap−rich ≈ 0% (t 0.04) — powered null | DSR n/a · value edge absent ✅ tested |

**The universal finding:** momentum/trend (bull regime) is the ONE metric that works in
nearly every market and survives the Deflated-Sharpe multiple-testing correction (India
trend, Korea breakout, Europe momentum). Mean-reversion works only in bear regimes and is
**fragile everywhere**. Value-reversion works where powered (IN/US/KR) and — now tested on
10y data — **fails in China** (the multiple converges but doesn't reward it: a real null,
not a data gap). Japan has **no technical factor that survives multiple-testing**; its value
question stays underpowered until an EDINET key enables deep history. Every cell is a tested
verdict or an explicit "needs data X" — never an invented number.

## Usage

```bash
pip install -r requirements.txt

python screener_rag.py strategy KR        # winning Korea strategy + its earnings
python screener_rag.py screen IN          # apply the India winning screen -> live picks
python screener_rag.py screen KR          # Korea long/short book
python screener_rag.py earnings           # historical earnings of every strategy
python screener_rag.py universal          # the metric that works in every market
python screener_rag.py ask "why long-only in india"
```

## How it works

- **`winning_strategies.json`** — the knowledge base: per-market character, book, winning
  metrics, screen rules, backtested earnings (t-stats, Deflated-Sharpe), and data-sufficiency
  status. Every figure traces to a point-in-time backtest.
- **`screener_rag.py`** — routes strategy/earnings/universal questions to the KB, applies the
  per-market winning screen to the bundled ratios/clusters to emit live picks (long/short as
  the market's book allows), and answers open questions via TF-IDF retrieval.
- **`data/`** — a bundled snapshot of current fundamentals ratios + peer-valuation clusters
  (regular git objects, not LFS), so the screener runs standalone.

## Method & caveats

Point-in-time backtests with `filed`-date lags; non-overlapping t-stats; **Deflated Sharpe**
(López de Prado) multiple-testing correction; **sufficiency-gated** — only markets with enough
powered + complete data get a verdict. Sizing discipline: inverse-vol + vol-target + kill-switch;
capacity ~$300–500k before the illiquidity edge decays. The edge is **illiquidity, not size**.

Descriptive research pipeline. Not investment advice. No warranty.
