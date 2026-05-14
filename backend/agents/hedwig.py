import os
import json
import logging
from anthropic import Anthropic
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from backend.memory.schema import AgentLog, Email

load_dotenv()

logger = logging.getLogger("hedwig")

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are Hedwig, the email intelligence agent in LifeOS.
You process emails, extract key information, and flag important items.
For each email, identify:
- Is it an order confirmation? If so, extract: item, merchant, order number, total.
- Is it urgent or needs a reply?
- One-line summary.
Respond in JSON with keys: summary, is_order, order_details (or null), needs_reply."""


def run(task: str, db: Session) -> str:
    """Fetch unread emails, process them, return a digest."""
    try:
        from backend.tools.gmail import get_unread_emails
        emails = get_unread_emails(max_results=10)

        if not emails:
            _log_agent(db, task, "No unread emails.", "success")
            return "No unread emails."

        summaries = []
        for raw in emails:
            parsed = _parse_email(raw)
            _save_email(db, raw, parsed)
            summaries.append(f"• {raw['sender']}: {parsed.get('summary', raw['subject'])}")

        digest = f"Found {len(emails)} unread emails:\n" + "\n".join(summaries)
        _log_agent(db, task, digest, "success")
        return digest

    except Exception as e:
        logger.error(f"Hedwig error: {e}")
        _log_agent(db, task, str(e), "error")
        return f"Hedwig couldn't fetch emails: {e}"


def _parse_email(raw: dict) -> dict:
    """Use Claude to extract structured info from one email."""
    try:
        prompt = (
            f"Subject: {raw['subject']}\n"
            f"From: {raw['sender']}\n"
            f"Body preview: {raw['body_preview']}"
        )
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(response.content[0].text)
    except Exception:
        return {"summary": raw["subject"], "is_order": False, "order_details": None, "needs_reply": False}


def _save_email(db: Session, raw: dict, parsed: dict):
    existing = db.query(Email).filter(Email.gmail_id == raw["gmail_id"]).first()
    if existing:
        return
    db.add(Email(
        gmail_id=raw["gmail_id"],
        subject=raw["subject"],
        sender=raw["sender"],
        body_preview=raw["body_preview"],
        parsed_data=json.dumps(parsed),
        processed=True,
    ))
    db.commit()


def _log_agent(db: Session, task: str, result: str, status: str):
    db.add(AgentLog(agent_name="hedwig", task=task, result=result, status=status))
    db.commit()
