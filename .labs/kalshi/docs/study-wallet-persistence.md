# Candidate study: do top prediction-market wallets persist?

Source: an Instagram reel (`lp_predicts`, reel `DedW0mvh3dw`) pitching a
third-party app that ranks ~3 million Polymarket wallets 1–5 stars by win rate
and ROI. The recipe: sort to five-star, find a wallet with >$100k profit in 30
days and an >80% win rate, click **Track Trade**, copy its next trade.

The pitch is rejected in `audio-extraction/sources.yaml`. The question
underneath it is good, and it is the reason this file exists.

## Why the pitch fails

**Win rate is not a skill metric here.** On a binary contract you choose your
win rate by choosing your price. Buying 80¢ favourites wins ~80% of the time
with no skill whatsoever, and a *fairly priced* favourite loses exactly the fee
every time. An 80% win rate is the signature of buying favourites, not of
forecasting well. The only honest metrics are the ones in `calibration.py` —
Brier against the market price — and P&L net of fees.

**Selecting the extreme of 3M wallets is a multiple-comparisons machine.** If
every wallet were a zero-skill coin-flipper:

| Trades | P(≥80% win rate) | Expected wallets of 3M |
|-------:|-----------------:|-----------------------:|
| 10     | 0.0547           | 164,062 |
| 20     | 0.0059           | 17,727  |
| 30     | 0.0007           | 2,146   |
| 50     | 0.000012         | 36      |

A leaderboard sorted on trailing 30-day performance will be full of these
regardless of whether skill exists anywhere on the platform. The app is not
finding talent; it is finding the right tail of a noise distribution. Note how
fast the column collapses with trade count — **trade count is the variable that
matters, and the leaderboard does not surface it.**

**Copy latency is adverse selection.** The whale takes the available liquidity;
you fill behind them at a worse price. On a 90¢ contract the entire fee-plus-edge
budget is 0.70% of notional, so a couple of cents of slippage is the whole thing.

## The honest test

Polymarket trades are public on-chain, which makes this cheaply falsifiable —
the same property that justifies this lab.

1. **Ingest** on-chain trades (wallet, market, side, price, size, timestamp)
   and the resolution of every market touched.
2. **Rebuild the leaderboard point-in-time** as of each month-end T, using only
   data available at T. No lookahead, exactly as `whale_13f` models filing lag.
3. **Score the next 30 days**, not the trailing ones. For the top decile by
   trailing P&L, measure forward P&L net of fees, forward Brier versus the
   market price at entry, and survival (how many are still active at T+30).
4. **Benchmark against two nulls**: a random wallet with matched trade count,
   and a mechanical buy-favourites-at-80¢ strategy. The second is the one that
   kills most copy-trading claims, because it reproduces the win rate for free.
5. **Cluster by market** in every bootstrap. Wallets crowd into the same few
   popular markets; those are not independent observations.
6. **Add latency**: re-score filling 1, 5 and 30 minutes behind the whale. If
   the edge dies at 5 minutes it is not implementable.

Gate: `screen_series` already encodes the right shape — skill, event-clustered
significance, fee hurdle, sample size. Re-use it with wallets in place of series.

## Prior expectation

Low. The published finding is that prediction-market prices are close to
calibrated and that takers lose, with mispricing concentrated in the tails
(see `edge-thesis.md`). Persistent wallet-level alpha large enough to survive
copy latency would be surprising. The study is worth running anyway because
it is cheap, it needs no money at risk, and a null result is genuinely
informative — it closes off an entire category of pitch.

## Blocker to resolve first

US access to Polymarket now runs through a CFTC-regulated product following
the QCEX acquisition, and reporting suggests direct crypto-wallet trading may
no longer be available to US users, while the international venue still runs
on wallets ([startpolymarket](https://startpolymarket.com/countries/united-states/),
[cryptonews](https://cryptonews.com/cryptocurrency/is-polymarket-legal/),
[predscope](https://predscope.com/guide/polymarket-us)). Sources conflict and
none is Polymarket's own documentation. **If the 3M wallets live on a venue a
US operator cannot trade, the study is interesting but not actionable** — so
confirm this before building any ingest. The research value stands either way:
the same persistence question applies to Kalshi, where this lab can already
score it.
