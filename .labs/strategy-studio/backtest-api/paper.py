"""Alpaca PAPER trading — champion-driven signal execution.

paper=True is HARDCODED. This module can never touch a live account; changing
that is a deliberate human decision, not a config flip.

Flow (what /paper/execute/{symbol} does):
  1. Look up the reigning champion for the symbol (champions table)
  2. Recompute that strategy's signal on the latest daily data
  3. Reconcile the paper position: signal 1 + flat -> buy (notional % of
     equity); signal 0 + long -> close; otherwise hold
  4. Log the action for audit (paper_actions table -> Grafana-able)
"""

import os
from datetime import datetime

def get_client():
    from alpaca.trading.client import TradingClient
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_SECRET_KEY")
    if not (key and secret):
        raise RuntimeError("set ALPACA_API_KEY / ALPACA_SECRET_KEY in .env")
    return TradingClient(key, secret, paper=True)  # paper only — by design


def account_summary(client) -> dict:
    a = client.get_account()
    return {
        "status": str(a.status),
        "equity": float(a.equity),
        "cash": float(a.cash),
        "buying_power": float(a.buying_power),
        "paper": True,
    }


def position_qty(client, symbol: str) -> float:
    try:
        p = client.get_open_position(symbol)
        return float(p.qty)
    except Exception:
        return 0.0


def pending_orders(client, symbol: str) -> int:
    """Open (queued/unfilled) orders for the symbol. Critical when the market is
    closed: a queued BUY means no position YET — without this check the daily
    run would happily stack duplicate orders."""
    from alpaca.trading.requests import GetOrdersRequest
    from alpaca.trading.enums import QueryOrderStatus
    orders = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN,
                                                symbols=[symbol]))
    return len(orders)


def buy_notional(client, symbol: str, dollars: float):
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    order = client.submit_order(MarketOrderRequest(
        symbol=symbol,
        notional=round(dollars, 2),
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
    ))
    return str(order.id)


def close_position(client, symbol: str):
    order = client.close_position(symbol)
    return str(getattr(order, "id", "closed"))
