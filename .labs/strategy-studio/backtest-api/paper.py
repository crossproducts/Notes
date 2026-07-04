"""Alpaca PAPER trading — champion-driven signal execution.

paper=True is HARDCODED. This module can never touch a live account; changing
that is a deliberate human decision, not a config flip.

Supports equities AND crypto (both live on Alpaca). Crypto quirks handled here:
  - symbol format: strategies/yfinance use 'BTC-USD', Alpaca orders use 'BTC/USD'
  - time-in-force: crypto rejects DAY, needs GTC
  - crypto trades 24/7, so a paper order actually fills any time (equities queue)

Flow (/paper/execute/{symbol}): look up the champion, recompute today's signal,
reconcile the paper position (buy notional % / close / hold), log for audit.
"""

import os


def is_crypto(symbol: str) -> bool:
    s = symbol.upper()
    return s.endswith("-USD") or "/" in s


def alpaca_symbol(symbol: str) -> str:
    """yfinance 'BTC-USD' -> Alpaca order symbol 'BTC/USD'. Equities unchanged."""
    if symbol.upper().endswith("-USD"):
        return symbol.upper().replace("-USD", "/USD")
    return symbol


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
    # Alpaca crypto positions may key on 'BTC/USD' or 'BTCUSD' depending on version
    for candidate in {alpaca_symbol(symbol), alpaca_symbol(symbol).replace("/", ""), symbol}:
        try:
            return float(client.get_open_position(candidate).qty)
        except Exception:
            continue
    return 0.0


def pending_orders(client, symbol: str) -> int:
    """Open (unfilled) orders — a queued BUY isn't a position yet; without this
    check the daily run would stack duplicates while an order sits unfilled."""
    from alpaca.trading.requests import GetOrdersRequest
    from alpaca.trading.enums import QueryOrderStatus
    orders = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN,
                                                symbols=[alpaca_symbol(symbol)]))
    return len(orders)


def buy_notional(client, symbol: str, dollars: float):
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    tif = TimeInForce.GTC if is_crypto(symbol) else TimeInForce.DAY  # crypto rejects DAY
    order = client.submit_order(MarketOrderRequest(
        symbol=alpaca_symbol(symbol),
        notional=round(dollars, 2),
        side=OrderSide.BUY,
        time_in_force=tif,
    ))
    return str(order.id)


def close_position(client, symbol: str):
    for candidate in [alpaca_symbol(symbol), alpaca_symbol(symbol).replace("/", "")]:
        try:
            order = client.close_position(candidate)
            return str(getattr(order, "id", "closed"))
        except Exception:
            continue
    return "close_failed"
