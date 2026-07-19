"""Task persistence endpoints: CRUD, bulk save, CSV export."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.task import (
    BulkSaveRequest,
    BulkSaveResponse,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from app.services import task_service

router = APIRouter()


def _get_or_404(db: Session, task_id: str):
    task = task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(db: Session = Depends(get_db)) -> list:
    return task_service.list_tasks(db)


@router.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    added = task_service.save_task(db, payload)
    db.commit()
    if not added:
        raise HTTPException(status_code=409, detail="Task already exists")
    # Return the most recently created matching task.
    tasks = task_service.list_tasks(db)
    return tasks[0]


@router.post("/tasks/bulk", response_model=BulkSaveResponse)
def bulk_save(payload: BulkSaveRequest, db: Session = Depends(get_db)) -> BulkSaveResponse:
    added, skipped = task_service.save_many(db, payload.tasks)
    return BulkSaveResponse(added=added, skipped=skipped)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = _get_or_404(db, task_id)
    return task_service.update_task(db, task, payload.model_dump(exclude_none=True))


@router.post("/tasks/{task_id}/toggle", response_model=TaskRead)
def toggle_task(task_id: str, db: Session = Depends(get_db)):
    task = _get_or_404(db, task_id)
    return task_service.toggle_status(db, task)


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)) -> Response:
    task = _get_or_404(db, task_id)
    task_service.delete_task(db, task)
    return Response(status_code=204)


@router.get("/tasks/export.csv")
def export_csv(db: Session = Depends(get_db)) -> Response:
    tasks = task_service.list_tasks(db)
    csv_text = task_service.tasks_to_csv(tasks, include_status=True)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inboxiq_tasks.csv"},
    )
