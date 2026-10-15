# Is this a step above gambling?

Yes — but for one specific structural reason, and only inside a narrow band
where the edge survives fees. This document is the argument, the evidence, and
the conditions that would prove it wrong.

## The one real advantage: ground truth

Every edge argument in `.labs/strategy-studio` is indirect. An equity backtest
cannot tell you whether a *forecast* was correct, only whether a P&L curve went
up — which is why that lab needs walk-forward splits, Monte Carlo, and a
champion/challenger registry just to fend off fooling itself. Its own
architecture review records the failure mode plainly: it had been promoting
strategies on in-sample Sharpe, the exact overfitting the walk-forward endpoint
existed to catch.

Event contracts remove that whole problem. Every market resolves to a known 0
or 1. That is a **supervised label**. You can measure whether your
probabilities are any good on thousands of settled markets without simulating a
single trade, and you can measure it against the only benchmark that matters:
the price itself.

That is the entire thesis. Not "prediction markets are inefficient" — they are
mostly efficient. The claim is that **this is the one venue where you can
cheaply and honestly find out whether you have an edge before risking money.**
Equities will never give you that.

## What the research actually says

The evidence is consistent on direction and sobering on magnitude.

**Favourite-longshot bias is real but tail-concentrated.** The main study of
Kalshi transaction data (>300,000 contracts) finds prices become more accurate
approaching close, and that low-priced contracts lose money after fees while
high-priced contracts earn small positive returns
([Makers and Takers, CESifo](https://www.ifo.de/en/cesifo/publications/2026/working-paper/makers-and-takers-economics-kalshi-prediction-market) ·
[VoxEU summary](https://cepr.org/voxeu/columns/economics-kalshi-prediction-market) ·
[UCD working paper](https://www.ucd.ie/economics/t4media/WP2025_19.pdf)).
An independent calibration check reports a slope of 1.07 one day before
resolution — close to calibrated, with bias only in the tails
([kalshi-calibration](https://github.com/nalimmm/kalshi-calibration)).

**Where the edge is not.** A study of 2,668 settled macro contracts finds Fed
and interest-rate markets close to perfectly calibrated with no significant
bias ([Information Efficiency Across Macroeconomic Prediction
Markets](https://www.researchgate.net/publication/409472804_Information_Efficiency_Across_Macroeconomic_Prediction_Markets_Evidence_from_Kalshi)).
Do not start there. Those are the crowded, well-arbitraged markets.

**Where it might be.** The same work finds unemployment markets the weakest
performers, with statistically significant systematic mispricing — longshots
below $0.30 significantly overpriced ([Market Efficiency and the
Favorite-Longshot Bias in Unemployment Prediction
Markets](https://www.researchgate.net/publication/409238145_Market_Efficiency_and_the_Favorite-Longshot_Bias_in_Unemployment_Prediction_Markets)).
Sports contracts show bias too, but the direction is not universal and reverses
in some books ([Prices, Probabilities, and
Parlays](https://arxiv.org/pdf/2607.14430)).

**Makers beat takers.** Both lose on cheap contracts, but takers lose
substantially more. Combined with the fee schedule below, this is the strongest
structural finding in the literature for a retail operator.

## The fee geometry decides everything

The fee is `0.07 × contracts × P × (1−P) × series_multiplier`, maker coefficient
`0.0175`, charged only on a flagged minority of series
([marketmath](https://marketmath.io/platforms/kalshi) ·
[pm.wiki](https://pm.wiki/learn/kalshi-fees-explained) ·
[polykal](https://polykal.net/kalshi-fees-explained/) ·
[predictefy](https://blog.predictefy.com/kalshi-fees) ·
[predictreport](https://predictreport.io/blog/kalshi-fees-explained) ·
[botforkalshi](https://www.botforkalshi.com/blog/kalshi-fees-explained)).
In dollars it peaks at 50¢. As a **share of capital at risk** it inverts to
`0.07 × (1−P)`, and that is the number that decides whether a trade pays:

| Price | Fee/contract | % of notional | Relative mispricing needed to break even |
|------:|-------------:|--------------:|------------------------------------------:|
| 5¢    | $0.0033      | 6.65%         | 6.65% |
| 25¢   | $0.0131      | 5.25%         | 5.25% |
| 50¢   | $0.0175      | 3.50%         | 3.50% |
| 90¢   | $0.0063      | 0.70%         | 0.70% |
| 95¢   | $0.0033      | 0.35%         | 0.35% |

A 5¢ longshot must be **19× more mispriced** than a 95¢ favourite before it is
worth touching. The fee curve and the published bias point the same way: buy
the favourite side, rest your orders, avoid the middle of the book.

One genuine structural advantage over equities: **holding to settlement incurs
no exit fee.** Settlement is not a trade. The equities lab pays spread and
slippage on both legs of every round trip; here one side can be free.

## What this is not

- **Not a large edge.** "Small positive returns" on favourites is the published
  finding. After fees, on a $2–5k bankroll, this is a learning system.
- **Not Fed markets.** Those are calibrated. Starting there wastes the sample.
- **Not an excuse to buy longshots.** They are the overpriced side *and* carry
  the worst fee hurdle. `demo.py` deliberately shows the sizer happily buying
  one when fed an optimistic probability — the machinery is agnostic, the
  belief is the risk.
- **Not tax-simple.** Event-contract treatment is genuinely unsettled and
  differs from the Section 475(f) analysis in the equities lab's
  `next-level-plan.md`. Do not reuse those conclusions. Ask a CPA.

## Falsification conditions

The thesis is wrong, and this lab should be abandoned, if any of these hold
after honest measurement:

1. No forecaster beats the market Brier score on any series, with an
   event-clustered CI excluding zero. (`screen_series` gate 1 and 2.)
2. The series where skill exists have mean edges below their fee hurdle.
   (Gate 3 — and note the demo's efficient series fails exactly here, with
   *statistically significant* skill that still does not pay.)
3. The tail mispricing is too thin to absorb meaningful size without moving
   the book. Liquidity is the unmeasured risk; the papers study price
   accuracy, not depth.
4. Resolution sources turn out to be ambiguous or disputed often enough that
   "known ground truth" stops being true.

Condition 2 is the likeliest killer, and the gate is built so it fails loudly
rather than quietly.

## Honest position

This is a **research project with a measurable kill criterion**, not an income
plan. Its value is that, unlike every equities strategy in this repo, it can be
*falsified cheaply* — thousands of settled markets, no money at risk, before a
single order is placed. That is what makes it a step above gambling. Whether it
is also profitable is unknown, and the gate exists to answer that honestly
rather than flatteringly.
