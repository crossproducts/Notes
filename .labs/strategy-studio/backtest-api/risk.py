"""Live risk layer — pre-trade checks and kill switch.

Limits (read from env with sane defaults):
  RISK_MAX_DAILY_LOSS_PCT      default 3.0  — % drop of account equity vs last_equity
  RISK_MAX_OPEN_POSITIONS      default 5    — total open positions (new buys only)
  RISK_MAX_SYMBOL_EXPOSURE_PCT default 25.0 — market value of one symbol / equity

Kill switch persisted in Postgres (risk_state table) so state survives restarts.

pre_trade_check order:
  1. kill switch engaged
  2. daily loss breach
  3. max open positions (new positions only)
  4. per-symbol exposure cap
"""

import os

RISK_MAX_DAILY_LOSS_PCT = float(os.getenv("RISK_MAX_DAILY_LOSS_PCT", "3.0"))
RISK_MAX_OPEN_POSITIONS = int(os.getenv("RISK_MAX_OPEN_POSITIONS", "5"))
RISK_MAX_SYMBOL_EXPOSURE_PCT = float(os.getenv("RISK_MAX_SYMBOL_EXPOSURE_PCT", "25.0"))

_KILL_KEY = "kill_switch"


def _get_db():
    """Import db lazily to avoid circular imports at module load time."""
    import main
    return main.db


def is_killed() -> bool:
    """Return True if the kill switch is engaged (persisted in Postgres)."""
    from sqlalchemy import text
    db = _get_db()
    with db.connect() as conn:
        row = conn.execute(
            text("SELECT value FROM risk_state WHERE key = :k"), {"k": _KILL_KEY}
        ).fetchone()
    return row is not None and row[0] == "1"


def set_kill(engaged: bool) -> None:
    """Persist kill switch state in Postgres."""
    from sqlalchemy import text
    db = _get_db()
    with db.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO risk_state (key, value, updated) "
                "VALUES (:k, :v, now()) "
                "ON CONFLICT (key) DO UPDATE SET value=:v, updated=now()"
            ),
            {"k": _KILL_KEY, "v": "1" if engaged else "0"},
        )


def pre_trade_check(client, symbol: str, buy_notional_dollars: float) -> tuple[bool, str]:
    """Run pre-trade risk checks before submitting a BUY order.

    Args:
        client:               Alpaca TradingClient instance.
        symbol:               The equity/crypto symbol being bought.
        buy_notional_dollars: Dollar notional of the proposed BUY.

    Returns:
        (ok, reason) — ok=True means the trade is allowed, ok=False means blocked.

    Check order (first failure blocks):
      1. Kill switch engaged
      2. Daily loss breach (equity vs last_equity from Alpaca account)
      3. Max open positions (only blocks NEW positions — symbol not currently held)
      4. Per-symbol exposure cap (existing market value + proposed notional vs equity)
    """
    # 1. Kill switch
    if is_killed():
        return False, "kill switch engaged"

    # Fetch account once — needed for checks 2, 3, 4
    acct = client.get_account()
    equity = float(acct.equity)
    last_equity = float(acct.last_equity)

    # 2. Daily loss breach
    if last_equity > 0:
        daily_loss_pct = (last_equity - equity) / last_equity * 100.0
        if daily_loss_pct >= RISK_MAX_DAILY_LOSS_PCT:
            return False, (
                f"daily loss {daily_loss_pct:.2f}% >= limit {RISK_MAX_DAILY_LOSS_PCT}%"
            )

    # 3. Max open positions (only for NEW positions — if already holding, skip)
    import paper as _paper
    current_qty = _paper.position_qty(client, symbol)
    is_new_position = current_qty == 0.0

    if is_new_position:
        positions = client.get_all_positions()
        open_count = len(positions)
        if open_count >= RISK_MAX_OPEN_POSITIONS:
            return False, (
                f"open positions {open_count} >= limit {RISK_MAX_OPEN_POSITIONS}"
            )

    # 4. Per-symbol exposure cap
    # existing market value of this symbol
    existing_mv = 0.0
    try:
        pos = client.get_open_position(_paper.alpaca_symbol(symbol))
        existing_mv = float(pos.market_value)
    except Exception:
        existing_mv = 0.0

    proposed_total = existing_mv + buy_notional_dollars
    if equity > 0:
        exposure_pct = proposed_total / equity * 100.0
        if exposure_pct > RISK_MAX_SYMBOL_EXPOSURE_PCT:
            return False, (
                f"symbol exposure {exposure_pct:.2f}% would exceed limit "
                f"{RISK_MAX_SYMBOL_EXPOSURE_PCT}% "
                f"(existing ${existing_mv:.0f} + proposed ${buy_notional_dollars:.0f})"
            )

    return True, "ok"


def live_readings(client) -> dict:
    """Return current risk readings; degrade gracefully if Alpaca is unreachable."""
    try:
        acct = client.get_account()
        equity = float(acct.equity)
        last_equity = float(acct.last_equity)

        daily_loss_pct = (
            (last_equity - equity) / last_equity * 100.0 if last_equity > 0 else 0.0
        )

        positions = client.get_all_positions()
        open_position_count = len(positions)

        per_symbol = {}
        for pos in positions:
            mv = float(pos.market_value)
            pct = mv / equity * 100.0 if equity > 0 else 0.0
            per_symbol[pos.symbol] = round(pct, 2)

        return {
            "available": True,
            "equity": equity,
            "last_equity": last_equity,
            "daily_loss_pct": round(daily_loss_pct, 3),
            "open_position_count": open_position_count,
            "per_symbol_exposure_pct": per_symbol,
        }
    except Exception as e:
        return {"available": False, "error": str(e)}
