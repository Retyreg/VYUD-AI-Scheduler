"""Prompts router — manage reusable AI prompt templates."""

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


class PromptCreate(BaseModel):
    title: str
    content: str
    platform: Optional[str] = None


class PromptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    platform: Optional[str] = None


@router.get("/", response_model=List[Dict[str, Any]])
async def list_prompts(authorization: Optional[str] = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/prompts",
                headers=_headers(token),
                params={"order": "created_at.desc"},
            )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error listing prompts: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error listing prompts: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_prompt(
    prompt: PromptCreate,
    authorization: Optional[str] = Header(None),
):
    token = authorization.replace("Bearer ", "") if authorization else None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/prompts",
                headers=_headers(token),
                json=prompt.model_dump(exclude_none=True),
            )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if isinstance(data, list) else data
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error creating prompt: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error creating prompt: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{prompt_id}", response_model=Dict[str, Any])
async def update_prompt(
    prompt_id: str,
    prompt: PromptUpdate,
    authorization: Optional[str] = Header(None),
):
    token = authorization.replace("Bearer ", "") if authorization else None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{SUPABASE_URL}/rest/v1/prompts",
                headers=_headers(token),
                params={"id": f"eq.{prompt_id}"},
                json=prompt.model_dump(exclude_none=True),
            )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise HTTPException(status_code=404, detail="Prompt not found")
        return data[0]
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error updating prompt: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error updating prompt: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{prompt_id}", status_code=204)
async def delete_prompt(
    prompt_id: str,
    authorization: Optional[str] = Header(None),
):
    token = authorization.replace("Bearer ", "") if authorization else None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{SUPABASE_URL}/rest/v1/prompts",
                headers=_headers(token),
                params={"id": f"eq.{prompt_id}"},
            )
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error deleting prompt: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error deleting prompt: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
