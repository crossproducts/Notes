# Kalshi Lab — calibration-first event-contract research

Binary event contracts on [Kalshi](https://kalshi.com), a CFTC-regulated
exchange. Contracts settle at $1 if the event happens and $0 if not, so the
quoted price *is* a probability — which makes this the one venue in this repo
where a forecast can be scored directly against ground truth.

**Status: analytical core complete and tested (43 tests, pure stdlib). Market
ingest is not built — see [Open piece](#open-piece-ingest).** Nothing here has
traded, and no claim is made that it will be profitable.

Read [`docs/edge-thesis.md`](docs/edge-thesis.md) first. It is the argument for
why this is worth building, the published evidence, and — more usefully — the
four conditions that would prove it wrong.

## The idea in one paragraph

An equity backtest cannot tell you whether a *forecast* was right, only whether
a P&L curve went up. Every market here resolves to a known 0 or 1, which is a
supervised label. You can measure your probabilities against thousands of
settled markets, and against the only benchmark that counts — the price itself
— **before risking anything**. The edge, where it exists, is small and
concentrated in the price tails; the fee schedule happens to be cheapest in
exactly those tails. That alignment is the whole thesis.

## Pipeline

```
  1. INGEST    settled markets + price history + resolutions      [NOT BUILT]
       |
  2. LABEL     join contracts to their 0/1 outcome, keyed by event
       |
  3. SCORE     calibration.py  -- Brier, log-loss, reliability bins,
       |                          skill_vs_market, clustered bootstrap
  4. GATE      screen.py       -- skill / significance / fees / sample
       |                          (a series must clear all four)
  5. SIZE      edge.py         -- EV and fractional Kelly, net of fees
       |
  6. EXECUTE   maker-first resting limit orders                   [NOT BUILT]
       |
  7. MONITOR   rolling Brier vs the market; stop when skill decays [NOT BUILT]
```

Stages 2–5 run today on synthetic data:

```bash
cd .labs/kalshi
python -m kalshi_lab.demo            # fee hurdle, the gate, calibration, sizing
python -m unittest discover -s tests -t .
```

No dependencies — the core is deliberately pure stdlib so it runs anywhere.

## Modules

| Module | What it does |
|---|---|
| `fees.py` | The fee model. `0.07·C·P·(1−P)·multiplier`, maker `0.0175`. Peaks at 50¢ in dollars; as a share of notional it is `0.07·(1−P)`, so a 5¢ longshot costs **19× more** per dollar risked than a 95¢ favourite. |
| `edge.py` | EV (`p − price − fee`) and Kelly (`(p − cost)/(1 − cost)`), quarter-Kelly by default. All of it is exact except `p`, which is the one thing you are guessing. |
| `calibration.py` | Brier, log-loss, reliability bins, calibration slope. `skill_vs_market` is the gate that matters. `bootstrap_paired_improvement` resamples whole events. |
| `screen.py` | Four-gate series verdict with diagnostic rejection reasons. |
| `demo.py` | Runs stages 3–5 end to end on generated history. |

## Two findings the code enforces

**Being well calibrated is not an edge.** The market is also well calibrated.
`expected_value(0.50, 0.50)` is *negative* — buying at exactly your own
probability loses the fee. Only beating the price pays, which is why
`skill_vs_market` is the first gate.

**Correlated contracts are not independent observations.** A hundred strikes on
one CPI print carry roughly one event's worth of information. A naive bootstrap
over contracts measures 4.6–5.4× too narrow on realistic synthetic data (there
is a test pinning this). Always pass `clusters`.

The demo makes a third point by example: a series with *statistically
significant* skill is still rejected because the edge does not clear its fee
hurdle. That is the gate working.

## Relationship to `.labs/strategy-studio`

Reuses its **patterns**, not its engine — the equities engine works on
continuous price series and `pct_change` returns, which binary contracts do not
have. What transfers: the champion/challenger gate shape, the Postgres +
Grafana results store, the in-process scheduler, the pre-trade risk check and
kill switch in `risk.py`, and SMS alerting via `.labs/email-sender`.

**A flag worth stating plainly.** `strategy-studio/docs/next-level-plan.md` has
a DO NOT BUILD list whose item 2 rules out "a second broker, different asset
class, before the primary system is live-validated — distraction." A Kalshi lab
is exactly that pattern. The counter-argument is that this is a *research*
project with a cheap kill criterion rather than a second trading venue, and
that it can be falsified without money or a live connection. But that is an
argument, not a refutation. If the equities system is not yet live-validated,
this should stay in the sandbox stage and not compete for execution attention.

## Open piece: ingest

The API client is deliberately **not** written. Third-party guides agree on
RSA-PSS request signing with `KALSHI-ACCESS-KEY` / `-TIMESTAMP` / `-SIGNATURE`
headers, but they disagree on the base URL (`demo-api.kalshi.co`,
`external-api.demo.kalshi.co`, `trading-api.kalshi.com`,
`api.elections.kalshi.com`), on the PSS salt length, and on fee rounding.
Shipping unverified auth code would be guessing, so these must be read from
the official docs first:

1. Base URLs for production and demo, and whether demo needs separate keys.
2. The exact signed message (timestamp + method + path; query string included?).
3. PSS salt length.
4. Per-series `multiplier` and maker-fee flag from `/trade-api/v2/series/{ticker}`
   — `FeeSchedule` exists so that swap is one line.
5. Fee rounding: per order or per contract.

Then: pull settled markets, persist as fixtures in `fixtures/`, and run
`screen_series` per series. Build the forecaster only for series the market
calibration report says are mispriced.

Sources consulted (all third-party, none authoritative):
[rekko](https://rekko.ai/docs/guides/kalshi-api-guide) ·
[predictandprofit](https://predictandprofit.io/blog/kalshi-api-python-guide) ·
[agentbets](https://agentbets.ai/guides/kalshi-api-guide/) ·
[predictionhunt](https://www.predictionhunt.com/blog/kalshi-api-getting-started-guide) ·
[parlay](https://www.parlay.run/kalshi-api) ·
[predscope](https://predscope.com/guide/kalshi-api) ·
[kalshi-python-sdk](https://github.com/TexasCoding/kalshi-python-sdk) ·
[kalshi-client](https://github.com/vaguenebula/kalshi-client) ·
[mcp-server-kalshi](https://github.com/9crusher/mcp-server-kalshi) ·
[quantvps](https://www.quantvps.com/blog/how-to-setup-kalshi-trading-bot)

## Roadmap

1. **Verify the API facts above**, then write `client.py` against demo only.
2. **Ingest settled history** for 3–4 candidate series. Skip Fed/rates — the
   literature says they are calibrated.
3. **Market calibration report per series** (`calibration_by_price_bucket`).
   Find where the book is actually wrong before building any forecaster.
4. **Build a forecaster only where step 3 found mispricing**, and run
   `screen_series`. Expect rejections; that is the gate doing its job.
5. **Paper trade** a passing series on the demo environment, maker-only.
6. **Live, small**, only if paper skill holds and `net_edge` stays positive.

Steps 1–4 need no money and no live connection. Do not skip to 5.

## Setup

```bash
cp .env.example .env     # only needed from step 1 onward
```

Nothing in the lab reads `.env` yet — the core is offline by design.
