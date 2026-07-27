# Market playbook — retail-accessible edges, ranked by priority per market

Only durable + retail-harvestable edges (low information-asymmetry tax). Ranked by this project's backtests. 🥇 primary · 🥈 secondary · ⚙️ base · 🚫 avoid (tested & fails).

## IN — *momentum / long-only*

- 🥇 PRIMARY — **Momentum / Trend** — trend DSR 0.994 — most robust factor found; long-only
- 🥈 secondary — **Value-reversion (cheap PE)** — +5.3%/6M t2.5 (sector-relative), long-only
- 🥈 secondary — **Quality (hi-ROE) overlay** — earns premium behind the liquidity gate
- ⚙️ base — **Insider sentiment (6-12m)** — filings-based, 6-12m outperformance
- ⚙️ base — **Passive core (DCA+rebalance)** — always-on base: DCA + annual rebalance, vol-targeted
- 🚫 AVOID — **Value+Quality Long/Short** — −1.0%/6M — momentum runs shorts over

## US — *mixed / efficient — light*

- 🥇 PRIMARY — **Value-reversion (cheap PE)** — +1.7%/3M t2.3 — best US edge, hold ≤3M
- ⚙️ base — **Value+Quality Long/Short** — +1.7%/6M t1.0 marginal
- ⚙️ base — **Momentum / Trend** — mom DSR 0.90 fragile — light
- ⚙️ base — **Insider sentiment (6-12m)** — SEC Form 4, documented edge
- ⚙️ base — **Passive core (DCA+rebalance)** — always-on base: DCA + annual rebalance, vol-targeted
- 🚫 AVOID — **Quality (hi-ROE) overlay** — Piotroski INVERTED in US

## KR — *mean-reversion / full L/S*

- 🥇 PRIMARY — **Value+Quality Long/Short** — +4.83%/6M t4.17 — STRONGEST edge of all; full L/S
- 🥈 secondary — **Value-reversion (cheap PE)** — +3.85%/6M t1.5
- 🥈 secondary — **Momentum / Trend** — breakout DSR 0.99
- 🥈 secondary — **Quality (hi-ROE) overlay** — hi-ROE cheap = the Korea discount
- ⚙️ base — **Insider sentiment (6-12m)** — DART disclosures
- ⚙️ base — **Passive core (DCA+rebalance)** — always-on base: DCA + annual rebalance, vol-targeted

## JP — *value-reversion*

- 🥇 PRIMARY — **Value-reversion (cheap PE)** — +6.6%/6M t4.84 — strongest value anywhere
- 🥈 secondary — **Value+Quality Long/Short** — ROE available; extension of value
- ⚙️ base — **Quality (hi-ROE) overlay** — pairs with value
- ⚙️ base — **Insider sentiment (6-12m)** — EDINET disclosures
- ⚙️ base — **Passive core (DCA+rebalance)** — always-on base: DCA + annual rebalance, vol-targeted
- 🚫 AVOID — **Momentum / Trend** — no DSR survivor — whipsaws

## EU — *momentum (bull)*

- 🥇 PRIMARY — **Momentum / Trend** — mom252 DSR 0.985 — primary EU edge
- ⚙️ base — **Insider sentiment (6-12m)** — 
- ⚙️ base — **Passive core (DCA+rebalance)** — always-on base: DCA + annual rebalance, vol-targeted

## CN — *speculation-ruled — passive only*

- 🥈 secondary — **Momentum / Trend** — breakout +2.77%/21d bull-gated (2026-07 replay); costs are the constraint
- ⚙️ base — **Passive core (DCA+rebalance)** — always-on base: DCA + annual rebalance, vol-targeted
- 🚫 AVOID — **Value-reversion (cheap PE)** — TESTED & FAILS (t0.3) — do not run
- 🚫 AVOID — **Value+Quality Long/Short** — value leg fails

## Regime gating (2026-07 full-history replay)

10y Darvas replay, ~470k signals, top-1000 liquid universe per market, regimes
point-in-time from a trimmed top-20 blue-chip basket (trend: EMA100
position+slope; vol: expanding percentile). Date-clustered stats. Source:
[price_prediction_backtest](https://github.com/herrrickshaw/price_prediction_backtest)
`docs/HISTORICAL_REPLAY.md`.

- **Gate every breakout entry on market trend regime.** Breakout-buy 21d excess, bull vs bear:
  KR +3.54% vs +1.56% · CN +2.77% vs +1.62% · IN +2.08% vs +0.57% (dead) ·
  JP +0.80% vs −0.11% (dead) · US +0.66% vs **−0.85% (harmful)**.
  The gate roughly doubles the buy leg everywhere; bear-regime breakouts are
  dead in US/JP/IN.
- **Breakdown-sell is contrarian, not a short signal** — breakdown names
  *outperform* peers +1.0–1.6% at 21d in bear regimes in all five markets.
  Use as a mean-reversion watch list; never short breakdowns.
- **Prefer LOW/MID-vol regimes for breakouts** (KR LOW-vol +4.67% t8.2; wins
  in 4 of 5 markets). A 6-date live sample said the opposite (HIGH-vol) —
  overturned by the full replay; distrust regime reads from short windows.
- CN momentum upgraded from "untested, character-implied" to **tested**:
  +2.77% bull-gated at 21d (before CN's heavy round-trip costs).

## Rules that apply everywhere

- **Horizon:** monthly-to-6-month rebalances only. Fast signals lose to the information-asymmetry tax (you'd be the counterparty).
- **Sizing:** inverse-vol + vol-target + a kill-switch (halves max drawdown).
- **Capacity:** the edge is illiquidity-driven — **~$300–500k** before it decays; a retail/family-office edge, not institutional.
- **Read spreads, not win-rate:** ~50% hit-rate is normal; the profit is in magnitude.
- **Long-only vs long/short:** short only where the market mean-reverts (KR ✅); never short a trending market (IN 🚫).
- **Costs:** net of round-trip cost the edge must still clear — worst in IN/CN (wide spreads), best in US.

> Descriptive research — not investment advice. Every ranking traces to a committed backtest (committed backtests).