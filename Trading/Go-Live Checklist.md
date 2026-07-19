# Go-Live Checklist

Every box checked before a single real dollar trades. Thresholds from the
researched plan (`.labs/strategy-studio/docs/next-level-plan.md`, 2026-07-18)
— never loosen a gate mid-paper-run.

## Strategy quality gates
- [ ] Champion survived walk-forward (positive stitched OOS return, cost-adjusted)
- [ ] ≥ 8 weeks continuous paper trading on the same champion (no mid-run swaps)
- [ ] ≥ 100 paper trades logged (across the book) — enough sample vs backtest
- [ ] Paper Sharpe ≥ 0.8 over the validation window
- [ ] Paper max drawdown < 20%
- [ ] Tracking error vs backtest expectation ≤ 50% (paper fills are systematically
      optimistic — infinite liquidity, no queue; expect live to be worse)
- [x] Signal-timing skew resolved: engine now fills at next open, matching 9:35
      live execution (2026-07-18)

## System reliability gates
- [ ] Zero silent failures for 30 consecutive days (every run texts success or [ERROR])
- [ ] Kill switch tested: engaged → verified nothing executes → resumed
- [ ] `/risk/reconcile` clean (no orphan positions, no book mismatches) for 2 weeks
- [ ] Stack survives a host reboot unattended (restart policies verified)

## Human gates
- [ ] Max loss I accept before pulling the plug is written down in [[Decisions]] — with the date
- [ ] Understand PDT rules for the account size; account structure chosen accordingly
- [ ] Tax treatment reviewed — wash sales bite automated daily strategies; the
      475(f) mark-to-market election exempts them entirely, next window is the
      2027 election (file by 2027-04-15 with the 2026 return); worth a CPA consult
      at ~150–300 trades/yr
- [ ] Live account funded with money I can lose entirely, and no more

## The switch itself
- [ ] `paper=True` change reviewed as a deliberate PR, not a hot edit
- [ ] Position size for live starts at ≤ 25% of what paper traded

Related: [[Paper Trading Journal]] · [[Decisions]]
