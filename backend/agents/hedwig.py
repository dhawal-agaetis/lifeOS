import os
import json
import logging
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from backend.memory.schema import AgentLog, Email, Order, OrderCustomer, OrderItem
from backend.tools.order_parser import parse_order_email

load_dotenv()

logger = logging.getLogger("hedwig")

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Accounts to check on every run, in priority order
ALL_ACCOUNTS = ["houseofworktops", "agaetis", "personal"]

# Per-account system prompts — cached so each is only tokenised once per session
_PROMPTS = {
    "personal": """\
You are Hedwig processing a personal Gmail inbox (gmail.com).
Goal: general triage.
For each email respond in JSON:
{
  "summary": "one-line summary",
  "is_urgent": true/false,
  "needs_reply": true/false,
  "flag_to_albus": true/false,
  "flag_reason": "why flagged, or null",
  "is_order": false,
  "order_details": null
}""",

    "agaetis": """\
You are Hedwig processing a work inbox (agaetis.tech).
Goal: identify client/project emails, tag by project, flag deadlines and action items.
For each email respond in JSON:
{
  "summary": "one-line summary",
  "project": "project name or null",
  "has_deadline": true/false,
  "deadline_text": "e.g. 'by Friday' or null",
  "has_action_item": true/false,
  "action_item": "what needs doing or null",
  "needs_reply": true/false,
  "flag_to_albus": true/false,
  "flag_reason": "why flagged, or null",
  "is_order": false,
  "order_details": null
}""",

    "houseofworktops": """\
You are Hedwig processing the House of Worktops shop inbox (houseofworktops.co.uk).
This is the highest priority inbox.
For each email respond in JSON:
{
  "summary": "one-line summary",
  "is_order": true/false,
  "order_details": {
    "order_id": "order number or null",
    "customer_name": "full name or null",
    "customer_email": "email or null",
    "product": "product description or null",
    "amount": "numeric amount as string or null",
    "currency": "GBP",
    "order_date": "ISO date string or null"
  },
  "is_customer_query": true/false,
  "query_summary": "what the customer is asking or null",
  "needs_reply": true/false,
  "flag_to_albus": true/false,
  "flag_reason": "why flagged, or null"
}""",
}


def run(task: str, db: Session, accounts: list[str] | None = None) -> str:
    """
    Fetch and process emails for the given accounts (defaults to all three).
    Returns a digest with a separate section per inbox.
    """
    from backend.tools.gmail import get_unread_emails, is_authenticated

    targets = accounts or ALL_ACCOUNTS
    sections: list[str] = []
    total = 0

    for account in targets:
        if not is_authenticated(account):
            sections.append(f"*{_label(account)}*: not authenticated — run OAuth setup first.")
            continue

        try:
            emails = get_unread_emails(account, max_results=10)
        except Exception as e:
            logger.error(f"Hedwig fetch error ({account}): {e}")
            sections.append(f"*{_label(account)}*: fetch failed — {e}")
            continue

        if not emails:
            sections.append(f"*{_label(account)}*: no unread emails.")
            continue

        lines: list[str] = []
        for raw in emails:
            if account == "houseofworktops" and is_order_email(raw["subject"], raw["sender"]):
                parsed_order = parse_order_email(raw["subject"], raw.get("body", raw["body_preview"]), raw["gmail_id"])
                _save_order_atomic(db, parsed_order, account)
                _save_email(db, raw, {"is_order": True, "summary": f"Order {parsed_order['order']['order_id']}"}, account)
                lines.append(f"• {raw['sender']}: Order {parsed_order['order']['order_id']} — {parsed_order['order']['status']}")
            else:
                parsed = _parse_email(account, raw)
                _save_email(db, raw, parsed, account)
                lines.append(_format_line(account, raw, parsed))

        total += len(emails)
        header = f"*{_label(account)}* ({len(emails)} unread)"
        sections.append(header + "\n" + "\n".join(lines))

    digest = f"Email check — {total} unread across {len(targets)} inbox(es).\n\n" + "\n\n".join(sections)
    _log_agent(db, task, digest, "success")
    return digest


