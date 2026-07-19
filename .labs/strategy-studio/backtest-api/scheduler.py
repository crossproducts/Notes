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
"""

import json
import os
import urllib.request

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

SYMBOLS = [s.strip() for s in os.getenv("STUDIO_SYMBOLS", "SPY,QQQ").split(",") if s.strip()]
PAPER_SYMBOL = os.getenv("STUDIO_PAPER_SYMBOL", "QQQ")
HEALTHCHECK_URL = os.getenv("HEALTHCHECK_URL", "")

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
    _scheduler.start()
    print(f"[scheduler] started: nightly 18:00, paper 09:35, monitor Fri 17:00 ({tz}); symbols={SYMBOLS}")
    return _scheduler


def jobs_status():
    if _scheduler is None:
        return {"enabled": False, "jobs": []}
    return {"enabled": True, "jobs": [
        {"id": j.id, "name": j.name,
         "next_run": str(j.next_run_time)} for j in _scheduler.get_jobs()]}
