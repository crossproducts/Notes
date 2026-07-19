# Paper Trading Journal

The evidence file. Real money waits until this journal proves the system
behaves. One entry per week, ~10 minutes, from `/paper/log`, `/paper/account`,
and the Grafana dashboard.

## Weekly entry template
```
## Week of YYYY-MM-DD
- Account equity: $ ____  (Δ week: ____%)
- Champion(s) & signals fired: 
- Actions taken (BUY/SELL/HOLD/BLOCKED):
- Tracking vs backtest expectation: on-track / drifting / broken
- Incidents (missed runs, silent failures, weird fills):
- One thing to fix:
```

## What "on-track" means
- Live paper P&L within the Monte Carlo p5–p95 band of the champion's backtest
- No unexplained divergence between expected book and Alpaca positions (`/risk/reconcile`)
- Zero silent failures — every scheduled run either texted a result or an [ERROR]

---

## Entries

(start here — first entry after the next 9:35 ET paper run)

Related: [[Go-Live Checklist]] · [[Strategy Studio System]]
