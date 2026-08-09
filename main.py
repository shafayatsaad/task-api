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

from database import get_connection, initialize_database, row_to_task


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

    connection = get_connection()

    query = "SELECT id, title, done FROM tasks"
    conditions = []
    parameters = []

    if done is not None:
        conditions.append("done = ?")
        parameters.append(int(done))

    if search:
        conditions.append("LOWER(title) LIKE LOWER(?)")
        parameters.append(f"%{search}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id"

    rows = connection.execute(query, parameters).fetchall()

    connection.close()

    return [row_to_task(row) for row in rows]


@app.get("/tasks/{task_id}", summary="Get one task")
def get_task(task_id: int):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT id, title, done
        FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    ).fetchone()

    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found",
        )

    return row_to_task(row)


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

@app.post("/tasks", status_code=201, summary="Create a task")
def create_task(task: TaskCreate):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO tasks (title, done)
        VALUES (?, ?)
        """,
        (task.title, False),
    )

    connection.commit()

    new_id = cursor.lastrowid

    row = connection.execute(
        """
        SELECT id, title, done
        FROM tasks
        WHERE id = ?
        """,
        (new_id,),
    ).fetchone()

    connection.close()

    return row_to_task(row)


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

@app.put("/tasks/{task_id}", summary="Update a task")
def update_task(task_id: int, update: TaskUpdate):
    connection = get_connection()

    existing = connection.execute(
        """
        SELECT id, title, done
        FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    ).fetchone()

    if existing is None:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found",
        )

    # Build the UPDATE dynamically, but only from known column names.
    fields = []
    parameters = []

    if update.title is not None:
        fields.append("title = ?")
        parameters.append(update.title)

    if update.done is not None:
        fields.append("done = ?")
        parameters.append(int(update.done))

    # If the request contains no fields, return the existing task.
    if fields:
        parameters.append(task_id)

        query = f"""
            UPDATE tasks
            SET {", ".join(fields)}
            WHERE id = ?
        """

        connection.execute(query, parameters)
        connection.commit()

    row = connection.execute(
        """
        SELECT id, title, done
        FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    ).fetchone()

    connection.close()

    return row_to_task(row)


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    connection = get_connection()

    cursor = connection.execute(
        """
        DELETE FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    )

    connection.commit()

    deleted = cursor.rowcount

    connection.close()

    if deleted == 0:
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
    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN done = 1 THEN 1 ELSE 0 END), 0) AS done
        FROM tasks
        """
    ).fetchone()

    connection.close()

    total = row["total"]
    done = row["done"]

    return {
        "total": total,
        "done": done,
        "open": total - done,
    }


# ---------------------------------------------------------------------------
# BONUS: Reset
# ---------------------------------------------------------------------------

@app.post("/reset", summary="Reset to the 3 example tasks")
def reset_tasks():
    connection = get_connection()

    connection.execute("DELETE FROM tasks")

    connection.executemany(
        """
        INSERT INTO tasks (title, done)
        VALUES (?, ?)
        """,
        [
            ("Buy milk", False),
            ("Walk the dog", True),
            ("Finish CRUD assignment", False),
        ],
    )

    connection.commit()

    connection.close()

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