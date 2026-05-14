from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.memory.db import get_db
from backend.memory.schema import Task

router = APIRouter()


@router.get("/")
def get_tasks(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Task).order_by(desc(Task.created_at))
    if status:
        query = query.filter(Task.status == status)
    tasks = query.limit(100).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "agent": t.agent,
            "due_at": t.due_at,
            "created_at": t.created_at,
        }
        for t in tasks
    ]


@router.patch("/{task_id}/status")
def update_task_status(task_id: int, status: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = status
    db.commit()
    return {"id": task_id, "status": status}
