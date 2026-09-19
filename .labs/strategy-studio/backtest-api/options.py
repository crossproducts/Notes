"""Options overlays: Black-Scholes-approximated backtests + real Alpaca paper
execution against the live chain.

Income and defined-risk strategies on top of an underlying's daily OHLC:
  covered_call      — hold shares, sell an OTM call every `dte` days (upside
                       capped at strike, premium collected, full downside)
  cash_secured_put  — hold cash, sell an OTM put every `dte` days (obligated to
                       buy at strike if breached, premium collected)
  wheel             — alternate the two: sell puts while in cash, get assigned
                       into shares on a breach, sell calls on those shares,
                       get called away back into cash, repeat
  bull_call_spread  — buy a near-the-money call + sell a further OTM call,
                       same expiry (defined max gain/loss; backtest-only for now)
  put_credit_spread — sell a near-the-money put + buy a further OTM put, same
                       expiry (defined max gain/loss, net CREDIT; capital-
                       efficient premium selling; backtest-only for now)

Backtest pricing: Black-Scholes with REALIZED volatility (trailing `vol_window`
days) — there's no historical options chain wired up yet, so this estimates the
overlay's PAYOFF SHAPE (capped upside, premium income, downside profile), not
exact historical fills. Real premiums will differ from implied vol, skew, and
the actual bid/ask at the time. Treat results as directional, like the existing
Ollama /analyze summaries — a draft, not ground truth.

`iv_over_rv` (default 1.0, i.e. off) scales the realized-vol estimate up before
pricing, as a stand-in for the volatility risk premium — equity-index implied
vol has historically averaged ~1.1-1.3x subsequent realized vol, and that
spread is most of the real edge in premium-selling strategies, which pure
realized-vol pricing can't show at all. It's a blunt global multiplier, not a
real IV surface (no skew, no term structure, no event vol) — treat it as a
calibration knob, not ground truth.

`iv_regime_aware=true` replaces the flat `iv_over_rv` scalar with a VIX-regime-
conditional one: `iv_high_mult` (default 1.3) when VIX is above its trailing
`iv_vix_ma_days`-day MA, `iv_low_mult` (default 1.0) otherwise. The volatility
risk premium has historically widened right after a VIX spike and compressed
in prolonged calm — the opposite of the naive "sell more premium when vol
looks high" intuition — so this tracks the premium's actual behavior instead
of assuming it's constant. Still a blunt regime split, not a real IV surface.

`put_credit_spread` — sell a put at K1 (closer to spot), buy a further-OTM put
at K2 < K1 for protection, same expiry: net CREDIT collected up front, max
loss capped at (K1-K2) minus the credit. The capital-efficient way to sell
premium on SPY/QQQ-sized underlyings — ties up (K1-K2)*100 per spread instead
of the six-figure cash/shares a naked CSP or covered call needs, so it fits an
account too small for the other three strategies. Backtest-only for now (needs
Alpaca multi-leg/MLEG orders to execute live, same follow-up as bull_call_spread).

Live paper execution (sell_option) hits Alpaca's real options chain and paper
account — same paper=True guarantee as paper.py. Requires an options-enabled
Alpaca paper account (approval level is set on Alpaca's side, not here).
"""

import math
from datetime import date, timedelta

import numpy as np
import pandas as pd

import engine


def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bs_price(S: float, K: float, T: float, r: float, sigma: float, kind: str = "call") -> float:
    """Black-Scholes European option price. T in years."""
    if T <= 0 or sigma <= 0:
        return max(S - K, 0.0) if kind == "call" else max(K - S, 0.0)
    d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if kind == "call":
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)


def _trailing_vol(close: pd.Series, window: int) -> pd.Series:
    """Annualized realized vol from daily log returns."""
    log_ret = np.log(close / close.shift(1))
    return log_ret.rolling(window).std() * np.sqrt(252)