def _parse_email(account: str, raw: dict) -> dict:
    """Call Claude with the account-specific prompt to extract structured data."""
    try:
        prompt = (
            f"Subject: {raw['subject']}\n"
            f"From: {raw['sender']}\n"
            f"Body preview: {raw['body_preview']}"
        )
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=[
                {
                    "type": "text",
                    "text": _PROMPTS[account],
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(response.content[0].text)
    except Exception:
        return {
            "summary": raw["subject"],
            "is_order": False,
            "order_details": None,
            "needs_reply": False,
            "flag_to_albus": False,
        }


def _format_line(account: str, raw: dict, parsed: dict) -> str:
    parts = [f"• {raw['sender']}: {parsed.get('summary', raw['subject'])}"]
    if parsed.get("flag_to_albus"):
        parts.append(f"⚠ {parsed.get('flag_reason', 'flagged')}")
    if account == "agaetis":
        if parsed.get("project"):
            parts.append(f"[{parsed['project']}]")
        if parsed.get("has_deadline"):
            parts.append(f"📅 {parsed.get('deadline_text', 'deadline')}")
    if account == "houseofworktops":
        if parsed.get("is_order"):
            od = parsed.get("order_details") or {}
            parts.append(f"🛒 Order {od.get('order_id', '?')} — {od.get('product', '?')}")
        if parsed.get("is_customer_query"):
            parts.append(f"💬 {parsed.get('query_summary', 'customer query')}")
    return " | ".join(parts)


def _save_email(db: Session, raw: dict, parsed: dict, account: str):
    existing = db.query(Email).filter(Email.gmail_id == raw["gmail_id"]).first()
    if existing:
        return
    db.add(Email(
        gmail_id=raw["gmail_id"],
        account=account,
        subject=raw["subject"],
        sender=raw["sender"],
        body_preview=raw["body_preview"],
        parsed_data=json.dumps(parsed),
        processed=True,
    ))
    db.commit()


def is_order_email(subject: str, sender: str) -> bool:
    """True when the email looks like a HoW order confirmation from noreply."""
    is_order_subject = bool(
        subject and (
            "house of worktops - order" in subject.lower()
            or "house of worktops - sample order" in subject.lower()
        )
    )
    is_noreply = "noreply" in sender.lower()
    return is_order_subject and is_noreply


def _save_order_atomic(db: Session, parsed: dict, source_email: str):
    """Save order, customer, and items atomically. Skips if order_id already exists."""
    od = parsed.get("order") or {}
    order_id = od.get("order_id")
    if not order_id:
        logger.warning("Hedwig: skipping order with no order_id")
        return

    existing = db.query(Order).filter(Order.order_id == order_id).first()
    if existing:
        logger.info(f"Hedwig: order {order_id} already in DB — skipping")
        return

    try:
        order = Order(
            order_id=order_id,
            date_added=od.get("date_added"),
            status=od.get("status"),
            subtotal=od.get("subtotal"),
            vat=od.get("vat"),
            grand_total=od.get("grand_total"),
            comments=od.get("comments"),
            deliver_by=od.get("deliver_by"),
            is_business_customer=od.get("is_business_customer", False),
            raw_email_id=od.get("raw_email_id"),
            source_email=source_email,
        )
        db.add(order)

        cust = parsed.get("customer") or {}
        db.add(OrderCustomer(
            order_id=order_id,
            name=cust.get("name"),
            email=cust.get("email"),
            postcode=cust.get("postcode"),
            phone=cust.get("phone"),
        ))

        for item in parsed.get("items") or []:
            db.add(OrderItem(
                order_id=order_id,
                product_name=item.get("product_name"),
                product_sku=item.get("product_sku"),
                quantity=item.get("quantity"),
                unit_price=item.get("unit_price"),
                line_total=item.get("line_total"),
            ))

        db.commit()
        logger.info(f"Hedwig: saved order {order_id} — £{od.get('grand_total', 0)}")
        db.add(AgentLog(
            agent_name="hedwig",
            task=f"parse order {order_id}",
            result=f"order_id={order_id} grand_total={od.get('grand_total')}",
            status="success",
        ))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Hedwig: failed to save order {order_id}: {e}")


def _log_agent(db: Session, task: str, result: str, status: str):
    db.add(AgentLog(agent_name="hedwig", task=task, result=result, status=status))
    db.commit()


def _label(account: str) -> str:
    return {
        "personal": "Personal Gmail",
        "agaetis": "Work (agaetis.tech)",
        "houseofworktops": "Shop (houseofworktops.co.uk)",
    }.get(account, account)
