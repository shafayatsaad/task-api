"""
Task API — a small in-memory CRUD API built with FastAPI.

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
from pydantic import BaseModel, field_validator

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A small in-memory CRUD API for managing a to-do list.",
)

# ---------------------------------------------------------------------------
# "Database" — just a list in memory. Restart the server and it resets.
# ---------------------------------------------------------------------------
tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Walk the dog", "done": True},
    {"id": 3, "title": "Finish CRUD assignment", "done": False},
]
next_id = 4  # tracks the next free id to hand out


# ---------------------------------------------------------------------------
# Request/response models — FastAPI uses these for validation AND to build
# the OpenAPI spec that powers Swagger UI at /docs.
# ---------------------------------------------------------------------------
class TaskCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title must not be empty")
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_not_empty_if_present(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("title must not be empty")
        return v


# ---------------------------------------------------------------------------
# Stage 1 — root and health endpoints
# ---------------------------------------------------------------------------
@app.get("/", summary="API info")
def read_root():
    """Describes the API — the front door."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks", "/tasks/{id}", "/health", "/stats"],
    }


@app.get("/health", summary="Health check")
def health_check():
    """Used to confirm the server is alive."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Stage 2 — Read
# ---------------------------------------------------------------------------
@app.get("/tasks", summary="List tasks (optionally filter/search)")
def list_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    """
    Returns all tasks. Bonus query params:
    - done=true/false  -> only finished/unfinished tasks
    - search=word       -> only tasks whose title contains the word
    """
    result = tasks
    if done is not None:
        result = [t for t in result if t["done"] == done]
    if search:
        result = [t for t in result if search.lower() in t["title"].lower()]
    return result


@app.get("/tasks/{task_id}", summary="Get one task")
def get_task(task_id: int):
    for t in tasks:
        if t["id"] == task_id:
            return t
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


# ---------------------------------------------------------------------------
# Stage 3 — Create
# ---------------------------------------------------------------------------
@app.post("/tasks", status_code=201, summary="Create a task")
def create_task(task: TaskCreate):
    global next_id
    new_task = {"id": next_id, "title": task.title, "done": False}
    tasks.append(new_task)
    next_id += 1
    return new_task


# ---------------------------------------------------------------------------
# Stage 4 — Update & Delete
# ---------------------------------------------------------------------------
@app.put("/tasks/{task_id}", summary="Update a task")
def update_task(task_id: int, update: TaskUpdate):
    for t in tasks:
        if t["id"] == task_id:
            if update.title is not None:
                t["title"] = update.title
            if update.done is not None:
                t["done"] = update.done
            return t
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


# ---------------------------------------------------------------------------
# Bonus extras
# ---------------------------------------------------------------------------
@app.get("/stats", summary="Task stats")
def get_stats():
    total = len(tasks)
    done = len([t for t in tasks if t["done"]])
    return {"total": total, "done": done, "open": total - done}


@app.post("/reset", summary="Reset to the 3 example tasks")
def reset_tasks():
    global tasks, next_id
    tasks = [
        {"id": 1, "title": "Buy milk", "done": False},
        {"id": 2, "title": "Walk the dog", "done": True},
        {"id": 3, "title": "Finish CRUD assignment", "done": False},
    ]
    next_id = 4
    return {"message": "Tasks reset to the 3 example tasks"}


# ---------------------------------------------------------------------------
# Turn Pydantic validation errors into a clean 400 with a JSON error message,
# instead of FastAPI's default 422.
# ---------------------------------------------------------------------------
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    message = errors[0]["msg"] if errors else "Invalid request body"
    return JSONResponse(status_code=400, content={"error": message})