def _sigma_series(close: pd.Series, window: int) -> pd.Series:
    """Base realized-vol estimate — no vol-risk-premium adjustment. See
    _priced_sigma for the iv_over_rv / iv_regime_aware knobs applied on top."""
    sigma = _trailing_vol(close, window)
    default = float(sigma.dropna().median()) if sigma.notna().any() else 0.20
    return sigma.fillna(default)


def _iv_multiplier_series(index: pd.DatetimeIndex, vix_ma_days: int = 50,
                          low_mult: float = 1.0, high_mult: float = 1.3) -> pd.Series:
    """VIX-regime-conditional vol-risk-premium multiplier: `high_mult` while
    VIX is above its trailing `vix_ma_days`-day MA (elevated-vol regime, where
    the VRP has historically widened), `low_mult` otherwise (calm regime,
    where it's historically compressed toward/at 1x realized vol)."""
    early = (index[0] - pd.Timedelta(days=400)).strftime("%Y-%m-%d")
    vix = engine.fetch("^VIX", early)["Close"].reindex(index).ffill()
    elevated = vix > vix.rolling(vix_ma_days).mean()
    return elevated.map({True: high_mult, False: low_mult}).fillna(low_mult)


def _priced_sigma(close: pd.Series, params: dict) -> pd.Series:
    """The vol series actually used for option pricing: base realized vol,
    scaled either by a flat `iv_over_rv` (default 1.0 = off) or, when
    `iv_regime_aware` is true, by the VIX-conditional multiplier series."""
    vol_window = int(params.get("vol_window", 30))
    base = _sigma_series(close, vol_window)
    if bool(params.get("iv_regime_aware", False)):
        mult = _iv_multiplier_series(
            close.index,
            vix_ma_days=int(params.get("iv_vix_ma_days", 50)),
            low_mult=float(params.get("iv_low_mult", 1.0)),
            high_mult=float(params.get("iv_high_mult", 1.3)),
        )
        return base * mult
    return base * float(params.get("iv_over_rv", 1.0))


def covered_call_backtest(df: pd.DataFrame, params: dict) -> pd.Series:
    dte = int(params.get("dte", 30))
    otm_pct = float(params.get("otm_pct", 0.05))
    cost_bps = float(params.get("cost_bps", 5.0))
    initial = float(params.get("initial", 100_000.0))

    close = df["Close"]
    sigma = _priced_sigma(close, params)
    r = engine.RISK_FREE_RATE
    n = len(close)

    equity = np.empty(n)
    e = initial
    for pos in range(0, n, dte):
        end = min(pos + dte, n) - 1
        S0 = float(close.iloc[pos])
        K = S0 * (1 + otm_pct)
        T = max(end - pos, 1) / 252.0
        premium = bs_price(S0, K, T, r, float(sigma.iloc[pos]), "call")
        for j in range(pos, end + 1):
            capped = min(float(close.iloc[j]), K)
            equity[j] = e * (capped + premium) / S0
        e = equity[end] * (1 - cost_bps / 10_000.0)  # roll cost
    return pd.Series(equity, index=close.index)


def cash_secured_put_backtest(df: pd.DataFrame, params: dict) -> pd.Series:
    dte = int(params.get("dte", 30))
    otm_pct = float(params.get("otm_pct", 0.05))
    cost_bps = float(params.get("cost_bps", 5.0))
    initial = float(params.get("initial", 100_000.0))

    close = df["Close"]
    sigma = _priced_sigma(close, params)
    r = engine.RISK_FREE_RATE
    n = len(close)

    equity = np.empty(n)
    e = initial
    for pos in range(0, n, dte):
        end = min(pos + dte, n) - 1
        S0 = float(close.iloc[pos])
        K = S0 * (1 - otm_pct)
        T = max(end - pos, 1) / 252.0
        premium = bs_price(S0, K, T, r, float(sigma.iloc[pos]), "put")
        for j in range(pos, end + 1):
            loss = max(K - float(close.iloc[j]), 0.0)
            equity[j] = e * (S0 + premium - loss) / S0
        e = equity[end] * (1 - cost_bps / 10_000.0)  # roll cost
    return pd.Series(equity, index=close.index)


