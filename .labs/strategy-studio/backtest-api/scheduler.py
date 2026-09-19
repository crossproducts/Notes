"""In-process scheduler — replaces the n8n workflows with two cron jobs.

Jobs (America/New_York, weekdays):
  18:00  nightly champion: sweep strategies per symbol, auto-promote (OOS-gated),
         SMS the summary
  09:35  paper execute: reconcile the champion's signal into the Alpaca paper
         account, SMS the action

Reliability contract (what n8n never gave us):
  - every job is wrapped: an exception -> SMS with [ERROR], not silence
  - after a successful nightly, optionally GET $HEALTHCHECK_URL (healthchecks.io
    dead-man switch: if the ping stops arriving, YOU get told, even if the whole
    box died)

Env: STUDIO_SCHEDULER=on|off (default on), STUDIO_SYMBOLS=SPY,QQQ,
     STUDIO_PAPER_SYMBOL=QQQ, HEALTHCHECK_URL (optional)

Options wheel (opt-in — see job_options_wheel):
  STUDIO_OPTIONS_WHEEL_ENABLED=on|off (default off — run a few manually-
    triggered `/paper/options/wheel/{symbol}/step` calls first)
  STUDIO_OPTIONS_WHEEL_SYMBOL   (default STUDIO_PAPER_SYMBOL)
  STUDIO_OPTIONS_WHEEL_DTE      (default 30)
  STUDIO_OPTIONS_WHEEL_OTM_PCT  (default 0.05)
"""

import json
import os
import urllib.request

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

SYMBOLS = [s.strip() for s in os.getenv("STUDIO_SYMBOLS", "SPY,QQQ").split(",") if s.strip()]
PAPER_SYMBOL = os.getenv("STUDIO_PAPER_SYMBOL", "QQQ")
HEALTHCHECK_URL = os.getenv("HEALTHCHECK_URL", "")

OPTIONS_WHEEL_ENABLED = os.getenv("STUDIO_OPTIONS_WHEEL_ENABLED", "off").lower() in ("on", "true", "1")
OPTIONS_WHEEL_SYMBOL = os.getenv("STUDIO_OPTIONS_WHEEL_SYMBOL", PAPER_SYMBOL)
OPTIONS_WHEEL_DTE = int(os.getenv("STUDIO_OPTIONS_WHEEL_DTE", "30"))
OPTIONS_WHEEL_OTM_PCT = float(os.getenv("STUDIO_OPTIONS_WHEEL_OTM_PCT", "0.05"))

_scheduler: BackgroundScheduler | None = None


def _ping_healthcheck():
    if HEALTHCHECK_URL:
        try:
            urllib.request.urlopen(HEALTHCHECK_URL, timeout=10)
        except Exception:
            pass  # the ping is the alarm; never let it break the job


def _safe(job_name: str, fn):
    """Run a job; on failure send an [ERROR] SMS instead of dying silently."""
    import main
    try:
        fn()
    except Exception as e:
        try:
            main.notify(main.NotifyRequest(text=f"[studio][ERROR] {job_name}: {str(e)[:200]}"))
        except Exception:
            print(f"[scheduler] {job_name} failed AND notify failed: {e}")


def job_nightly():
    import main
    def work():
        lines = []
        for sym in SYMBOLS:
            r = main.nightly(sym)
            lines.append(r["summary"])
        main.notify(main.NotifyRequest(text=" | ".join(lines)[:300]))
        _ping_healthcheck()
    _safe("nightly", work)


def job_paper():
    import main
    def work():
        r = main.paper_execute(PAPER_SYMBOL)
        # notify on blocked/kill outcomes so they are never silent
        if r.get("blocked"):
            main.notify(main.NotifyRequest(
                text=f"[paper][BLOCKED] {r['symbol']} {r['action']}: {r['detail']} "
                     f"({r['champion_strategy']}, signal {r['signal_today']})"))
        else:
            main.notify(main.NotifyRequest(
                text=f"[paper] {r['symbol']} {r['action']} ({r['champion_strategy']}, "
                     f"signal {r['signal_today']}) equity ${r['account_equity']}"))
    _safe("paper", work)


