"""Tasks API — therapy homework management"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.models.task import TherapyTask

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    task_type: str
    difficulty: int
    status: str
    reflection: str | None = None

    class Config:
        from_attributes = True


class CompleteTaskRequest(BaseModel):
    reflection: str = ""
    difficulty_rating: int | None = None
    usefulness_rating: int | None = None


@router.get("")
async def list_tasks(
    user_id: int,
    status: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    """List tasks, optionally filtered by status."""
    query = select(TherapyTask).where(TherapyTask.user_id == user_id)
    if status:
        query = query.where(TherapyTask.status == status)
    query = query.order_by(TherapyTask.created_at.desc())

    result = await db.execute(query)
    tasks = result.scalars().all()
    return [
        TaskResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            task_type=t.task_type,
            difficulty=t.difficulty,
            status=t.status,
            reflection=t.reflection,
        )
        for t in tasks
    ]


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: int,
    req: CompleteTaskRequest,
    db: AsyncSession = Depends(get_session),
):
    """Mark a task as completed with reflection."""
    result = await db.execute(select(TherapyTask).where(TherapyTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")

    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc)
    task.reflection = req.reflection
    task.difficulty_rating = req.difficulty_rating
    task.usefulness_rating = req.usefulness_rating
    await db.flush()

    return {"status": "completed", "task_id": task_id}


@router.post("/{task_id}/skip")
async def skip_task(task_id: int, db: AsyncSession = Depends(get_session)):
    """Skip a task."""
    result = await db.execute(select(TherapyTask).where(TherapyTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")

    task.status = "skipped"
    await db.flush()
    return {"status": "skipped", "task_id": task_id}