def bull_call_spread_backtest(df: pd.DataFrame, params: dict) -> pd.Series:
    """Defined-risk directional bet: long call at K1 (near the money), short
    call at K2 > K1 (further OTM), same expiry. Backtest-only — no live
    execution yet (Alpaca multi-leg/MLEG orders are a follow-up)."""
    dte = int(params.get("dte", 30))
    otm_pct_long = float(params.get("otm_pct_long", 0.0))
    otm_pct_short = float(params.get("otm_pct_short", 0.08))
    cost_bps = float(params.get("cost_bps", 5.0))
    initial = float(params.get("initial", 100_000.0))
    if otm_pct_short <= otm_pct_long:
        raise ValueError("otm_pct_short must exceed otm_pct_long (K2 > K1)")

    close = df["Close"]
    sigma = _priced_sigma(close, params)
    r = engine.RISK_FREE_RATE
    n = len(close)

    equity = np.empty(n)
    e = initial
    for pos in range(0, n, dte):
        end = min(pos + dte, n) - 1
        S0 = float(close.iloc[pos])
        K1 = S0 * (1 + otm_pct_long)
        K2 = S0 * (1 + otm_pct_short)
        T = max(end - pos, 1) / 252.0
        sig = float(sigma.iloc[pos])
        net_debit = bs_price(S0, K1, T, r, sig, "call") - bs_price(S0, K2, T, r, sig, "call")
        for j in range(pos, end + 1):
            Sj = float(close.iloc[j])
            spread_value = max(min(Sj, K2) - K1, 0.0)
            equity[j] = e * (S0 - net_debit + spread_value) / S0
        e = equity[end] * (1 - cost_bps / 10_000.0)  # roll cost
    return pd.Series(equity, index=close.index)


def put_credit_spread_backtest(df: pd.DataFrame, params: dict) -> pd.Series:
    """Defined-risk premium-selling spread: sell a put at K1 (closer to spot),
    buy a further-OTM put at K2 < K1 for protection, same expiry — net CREDIT
    collected, max loss capped at (K1-K2) minus the credit. See module
    docstring for why this is the capital-efficient premium-selling structure
    for a small account. Backtest-only — needs Alpaca MLEG orders to execute
    live, same follow-up as bull_call_spread."""
    dte = int(params.get("dte", 30))
    otm_pct_short = float(params.get("otm_pct_short", 0.05))  # K1: put sold, closer to spot
    otm_pct_long = float(params.get("otm_pct_long", 0.10))    # K2: put bought, further OTM
    cost_bps = float(params.get("cost_bps", 5.0))
    initial = float(params.get("initial", 100_000.0))
    if otm_pct_long <= otm_pct_short:
        raise ValueError("otm_pct_long must exceed otm_pct_short (K2 further OTM than K1)")

    close = df["Close"]
    sigma = _priced_sigma(close, params)
    r = engine.RISK_FREE_RATE
    n = len(close)

    equity = np.empty(n)
    e = initial
    for pos in range(0, n, dte):
        end = min(pos + dte, n) - 1
        S0 = float(close.iloc[pos])
        K1 = S0 * (1 - otm_pct_short)
        K2 = S0 * (1 - otm_pct_long)
        T = max(end - pos, 1) / 252.0
        sig = float(sigma.iloc[pos])
        net_credit = bs_price(S0, K1, T, r, sig, "put") - bs_price(S0, K2, T, r, sig, "put")
        for j in range(pos, end + 1):
            Sj = float(close.iloc[j])
            spread_liability = min(max(K1 - Sj, 0.0), K1 - K2)
            equity[j] = e * (S0 + net_credit - spread_liability) / S0
        e = equity[end] * (1 - cost_bps / 10_000.0)  # roll cost
    return pd.Series(equity, index=close.index)


