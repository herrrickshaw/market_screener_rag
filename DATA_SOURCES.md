
```markdown
# DATA_SOURCES.md - market-screener-rag

Status as of 2026-11-08. Research and education only; not investment advice.
The screener is offline: it reads the two CSV snapshots below plus `winning_strategies.json`.

## 1. Bundled data

### 1.1 `data/valuation_clusters.csv` (3,183 rows, 32 columns)
- What: per-company valuation z-scores, peer cluster id, and a verdict (UNDERPRICED / fair / OVERPRICED).
- Markets: India (1,179 rows, source yfinance), Korea (1,470, OpenDART), US (534, SEC EDGAR). Japan, Europe, China are not present.
- Fields: market, ticker, name, currency, fy_end, close, close_date, mcap_local, pe, pb, roe, roa, roce, debt_to_equity, current_ratio, gross_margin, operating_margin, net_margin, fcf_yield, cfo_to_ni, asset_turnover, revenue_growth, source, computed_at, eps, cluster, pe_z, pb_z, valuation_z, val_pct, roe_rank, verdict.
- Snapshot dates: close_date 2026-05-27..2026-07-23 (stale by 3.5+ months).
- Publishers and terms:
  - Yahoo Finance (yfinance): https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html - sharing/sublicensing of the data prohibited. Private only.
  - OpenDART (Financial Supervisory Service, Korea): https://opendart.fss.or.kr/ - free key; check terms of use before redistribution.
  - SEC EDGAR XBRL: https://data.sec.gov/ - US government public information; declared User-Agent, <= 10 req/s.
- Caveats: ratios are single-period (TTM or last fiscal year) and unwinsorised: current_ratio max 63,152, ROE max 3,748%, PE as low as 0.01. India PE values near 1 to 5 for large caps indicate unit or EPS artefacts and should not be treated as bargains.
- Collection: upstream pipeline in the private global-market-research-platform; not reproducible from this repo.

### 1.2 `data/all_ratios.csv` (10,202 rows, 10 columns)
- What: latest fundamentals ratios per ticker: market, ticker, fy_end, close, eps, pe, pb, roe, mcap_local, earnings_yield.
- Markets: US 4,591; IN 1,595; KR 1,531; JP 1,164; CN 926; EU 395.
- Caveats: India pb never populated, roe 14%; 244 India rows have EPS about 1e-6 (Rs crore vs absolute INR mix); fy_end extends to 2029-12-31 (forward-dated periods); no per-row source column (add one).
- Terms: inherits the sources above plus exchange / EDINET / Eastmoney origins for JP and CN (not documented).

### 1.3 `winning_strategies.json`, `edge_matrix.csv`
- Own backtest results (generated 2026-07-25): per-market character, winning metric, t-stats, Deflated Sharpe, sufficiency flags. Original panels live in a private repo and are not included; numbers cannot be re-derived here.
- Method statement: point-in-time (filed date or fiscal-year-end + 90 days, 120 for China), non-overlapping t-stats, gross of costs, survivorship-biased universes.

## 2. External data used in the research but not bundled
- Japan deep panel: Sakana AI EDINET-Bench task sample (about 1,437 firms), derived from EDINET (Japan FSA). Dataset card: https://huggingface.co/datasets/SakanaAI/EDINET-Bench (license: other). Paper: arXiv:2506.08762. Do not redistribute filing text.
- Damodaran (NYU Stern) global industry tables for the speculation cross-check: https://pages.stern.nyu.edu/~adamodar/ (cite; no explicit licence found).

## 3. Literature referenced (citations only; no paper text is stored)
Bailey and Lopez de Prado (2014); Harvey, Liu and Zhu (2016); Harvey and Liu (2015); De Bondt and Thaler (1985); Lakonishok, Shleifer and Vishny (1994); Jegadeesh and Titman (1993); Moskowitz, Ooi and Pedersen (2012); Piotroski (2000); Almgren and Chriss (2000); Amihud (2002); Corwin and Schultz (2012); Tibshirani (1996); Sugiura et al. (2025). Verify each citation with Crossref/OpenAlex before publication.

## 4. Open items
1. Add Japan, Europe, China clusters or remove the "winning screen per market" claim for them.
2. Winsorise or flag extreme ratios; fix India EPS units; drop forward-dated fy_end.
3. Add `source` to `all_ratios.csv`; record collection dates per row.
4. Decide publication scope: derived verdicts only (no raw close/mcap) if made public.
5. Refresh snapshots (latest 2026-07-23) and `winning_strategies.json` (2026-07-25).
6. Add LICENSE and NOTICE (SEC, Damodaran, EDINET-Bench attribution).
```
