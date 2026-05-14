import os
import logging
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from backend.memory.schema import AgentLog, Message

load_dotenv()

logger = logging.getLogger("albus")

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are Albus, the orchestrating intelligence of LifeOS — a personal operating system.
You have a top-level view of the user's life across all domains.
Your job is to understand what the user needs and route them to the right specialist agent, or handle simple responses yourself.

Available agents:
- Dobby: quick tasks, reminders, simple lookups, fast answers
- Hedwig: anything related to email, Gmail, orders, inbox

If you can answer simply and quickly yourself, do so.
If the task needs a specialist, respond with: ROUTE:<agent_name>:<task>
Always be wise, warm, and concise."""


def run(message: str, db: Session, source: str = "whatsapp") -> str:
    """Receive a message, decide routing, return a response."""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    # Cache the system prompt — it's large and static
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": message}],
        )

        reply = response.content[0].text
        agent_routed_to = "albus"
        final_reply = reply

        if reply.startswith("ROUTE:"):
            # ROUTE:<agent_name>:<task>
            parts = reply.split(":", 2)
            if len(parts) == 3:
                agent_name = parts[1].strip().lower()
                task = parts[2].strip()
                agent_routed_to = agent_name
                final_reply = _dispatch(agent_name, task, db)

        _log_message(db, source, message, agent_routed_to, final_reply)
        _log_agent(db, "albus", message, final_reply, "success")

        return final_reply

    except Exception as e:
        logger.error(f"Albus error: {e}")
        _log_agent(db, "albus", message, str(e), "error")
        return "Something went wrong. Please try again."


def _dispatch(agent_name: str, task: str, db: Session) -> str:
    if agent_name == "dobby":
        from backend.agents.dobby import run as dobby_run
        return dobby_run(task, db)
    elif agent_name == "hedwig":
        from backend.agents.hedwig import run as hedwig_run
        return hedwig_run(task, db)
    else:
        return f"Unknown agent: {agent_name}"


def _log_message(db: Session, source: str, content: str, agent: str, response: str):
    db.add(Message(source=source, content=content, agent_routed_to=agent, response=response))
    db.commit()


def _log_agent(db: Session, agent: str, task: str, result: str, status: str):
    db.add(AgentLog(agent_name=agent, task=task, result=result, status=status))
    db.commit()
