"""Analytics router — post performance metrics via TGStat and platform APIs."""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Header, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TGSTAT_API_KEY = os.getenv("TGSTAT_API_KEY")


def _headers(token: Optional[str] = None) -> Dict[str, str]:
    key = SUPABASE_KEY
    auth = f"Bearer {token}" if token else f"Bearer {key}"
    return {
        "apikey": key,
        "Authorization": auth,
        "Content-Type": "application/json",
    }


@router.get("/", response_model=List[Dict[str, Any]])
async def get_analytics(
    platform: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    """Return analytics records from DB (enriched by scheduler jobs)."""
    token = authorization.replace("Bearer ", "") if authorization else None
    params = {"order": "updated_at.desc"}
    if platform:
        params["platform"] = f"eq.{platform}"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/analytics",
                headers=_headers(token),
                params=params,
            )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("Supabase error fetching analytics: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error fetching analytics: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tgstat/{channel_id}")
async def get_tgstat_stats(channel_id: str):
    """Fetch channel stats directly from TGStat API."""
    if not TGSTAT_API_KEY:
        raise HTTPException(status_code=503, detail="TGSTAT_API_KEY not configured")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.tgstat.ru/channels/stat",
                params={"token": TGSTAT_API_KEY, "channelId": channel_id},
                timeout=15.0,
            )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("TGStat API error: %s", e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error("Error fetching TGStat stats: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
