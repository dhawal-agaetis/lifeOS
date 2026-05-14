import os
import logging
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("obsidian_sync")

VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "")

DAILY_NOTE_TEMPLATE = """\
# Daily Summary — {date}

## Emails
{email_summary}

## Tasks
{tasks_summary}

## Agent Activity
{agent_log_summary}
"""


def write_daily_note(
    note_date: date,
    email_summary: str,
    tasks_summary: str,
    agent_log_summary: str,
) -> Path:
    """Write a daily summary markdown file to the Obsidian vault."""
    if not VAULT_PATH:
        raise ValueError("OBSIDIAN_VAULT_PATH is not set in .env")

    vault = Path(VAULT_PATH)
    daily_dir = vault / "LifeOS" / "Daily"
    daily_dir.mkdir(parents=True, exist_ok=True)

    note_path = daily_dir / f"{note_date.isoformat()}.md"
    content = DAILY_NOTE_TEMPLATE.format(
        date=note_date.isoformat(),
        email_summary=email_summary,
        tasks_summary=tasks_summary,
        agent_log_summary=agent_log_summary,
    )

    note_path.write_text(content, encoding="utf-8")
    logger.info(f"Daily note written: {note_path}")
    return note_path
