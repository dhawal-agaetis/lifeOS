from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.memory.db import get_db
from backend.memory.schema import Email

router = APIRouter()


@router.get("/")
def get_emails(processed: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(Email).order_by(desc(Email.created_at))
    if processed is not None:
        query = query.filter(Email.processed == processed)
    emails = query.limit(50).all()
    return [
        {
            "id": e.id,
            "gmail_id": e.gmail_id,
            "subject": e.subject,
            "sender": e.sender,
            "body_preview": e.body_preview,
            "parsed_data": e.parsed_data,
            "processed": e.processed,
            "created_at": e.created_at,
        }
        for e in emails
    ]
