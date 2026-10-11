# research/

Falsification harnesses. One file per claim we tested and did **not** adopt.

These are kept deliberately. A reproducible negative result is worth more than a
deleted branch — when the same idea comes back round in another reel, the answer
is already here with the numbers attached.

They are **not** part of the API. `research/` is mounted read-only into the
container at `/app/research`, so no copy step is needed:

```bash
docker compose up -d
docker compose exec -T api python /app/research/overnight_check.py SPY QQQ
```

> On Git Bash, prefix with `MSYS_NO_PATHCONV=1` or `/app/...` gets rewritten
> into a Windows path.

| Script | Claim under test | Verdict |
|---|---|---|
| `overnight_check.py` | Holding **only overnight** (close→open) captures all the return; intraday loses it. Reel `DeF6WMaB-NX`, Knuteson. | **Real but cost-killed.** Decomposition is exact — (overnight × intraday) reproduces buy&hold to the dollar. Gross SPY sharpe 0.75 vs buy&hold 0.45. At our 5 bps/side SPY is **−99%, sharpe −1.42**; QQQ −96%. Survives only near 1 bp, where SPY's 0.27 still trails buy&hold. |
| `er_claim_check.py` | A logistic model over 15 features predicts next-day **efficiency ratio**; gating out low-efficiency days improves a strategy. Reel `DeF5_5yPtDb`. | **Falsified.** OOS AUC 0.519 (SPY) / 0.538 (QQQ) — below the majority-class baseline on both. The reel's monotonic tercile table does not reproduce. Gating hurt **10/10** strategy×instrument combinations. |
| `champion_full_cycle.py` | Is the champion an artifact of its 2020-start measurement window? (E6) | **Yes, partly.** `momentum` scores sharpe **0.95** on 2020+ but **0.23** on 2000+ — a 0.72 spread, the **worst rank instability of any real strategy** in the registry. `trend_ma` is #1 over the full cycle (0.45) and beats buy&hold on **all three** windows; `momentum` beats it on only one. But the walk-forward gate is a near-tie (543.6% vs 541.6%), because WF re-optimises the lookback each window — momentum's weakness is its *fixed* parameter, not the concept. |
| `ema_pullback_check.py` | EMA3>EMA7>EMA50 + ATR(14) flat/falling + a bearish candle, entered on a buy stop with a 2R bracket, returns **449% in 12 months**. Reel `DeUGFf4yLX8`. | **Falsified, and not merely cost-killed.** SPY 2000+ (26.7y): 331 trades, win **34.1%**, expectancy **-0.231R**, -1.71%/yr vs buy-and-hold +8.37%/yr. A 2R bracket breaks even at 33.3% - which is also the driftless random-walk rate, so 34-36% *is* the coin flip. Still negative at **zero cost** (-0.073R). A control arm that keeps the bracket but drops both filters scores **-0.118R, better than the full rules**, on twice the trades. Best case anywhere was BTC-USD 2017+ at +0.46%/yr against +36.61% buy-and-hold. |

## The shared lesson

The first two claims were true *gross* and false *net*. The engine defaults to 5 bps/side
for exactly this reason — see [[Decisions]], 2026-07.

Each script is strictly out-of-sample where it fits a model: expanding-window
refit, training-only standardisation, training-only threshold cuts. If you add
one, keep that discipline or the result is not worth storing.

Related: `../../audio-extraction/sources.yaml` (verdicts per reel) ·
`Trading/Engine Backlog.md`