def wheel_backtest(df: pd.DataFrame, params: dict) -> pd.Series:
    """The wheel: alternate cash-secured puts and covered calls on the same
    underlying. Start in CASH, selling an OTM put every `dte` days. If the
    close at expiry is below the put's strike, treat it as assigned (bought
    at the strike) and roll into COVERED CALLS on those shares. If a covered
    call's strike is breached at expiry, treat the shares as called away and
    roll back into CASH. Repeat.

    Same approximation as the other overlays: assignment is decided by the
    close vs strike on the period's last bar, not a real chain, so intraperiod
    gap risk isn't captured. `start_state` ("cash" or "shares") picks which
    leg the wheel begins on."""
    dte = int(params.get("dte", 30))
    otm_pct = float(params.get("otm_pct", 0.05))
    cost_bps = float(params.get("cost_bps", 5.0))
    initial = float(params.get("initial", 100_000.0))
    state = params.get("start_state", "cash")
    if state not in ("cash", "shares"):
        raise ValueError("start_state must be 'cash' or 'shares'")

    close = df["Close"]
    sigma = _priced_sigma(close, params)
    r = engine.RISK_FREE_RATE
    n = len(close)

    equity = np.empty(n)
    e = initial
    assignments = 0
    for pos in range(0, n, dte):
        end = min(pos + dte, n) - 1
        S0 = float(close.iloc[pos])
        T = max(end - pos, 1) / 252.0
        sig = float(sigma.iloc[pos])

        if state == "cash":
            K = S0 * (1 - otm_pct)
            premium = bs_price(S0, K, T, r, sig, "put")
            for j in range(pos, end + 1):
                loss = max(K - float(close.iloc[j]), 0.0)
                equity[j] = e * (S0 + premium - loss) / S0
            assigned = float(close.iloc[end]) < K
        else:  # shares
            K = S0 * (1 + otm_pct)
            premium = bs_price(S0, K, T, r, sig, "call")
            for j in range(pos, end + 1):
                capped = min(float(close.iloc[j]), K)
                equity[j] = e * (capped + premium) / S0
            assigned = float(close.iloc[end]) > K

        e = equity[end] * (1 - cost_bps / 10_000.0)  # roll cost
        if assigned:
            assignments += 1
            state = "shares" if state == "cash" else "cash"

    result = pd.Series(equity, index=close.index)
    result.attrs["assignments"] = assignments
    return result


