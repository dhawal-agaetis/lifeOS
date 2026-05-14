from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.memory.db import get_db
from backend.memory.schema import AgentLog

router = APIRouter()


@router.get("/logs")
def get_agent_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(AgentLog).order_by(desc(AgentLog.created_at)).limit(limit).all()
    return [
        {
            "id": log.id,
            "agent_name": log.agent_name,
            "task": log.task,
            "result": log.result,
            "status": log.status,
            "created_at": log.created_at,
        }
        for log in logs
    ]
