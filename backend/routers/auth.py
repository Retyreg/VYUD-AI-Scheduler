"""Auth router — login, register, current user via Supabase Auth API.

Supabase auth is called directly (no SDK) to stay compatible with Python 3.10 asyncio.
Endpoints:
  POST /api/auth/login       — email + password → JWT access_token
  POST /api/auth/register    — email + password → creates user + JWT
  GET  /api/auth/me          — returns current user from JWT (Bearer header)
"""

import logging
import os

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # anon key is fine for auth endpoints


def _anon_headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
    }


class AuthRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(body: AuthRequest):
    """Sign in with email + password. Returns access_token for localStorage."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers=_anon_headers(),
            json={"email": body.email, "password": body.password},
            timeout=15,
        )

    if resp.status_code == 400:
        try:
            data = resp.json()
        except Exception:
            data = {}
        # Supabase returns {"error": "...", "error_description": "..."}
        msg = data.get("error_description") or data.get("error") or "Invalid credentials"
        raise HTTPException(status_code=401, detail=msg)

    if resp.status_code != 200:
        logger.error("Supabase login error %s: %s", resp.status_code, resp.text)
        raise HTTPException(status_code=resp.status_code, detail="Authentication failed")

    data = resp.json()
    return {
        "access_token": data.get("access_token"),
        "token_type": data.get("token_type", "bearer"),
        "expires_in": data.get("expires_in"),
        "user": data.get("user"),
    }


@router.post("/register")
async def register(body: AuthRequest):
    """Create a new user account. Returns access_token on success."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SUPABASE_URL}/auth/v1/signup",
            headers=_anon_headers(),
            json={"email": body.email, "password": body.password},
            timeout=15,
        )

    if resp.status_code == 400:
        try:
            data = resp.json()
        except Exception:
            data = {}
        msg = data.get("error_description") or data.get("msg") or data.get("error") or "Registration failed"
        raise HTTPException(status_code=400, detail=msg)

    if resp.status_code not in (200, 201):
        logger.error("Supabase register error %s: %s", resp.status_code, resp.text)
        raise HTTPException(status_code=resp.status_code, detail="Registration failed")

    data = resp.json()
    return {
        "access_token": data.get("access_token"),
        "token_type": data.get("token_type", "bearer"),
        "expires_in": data.get("expires_in"),
        "user": data.get("user"),
    }


@router.get("/me")
async def get_me(authorization: str | None = Header(default=None)):
    """Return current user info from Bearer JWT. Verifies token via Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization[len("Bearer "):]

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={**_anon_headers(), "Authorization": f"Bearer {token}"},
            timeout=10,
        )

    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch user")

    return resp.json()
