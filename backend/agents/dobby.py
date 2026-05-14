import os
import logging
from anthropic import Anthropic
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from backend.memory.schema import AgentLog, Task

load_dotenv()

logger = logging.getLogger("dobby")

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are Dobby, a quick and efficient personal assistant in LifeOS.
You handle fast, simple tasks: reminders, quick answers, lookups, notes.
Be brief, accurate, and fast. No waffle."""


def run(task: str, db: Session) -> str:
    """Handle a quick task and return the result."""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": task}],
        )

        result = response.content[0].text

        _save_task(db, task, result)
        _log_agent(db, task, result, "success")

        return result

    except Exception as e:
        logger.error(f"Dobby error: {e}")
        _log_agent(db, task, str(e), "error")
        return f"Dobby couldn't complete the task: {e}"


def _save_task(db: Session, title: str, result: str):
    db.add(Task(title=title[:255], description=result, status="done", agent="dobby"))
    db.commit()


def _log_agent(db: Session, task: str, result: str, status: str):
    db.add(AgentLog(agent_name="dobby", task=task, result=result, status=status))
    db.commit()