def options_metrics(equity: pd.Series, dte: int) -> dict:
    """Same shape as engine.metrics() so _persist() needs no changes — extra
    keys (like `assignments`, when the backtest fn recorded one) are simply
    ignored by _persist and pass through to the API response."""
    rf = engine.RISK_FREE_RATE
    rf_daily = (1 + rf) ** (1 / 252) - 1
    rets = equity.pct_change().fillna(0)
    peak = equity.cummax()
    max_dd = float(((equity - peak) / peak).min() * 100)
    sharpe = float((rets.mean() - rf_daily) / rets.std() * np.sqrt(252)) if rets.std() > 0 else 0.0
    period_rets = equity.iloc[::dte].pct_change().dropna()
    win_rate = float((period_rets > 0).sum() / max(len(period_rets), 1) * 100)
    m = {
        "total_return_pct": round(float(equity.iloc[-1] / equity.iloc[0] - 1) * 100, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe": round(sharpe, 2),
        "trades": max(int(np.ceil(len(equity) / dte)), 1),
        "win_rate": round(win_rate, 1),
    }
    if "assignments" in equity.attrs:
        m["assignments"] = equity.attrs["assignments"]
    return m


OPTIONS_REGISTRY = {
    "covered_call": {"fn": covered_call_backtest,
                     "grid": {"otm_pct": [0.03, 0.05, 0.08], "dte": [21, 30, 45],
                             "iv_over_rv": [1.0, 1.15, 1.3]}},
    "cash_secured_put": {"fn": cash_secured_put_backtest,
                         "grid": {"otm_pct": [0.03, 0.05, 0.08], "dte": [21, 30, 45],
                                 "iv_over_rv": [1.0, 1.15, 1.3]}},
    "wheel": {"fn": wheel_backtest,
             "grid": {"otm_pct": [0.03, 0.05, 0.08], "dte": [21, 30, 45],
                     "iv_over_rv": [1.0, 1.15, 1.3]}},
    "bull_call_spread": {"fn": bull_call_spread_backtest,
                         "grid": {"otm_pct_short": [0.05, 0.08, 0.1], "dte": [21, 30, 45],
                                 "iv_over_rv": [1.0, 1.15, 1.3]}},
    "put_credit_spread": {"fn": put_credit_spread_backtest,
                          "grid": {"otm_pct_short": [0.03, 0.05, 0.08],
                                  "otm_pct_long": [0.08, 0.10, 0.15], "dte": [21, 30, 45]}},
}


# ---- live paper execution against Alpaca's real options chain ----

def get_client():
    """Same options-enabled paper=True client as paper.py's equity client."""
    import paper
    return paper.get_client()


def find_contract(client, underlying: str, option_type: str, target_strike: float,
                  dte_target: int, dte_tolerance: int = 7):
    from alpaca.trading.requests import GetOptionContractsRequest
    from alpaca.trading.enums import ContractType

    today = date.today()
    req = GetOptionContractsRequest(
        underlying_symbols=[underlying],
        status="active",
        type=ContractType.CALL if option_type == "call" else ContractType.PUT,
        expiration_date_gte=today + timedelta(days=max(dte_target - dte_tolerance, 1)),
        expiration_date_lte=today + timedelta(days=dte_target + dte_tolerance),
    )
    contracts = client.get_option_contracts(req).option_contracts
    if not contracts:
        raise RuntimeError(f"no {option_type} contracts found for {underlying} near "
                           f"{dte_target}d expiry — is options trading enabled on this account?")
    return min(contracts, key=lambda c: abs(float(c.strike_price) - target_strike))


def latest_quote(contract_symbol: str):
    """Current bid/ask for an option contract, via Alpaca's market data API
    (separate client class from trading, same paper keys)."""
    import os
    from alpaca.data.historical.option import OptionHistoricalDataClient
    from alpaca.data.requests import OptionLatestQuoteRequest
    data_client = OptionHistoricalDataClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"))
    quotes = data_client.get_option_latest_quote(OptionLatestQuoteRequest(symbol_or_symbols=contract_symbol))
    if contract_symbol not in quotes:
        raise RuntimeError(f"no live quote for {contract_symbol} — market may be closed, "
                           "or Alpaca has no quote data for this contract")
    return quotes[contract_symbol]


def sell_to_open(client, contract_symbol: str, qty: int = 1) -> str:
    """LIMIT order at the current bid (not market) — options market orders are
    rejected by Alpaca outside market hours, and limits avoid a bad fill on the
    wide bid/ask spreads options routinely have."""
    from alpaca.trading.requests import LimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    quote = latest_quote(contract_symbol)
    if not quote.bid_price:
        raise RuntimeError(f"{contract_symbol} has no live bid — can't set a limit price")
    order = client.submit_order(LimitOrderRequest(
        symbol=contract_symbol, qty=qty, side=OrderSide.SELL, time_in_force=TimeInForce.DAY,
        limit_price=round(float(quote.bid_price), 2),
    ))
    return str(order.id)


def sell_covered_call(client, underlying: str, spot: float, dte_target: int = 30,
                      otm_pct: float = 0.05):
    """Sells 1 call per 100 shares currently held. Caller must confirm shares
    are actually held — this module doesn't check position size."""
    target_strike = spot * (1 + otm_pct)
    contract = find_contract(client, underlying, "call", target_strike, dte_target)
    oid = sell_to_open(client, contract.symbol)
    return {"contract": contract.symbol, "strike": float(contract.strike_price),
            "expiration": str(contract.expiration_date), "order_id": oid}


def sell_cash_secured_put(client, underlying: str, spot: float, dte_target: int = 30,
                          otm_pct: float = 0.05):
    """Sells 1 put; caller is responsible for confirming cash covers strike*100."""
    target_strike = spot * (1 - otm_pct)
    contract = find_contract(client, underlying, "put", target_strike, dte_target)
    oid = sell_to_open(client, contract.symbol)
    return {"contract": contract.symbol, "strike": float(contract.strike_price),
            "expiration": str(contract.expiration_date), "order_id": oid}


def option_positions(client) -> list[dict]:
    return [{"symbol": p.symbol, "qty": float(p.qty), "market_value": float(p.market_value),
             "unrealized_pl": float(p.unrealized_pl)}
            for p in client.get_all_positions() if getattr(p, "asset_class", None) == "us_option"]


def wheel_step(client, symbol: str, dte: int = 30, otm_pct: float = 0.05) -> dict:
    """One live reconciliation/roll step of the wheel for `symbol`. Idempotent
    — call it daily; it no-ops unless there's actually something to do. State
    is persisted in Postgres via wheel_state so this picks up correctly across
    restarts and scheduler ticks.

    Never re-derives assignment from a price comparison — always asks Alpaca
    what's actually in the account. A tracked contract that vanished from
    positions is treated as "settled" (expired OTM, assigned, or exercised —
    which one doesn't matter, since the new leg is inferred purely from
    current share count, which handles early assignment for free).
    """
    import paper
    import risk
    import wheel_state

    state = wheel_state.get_state(symbol)

    # 1. An order was placed but not yet confirmed filled — check it, don't sell again.
    if state["pending_order_id"]:
        order = client.get_order_by_id(state["pending_order_id"])
        status = str(getattr(order, "status", ""))
        if "filled" in status.lower():
            wheel_state.set_state(symbol, state["state"], contract_symbol=state["contract_symbol"],
                                  pending_order_id=None, strike=state["strike"],
                                  expiration=state["expiration"])
            return {"symbol": symbol, "action": "CONFIRMED", "state": state["state"],
                    "contract": state["contract_symbol"]}
        if status.lower() in ("canceled", "expired", "rejected", "done_for_day"):
            wheel_state.set_state(symbol, state["state"])  # clear contract/order fields, retry next step
            return {"symbol": symbol, "action": "ORDER_FAILED", "detail": status,
                    "note": "cleared — will retry sell-to-open on the next step"}
        return {"symbol": symbol, "action": "PENDING", "detail": status,
                "contract": state["contract_symbol"]}

    # 2. A confirmed-open contract — has it settled (expired/assigned/exercised)?
    if state["contract_symbol"]:
        still_open = any(p["symbol"] == state["contract_symbol"] for p in option_positions(client))
        if still_open:
            return {"symbol": symbol, "action": "HOLD", "state": state["state"],
                    "contract": state["contract_symbol"]}
        shares = paper.position_qty(client, symbol)
        new_leg = "shares" if shares >= 100 else "cash"
        wheel_state.set_state(symbol, new_leg)
        return {"symbol": symbol, "action": "SETTLED", "new_state": new_leg,
                "detail": "contract left positions — inferred from live share count; "
                          "will sell the next leg on the following step"}

    # 3. Nothing open, nothing pending — sell the leg matching the current state.
    spot = float(engine.fetch(symbol, "2024-01-01")["Close"].iloc[-1])
    if state["state"] == "cash":
        target_strike = spot * (1 - otm_pct)
        ok, reason = risk.options_pre_trade_check(client, symbol, "cash", target_strike)
        if not ok:
            return {"symbol": symbol, "action": "BLOCKED", "detail": reason}
        result = sell_cash_secured_put(client, symbol, spot, dte, otm_pct)
    else:
        ok, reason = risk.options_pre_trade_check(client, symbol, "shares")
        if not ok:
            return {"symbol": symbol, "action": "BLOCKED", "detail": reason}
        result = sell_covered_call(client, symbol, spot, dte, otm_pct)

    wheel_state.set_state(symbol, state["state"], contract_symbol=result["contract"],
                          pending_order_id=result["order_id"], strike=result["strike"],
                          expiration=result["expiration"])
    return {"symbol": symbol, "action": "SELL_OPEN", "state": state["state"], **result}
