"""Options overlays: Black-Scholes-approximated backtests + real Alpaca paper
execution against the live chain.

Two income strategies on top of an underlying's daily OHLC, plus a defined-risk
directional spread:
  covered_call      — hold shares, sell an OTM call every `dte` days (upside
                       capped at strike, premium collected, full downside)
  cash_secured_put  — hold cash, sell an OTM put every `dte` days (obligated to
                       buy at strike if breached, premium collected)
  bull_call_spread  — buy a near-the-money call + sell a further OTM call,
                       same expiry (defined max gain/loss; backtest-only for now)

Backtest pricing: Black-Scholes with REALIZED volatility (trailing `vol_window`
days) — there's no historical options chain wired up yet, so this estimates the
overlay's PAYOFF SHAPE (capped upside, premium income, downside profile), not
exact historical fills. Real premiums will differ from implied vol, skew, and
the actual bid/ask at the time. Treat results as directional, like the existing
Ollama /analyze summaries — a draft, not ground truth.

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
    sigma = _trailing_vol(close, window)
    default = float(sigma.dropna().median()) if sigma.notna().any() else 0.20
    return sigma.fillna(default)


def covered_call_backtest(df: pd.DataFrame, params: dict) -> pd.Series:
    dte = int(params.get("dte", 30))
    otm_pct = float(params.get("otm_pct", 0.05))
    vol_window = int(params.get("vol_window", 30))
    cost_bps = float(params.get("cost_bps", 5.0))
    initial = float(params.get("initial", 100_000.0))

    close = df["Close"]
    sigma = _sigma_series(close, vol_window)
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
    vol_window = int(params.get("vol_window", 30))
    cost_bps = float(params.get("cost_bps", 5.0))
    initial = float(params.get("initial", 100_000.0))

    close = df["Close"]
    sigma = _sigma_series(close, vol_window)
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
    vol_window = int(params.get("vol_window", 30))
    cost_bps = float(params.get("cost_bps", 5.0))
    initial = float(params.get("initial", 100_000.0))
    if otm_pct_short <= otm_pct_long:
        raise ValueError("otm_pct_short must exceed otm_pct_long (K2 > K1)")

    close = df["Close"]
    sigma = _sigma_series(close, vol_window)
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


def options_metrics(equity: pd.Series, dte: int) -> dict:
    """Same shape as engine.metrics() so _persist() needs no changes."""
    rf = engine.RISK_FREE_RATE
    rf_daily = (1 + rf) ** (1 / 252) - 1
    rets = equity.pct_change().fillna(0)
    peak = equity.cummax()
    max_dd = float(((equity - peak) / peak).min() * 100)
    sharpe = float((rets.mean() - rf_daily) / rets.std() * np.sqrt(252)) if rets.std() > 0 else 0.0
    period_rets = equity.iloc[::dte].pct_change().dropna()
    win_rate = float((period_rets > 0).sum() / max(len(period_rets), 1) * 100)
    return {
        "total_return_pct": round(float(equity.iloc[-1] / equity.iloc[0] - 1) * 100, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe": round(sharpe, 2),
        "trades": max(int(np.ceil(len(equity) / dte)), 1),
        "win_rate": round(win_rate, 1),
    }


OPTIONS_REGISTRY = {
    "covered_call": {"fn": covered_call_backtest,
                     "grid": {"otm_pct": [0.03, 0.05, 0.08], "dte": [21, 30, 45]}},
    "cash_secured_put": {"fn": cash_secured_put_backtest,
                         "grid": {"otm_pct": [0.03, 0.05, 0.08], "dte": [21, 30, 45]}},
    "bull_call_spread": {"fn": bull_call_spread_backtest,
                         "grid": {"otm_pct_short": [0.05, 0.08, 0.1], "dte": [21, 30, 45]}},
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
