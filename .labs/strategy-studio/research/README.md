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

## The shared lesson

Both claims were true *gross* and false *net*. The engine defaults to 5 bps/side
for exactly this reason — see [[Decisions]], 2026-07.

Each script is strictly out-of-sample where it fits a model: expanding-window
refit, training-only standardisation, training-only threshold cuts. If you add
one, keep that discipline or the result is not worth storing.

Related: `../../audio-extraction/sources.yaml` (verdicts per reel) ·
`Trading/Engine Backlog.md`
