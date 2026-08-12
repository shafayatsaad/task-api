"""
Task API — PostgreSQL CRUD API with Supabase authentication.

Run with:
    uvicorn main:app --reload

Then visit:
    http://localhost:8000/          -> API info
    http://localhost:8000/health    -> health check
    http://localhost:8000/docs      -> Swagger UI
"""

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, field_validator

from auth import get_current_user, serialize_user, supabase
from database import initialize_database
import task_repository


app = FastAPI(
    title="Task API — Auth & Protect",
    version="2.0",
    description=(
        "A PostgreSQL-backed CRUD API secured with Supabase Auth. "
        "Protected routes verify Bearer JWTs with Supabase."
    ),
)


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

initialize_database()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class AuthRequest(BaseModel):
    email: str
    password: str

    @field_validator("email", "password")
    @classmethod
    def required_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("email and password are required")
        return value.strip()


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
    return {
        "name": "Task API — Auth & Protect",
        "version": "2.0",
        "endpoints": [
            "/auth/signup",
            "/auth/login",
            "/auth/logout",
            "/public/info",
            "/protected/profile",
            "/protected/dashboard",
            "/tasks",
            "/tasks/{id}",
            "/health",
            "/stats",
        ],
    }


@app.get("/health", summary="Health check")
def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Stage 1 — Authentication
# ---------------------------------------------------------------------------

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED, summary="Create a user")
def signup(payload: AuthRequest):
    try:
        response = supabase.auth.sign_up(
            {
                "email": payload.email,
                "password": payload.password,
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(getattr(exc, "message", exc))},
        ) from exc

    user = getattr(response, "user", None)
    session = getattr(response, "session", None)

    return {
        "user": serialize_user(user),
        "session": {
            "access_token": getattr(session, "access_token", None),
            "refresh_token": getattr(session, "refresh_token", None),
        }
        if session
        else None,
        "message": (
            "Account created. Check your email to confirm the account."
            if session is None
            else "Account created and signed in."
        ),
    }


@app.post("/auth/login", summary="Log in and receive JWT")
def login(payload: AuthRequest):
    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": payload.email,
                "password": payload.password,
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid login credentials"},
        ) from exc

    session = getattr(response, "session", None)
    user = getattr(response, "user", None)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid login credentials"},
        )

    return {
        "user": serialize_user(user),
        "access_token": getattr(session, "access_token", None),
        "refresh_token": getattr(session, "refresh_token", None),
        "token_type": "bearer",
    }


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Log out")
def logout(current_user=Depends(get_current_user)):
    """Sign out the authenticated Supabase session.

    The access token is verified first by get_current_user. Supabase access
    JWTs remain valid until expiry even after sign-out; sign-out revokes the
    refresh-token/session state. The client must discard its local tokens.
    """
    try:
        # Supabase's Python SDK sign_out() operates on the client's current
        # session. The endpoint is still protected by the submitted JWT.
        supabase.auth.sign_out()
    except Exception:
        # The authenticated request is still a valid logout request even when
        # this server-side client has no persistent local session to clear.
        pass

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Stage 2/3 — Public & protected routes
# ---------------------------------------------------------------------------

@app.get("/public/info", summary="Public information")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile", summary="Read authenticated profile")
def protected_profile(current_user=Depends(get_current_user)):
    return {
        "id": getattr(current_user, "id", None),
        "email": getattr(current_user, "email", None),
        "created_at": getattr(current_user, "created_at", None),
    }


@app.get("/protected/dashboard", summary="Protected dashboard")
def protected_dashboard(current_user=Depends(get_current_user)):
    return {
        "message": "Welcome to the protected dashboard.",
        "user": serialize_user(current_user),
    }


# ---------------------------------------------------------------------------
# Existing CRUD API
# ---------------------------------------------------------------------------

@app.get("/tasks", summary="List tasks (optionally filter/search)")
def list_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    return task_repository.get_all_tasks(done=done, search=search)


@app.get("/tasks/{task_id}", summary="Get one task")
def get_task(task_id: int):
    task = task_repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.post("/tasks", status_code=201, summary="Create a task")
def create_task(task: TaskCreate):
    return task_repository.create_task(task.title)


@app.put("/tasks/{task_id}", summary="Update a task")
def update_task(task_id: int, update: TaskUpdate):
    task = task_repository.update_task(task_id, title=update.title, done=update.done)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    deleted = task_repository.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return None


@app.get("/stats", summary="Task stats")
def get_stats():
    return task_repository.get_stats()


@app.post("/reset", summary="Reset to the 3 example tasks")
def reset_tasks():
    task_repository.reset_tasks()
    return {"message": "Tasks reset to the 3 example tasks"}


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    message = errors[0]["msg"] if errors else "Invalid request body"
    return JSONResponse(status_code=400, content={"error": message})
