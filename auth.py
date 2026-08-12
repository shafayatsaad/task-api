"""Supabase authentication helpers and reusable FastAPI auth dependency."""

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set in the environment. "
        "Copy .env.example to .env and fill them in."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# auto_error=False lets us return the assignment's exact JSON error instead
# of FastAPI's default 403 response when the Authorization header is missing.
bearer_scheme = HTTPBearer(auto_error=False)


def serialize_user(user: Any) -> dict:
    """Return only safe, useful user fields for API responses."""
    if user is None:
        return {}

    return {
        "id": getattr(user, "id", None),
        "email": getattr(user, "email", None),
        "created_at": getattr(user, "created_at", None),
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """Verify a Bearer JWT with Supabase and return the verified user."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"},
        )

    token = credentials.credentials

    try:
        response = supabase.auth.get_user(token)
        user = getattr(response, "user", None)
    except Exception:
        user = None

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"},
        )

    return user
