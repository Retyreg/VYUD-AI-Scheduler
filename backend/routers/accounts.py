"""Accounts router — manage Telegram / LinkedIn / VK publishing accounts.

IMPORTANT: Uses SUPABASE_SERVICE_KEY (not anon key) to bypass RLS.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
# Service role key is required here — anon key is blocked by RLS on accounts table.
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


def _service_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


class TelegramAccount(BaseModel):
    name: str
    bot_token: str
    channel_id: str


class LinkedInAccount(BaseModel):
    name: str
    access_token: str
    profile_id: str


class VKAccount(BaseModel):
    name: str
    access_token: str
    group_id: Optional[str] = None


@router.get("/", response_model=List[Dict[str, Any]])
async def list_accounts():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/accounts",
                headers=_service_headers(),
                params={"order": "created_at.desc", "select": "id,name,platform,created_at"},
            )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error listing accounts: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error listing accounts: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/telegram", response_model=Dict[str, Any], status_code=201)
async def add_telegram_account(account: TelegramAccount):
    payload = {
        "platform": "telegram",
        "name": account.name,
        "token": account.bot_token,
        "channel_id": account.channel_id,
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/accounts",
                headers=_service_headers(),
                json=payload,
            )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if isinstance(data, list) else data
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error adding Telegram account: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error adding Telegram account: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/linkedin", response_model=Dict[str, Any], status_code=201)
async def add_linkedin_account(account: LinkedInAccount):
    payload = {
        "platform": "linkedin",
        "name": account.name,
        "token": account.access_token,
        "channel_id": account.profile_id,
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/accounts",
                headers=_service_headers(),
                json=payload,
            )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if isinstance(data, list) else data
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error adding LinkedIn account: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error adding LinkedIn account: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vk", response_model=Dict[str, Any], status_code=201)
async def add_vk_account(account: VKAccount):
    payload = {
        "platform": "vk",
        "name": account.name,
        "token": account.access_token,
        "channel_id": account.group_id or "",
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/accounts",
                headers=_service_headers(),
                json=payload,
            )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if isinstance(data, list) else data
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error adding VK account: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error adding VK account: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{account_id}", status_code=204)
async def delete_account(account_id: str):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{SUPABASE_URL}/rest/v1/accounts",
                headers=_service_headers(),
                params={"id": f"eq.{account_id}"},
            )
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error deleting account: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error deleting account: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
