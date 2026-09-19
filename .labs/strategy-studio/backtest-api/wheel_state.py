"""Persisted live state for the options wheel — which leg (cash/shares) each
symbol is currently on, and the currently-open contract (if any), including
an order placed but not yet confirmed filled. Lets the scheduler job pick up
exactly where it left off across restarts. Same lazy-db-import pattern as
risk.py's kill switch, to avoid a circular import with main.py at load time.
"""

from sqlalchemy import text


def _get_db():
    import main
    return main.db


def get_state(symbol: str) -> dict:
    db = _get_db()
    with db.connect() as conn:
        row = conn.execute(
            text("SELECT state, contract_symbol, pending_order_id, strike, expiration "
                 "FROM options_wheel_state WHERE symbol = :s"), {"s": symbol}
        ).fetchone()
    if row is None:
        return {"symbol": symbol, "state": "cash", "contract_symbol": None,
                "pending_order_id": None, "strike": None, "expiration": None}
    return {"symbol": symbol, "state": row[0], "contract_symbol": row[1],
            "pending_order_id": row[2], "strike": row[3],
            "expiration": str(row[4]) if row[4] else None}


def set_state(symbol: str, state: str, contract_symbol: str | None = None,
             pending_order_id: str | None = None, strike: float | None = None,
             expiration: str | None = None) -> None:
    """Full replace of a symbol's wheel state — pass only `state` to clear the
    contract/order fields (e.g. after a settlement), or all fields together
    when opening a new leg."""
    db = _get_db()
    with db.begin() as conn:
        conn.execute(text(
            "INSERT INTO options_wheel_state "
            "(symbol, state, contract_symbol, pending_order_id, strike, expiration, opened, updated) "
            "VALUES (:s, :st, :c, :p, :k, :e, now(), now()) "
            "ON CONFLICT (symbol) DO UPDATE SET state=:st, contract_symbol=:c, "
            "pending_order_id=:p, strike=:k, expiration=:e, updated=now()"),
            {"s": symbol, "st": state, "c": contract_symbol, "p": pending_order_id,
             "k": strike, "e": expiration})
