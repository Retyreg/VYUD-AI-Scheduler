"""Posts router — CRUD for scheduled posts via Supabase REST API."""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def _headers(token: Optional[str] = None) -> Dict[str, str]:
    key = SUPABASE_KEY
    auth = f"Bearer {token}" if token else f"Bearer {key}"
    return {
        "apikey": key,
        "Authorization": auth,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


class PostCreate(BaseModel):
    content: str
    platform: str
    account_id: Optional[str] = None
    scheduled_at: Optional[str] = None
    status: str = "draft"
    image_url: Optional[str] = None
    utm_params: Optional[Dict[str, Any]] = None


class PostUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None
    scheduled_at: Optional[str] = None
    platform: Optional[str] = None
    account_id: Optional[str] = None
    image_url: Optional[str] = None
    utm_params: Optional[Dict[str, Any]] = None


@router.get("/", response_model=List[Dict[str, Any]])
async def list_posts(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    token = authorization.replace("Bearer ", "") if authorization else None
    params = {"order": "scheduled_at.desc"}
    if status:
        params["status"] = f"eq.{status}"
    if platform:
        params["platform"] = f"eq.{platform}"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=_headers(token),
                params=params,
            )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error listing posts: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error listing posts: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_post(
    post: PostCreate,
    authorization: Optional[str] = Header(None),
):
    token = authorization.replace("Bearer ", "") if authorization else None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=_headers(token),
                json=post.model_dump(exclude_none=True),
            )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if isinstance(data, list) else data
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error creating post: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error creating post: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{post_id}", response_model=Dict[str, Any])
async def get_post(
    post_id: str,
    authorization: Optional[str] = Header(None),
):
    token = authorization.replace("Bearer ", "") if authorization else None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=_headers(token),
                params={"id": f"eq.{post_id}"},
            )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise HTTPException(status_code=404, detail="Post not found")
        return data[0]
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error fetching post: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error fetching post: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{post_id}", response_model=Dict[str, Any])
async def update_post(
    post_id: str,
    post: PostUpdate,
    authorization: Optional[str] = Header(None),
):
    token = authorization.replace("Bearer ", "") if authorization else None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=_headers(token),
                params={"id": f"eq.{post_id}"},
                json=post.model_dump(exclude_none=True),
            )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise HTTPException(status_code=404, detail="Post not found")
        return data[0]
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error updating post: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error updating post: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: str,
    authorization: Optional[str] = Header(None),
):
    token = authorization.replace("Bearer ", "") if authorization else None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=_headers(token),
                params={"id": f"eq.{post_id}"},
            )
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error deleting post: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error deleting post: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
