"""
Task API — a small SQLite-backed CRUD API built with FastAPI.

Run with:
    uvicorn main:app --reload

Then visit:
    http://localhost:8000/          -> API info
    http://localhost:8000/health    -> health check
    http://localhost:8000/docs      -> Swagger UI
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, field_validator

from database import initialize_database
import task_repository


app = FastAPI(
    title="Task API",
    version="1.0",
    description="A small SQLite-backed CRUD API for managing a to-do list.",
)


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

initialize_database()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_not_empty_if_present(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("title must not be empty")
        return v.strip() if v is not None else v


# ---------------------------------------------------------------------------
# Root and health endpoints
# ---------------------------------------------------------------------------

@app.get("/", summary="API info")
def read_root():
    """Describes the API — the front door."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": [
            "/tasks",
            "/tasks/{id}",
            "/health",
            "/stats",
        ],
    }


@app.get("/health", summary="Health check")
def health_check():
    """Used to confirm the server is alive."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

@app.get("/tasks", summary="List tasks (optionally filter/search)")
def list_tasks(
    done: Optional[bool] = None,
    search: Optional[str] = None,
):
    """
    Returns all tasks.

    Optional query parameters:
    - done=true/false -> only completed/unfinished tasks
    - search=word     -> tasks whose title contains the word
    """
    return task_repository.get_all_tasks(done=done, search=search)


@app.get("/tasks/{task_id}", summary="Get one task")
def get_task(task_id: int):
    task = task_repository.get_task(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found",
        )

    return task


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

@app.post("/tasks", status_code=201, summary="Create a task")
def create_task(task: TaskCreate):
    return task_repository.create_task(task.title)


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

@app.put("/tasks/{task_id}", summary="Update a task")
def update_task(task_id: int, update: TaskUpdate):
    task = task_repository.update_task(
        task_id,
        title=update.title,
        done=update.done,
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found",
        )

    return task


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    deleted = task_repository.delete_task(task_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found",
        )

    return None


# ---------------------------------------------------------------------------
# BONUS: Statistics
# ---------------------------------------------------------------------------

@app.get("/stats", summary="Task stats")
def get_stats():
    return task_repository.get_stats()


# ---------------------------------------------------------------------------
# BONUS: Reset
# ---------------------------------------------------------------------------

@app.post("/reset", summary="Reset to the 3 example tasks")
def reset_tasks():
    task_repository.reset_tasks()

    return {
        "message": "Tasks reset to the 3 example tasks"
    }


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    message = errors[0]["msg"] if errors else "Invalid request body"

    return JSONResponse(
        status_code=400,
        content={"error": message},
    )