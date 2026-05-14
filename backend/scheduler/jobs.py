import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("scheduler")

_scheduler = BackgroundScheduler()


def start_scheduler():
    if _scheduler.running:
        return

    _scheduler.add_job(
        _check_gmail,
        IntervalTrigger(minutes=30),
        id="hedwig_gmail_check",
        replace_existing=True,
    )

    _scheduler.add_job(
        _write_daily_summary,
        CronTrigger(hour=8, minute=0),
        id="daily_summary",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Scheduler started.")


def _check_gmail():
    """Scheduled Hedwig run — fetch and process unread emails."""
    try:
        from backend.memory.db import SessionLocal
        from backend.agents.hedwig import run as hedwig_run
        db = SessionLocal()
        try:
            result = hedwig_run("scheduled gmail check", db)
            logger.info(f"Hedwig scheduled run: {result}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Scheduled Gmail check failed: {e}")


def _write_daily_summary():
    """Scheduled daily summary — query DB and write to Obsidian vault."""
    try:
        from datetime import date
        from backend.memory.db import SessionLocal
        from backend.memory.schema import AgentLog, Task, Email
        from backend.obsidian_sync.writer import write_daily_note

        db = SessionLocal()
        try:
            today = date.today()

            recent_logs = db.query(AgentLog).order_by(AgentLog.created_at.desc()).limit(20).all()
            pending_tasks = db.query(Task).filter(Task.status == "pending").all()
            recent_emails = db.query(Email).filter(Email.processed == True).order_by(Email.created_at.desc()).limit(10).all()

            email_lines = "\n".join(f"- {e.sender}: {e.subject}" for e in recent_emails) or "No emails processed."
            task_lines = "\n".join(f"- [ ] {t.title}" for t in pending_tasks) or "No pending tasks."
            log_lines = "\n".join(f"- [{l.agent_name}] {l.task[:80]}" for l in recent_logs) or "No agent activity."

            write_daily_note(today, email_lines, task_lines, log_lines)
            logger.info(f"Daily summary written for {today}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Daily summary failed: {e}")