def job_monitor():
    """Weekly decay check on every champion — SMS ONLY if something degraded,
    so silence means healthy (no alert fatigue)."""
    import main, monitor
    def work():
        decayed = []
        for sym in SYMBOLS:
            try:
                champ = main.get_champion(sym)
            except Exception:
                continue
            params = champ.get("params") or {}
            if isinstance(params, str):
                params = json.loads(params)
            m = monitor.monitor(champ["strategy"], sym, params)
            if m.get("verdict") == "DECAY":
                decayed.append(f"{sym}/{m['strategy']}: {'; '.join(m['flags'])}")
        if decayed:
            main.notify(main.NotifyRequest(text=("[studio][DECAY] " + " | ".join(decayed))[:300]))
    _safe("monitor", work)


def job_options_wheel():
    """Daily wheel reconciliation/roll step — idempotent, no-ops (HOLD/PENDING)
    unless there's actually something to do. Opt-in via
    STUDIO_OPTIONS_WHEEL_ENABLED: unlike the equity paper trade, this should
    get a few manually-triggered `/paper/options/wheel/{symbol}/step` cycles
    watched by hand before trusting it to the scheduler."""
    import main
    def work():
        r = main.paper_options_wheel_step(OPTIONS_WHEEL_SYMBOL, OPTIONS_WHEEL_DTE, OPTIONS_WHEEL_OTM_PCT)
        if r["action"] in ("BLOCKED", "ORDER_FAILED"):
            main.notify(main.NotifyRequest(
                text=f"[wheel][{r['action']}] {r['symbol']}: {r.get('detail', '')}"))
        elif r["action"] in ("SELL_OPEN", "SETTLED", "CONFIRMED"):
            main.notify(main.NotifyRequest(
                text=f"[wheel] {r['symbol']} {r['action']}: "
                     f"{r.get('contract', r.get('new_state', ''))}"))
        # HOLD/PENDING: no alert — same alert-fatigue reasoning as job_monitor
    _safe("options_wheel", work)


def start():
    global _scheduler
    if os.getenv("STUDIO_SCHEDULER", "on").lower() not in ("on", "true", "1"):
        print("[scheduler] disabled via STUDIO_SCHEDULER")
        return None
    tz = "America/New_York"
    _scheduler = BackgroundScheduler(timezone=tz)
    _scheduler.add_job(job_nightly, CronTrigger(day_of_week="mon-fri", hour=18, minute=0, timezone=tz),
                       id="nightly_champion", name="Nightly champion sweep + SMS")
    _scheduler.add_job(job_paper, CronTrigger(day_of_week="mon-fri", hour=9, minute=35, timezone=tz),
                       id="paper_execute", name=f"Paper trade {PAPER_SYMBOL} champion + SMS")
    _scheduler.add_job(job_monitor, CronTrigger(day_of_week="fri", hour=17, minute=0, timezone=tz),
                       id="decay_monitor", name="Weekly champion decay check (SMS on decay only)")
    wheel_msg = "disabled"
    if OPTIONS_WHEEL_ENABLED:
        _scheduler.add_job(job_options_wheel, CronTrigger(day_of_week="mon-fri", hour=9, minute=40, timezone=tz),
                           id="options_wheel", name=f"Options wheel {OPTIONS_WHEEL_SYMBOL} step + SMS")
        wheel_msg = f"{OPTIONS_WHEEL_SYMBOL} daily @ 09:40"
    _scheduler.start()
    print(f"[scheduler] started: nightly 18:00, paper 09:35, monitor Fri 17:00 ({tz}); "
         f"symbols={SYMBOLS}; options wheel: {wheel_msg}")
    return _scheduler


def jobs_status():
    if _scheduler is None:
        return {"enabled": False, "jobs": []}
    return {"enabled": True, "jobs": [
        {"id": j.id, "name": j.name,
         "next_run": str(j.next_run_time)} for j in _scheduler.get_jobs()]}
