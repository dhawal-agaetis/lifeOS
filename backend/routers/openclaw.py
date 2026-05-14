import os
import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.memory.db import get_db

load_dotenv()

logger = logging.getLogger("openclaw")

router = APIRouter()

WEBHOOK_SECRET = os.getenv("OPENCLAW_WEBHOOK_SECRET", "")


class InboundMessage(BaseModel):
    sender: str
    content: str
    # OpenClaw passes a signature so we can verify authenticity
    signature: str | None = None


@router.post("/message")
async def receive_message(payload: InboundMessage, db: Session = Depends(get_db)):
    """Receive a WhatsApp message from OpenClaw, route via Albus, return response."""
    if WEBHOOK_SECRET and payload.signature:
        expected = hmac.new(
            WEBHOOK_SECRET.encode(),
            payload.content.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, payload.signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    logger.info(f"Incoming message from {payload.sender}: {payload.content}")

    from backend.agents.albus import run as albus_run
    response = albus_run(payload.content, db, source="whatsapp")

    return {"response": response}
