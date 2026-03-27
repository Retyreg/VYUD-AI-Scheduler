"""Analytics router — post performance metrics via platform APIs."""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException

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
    """Return analytics records from DB, enriched by the scheduler every 30 minutes."""
    token = authorization.replace("Bearer ", "") if authorization else None
    params = {"order": "updated_at.desc", "limit": "200"}
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


@router.post("/refresh")
async def trigger_refresh(background_tasks: BackgroundTasks):
    """Manually trigger an analytics refresh in the background.

    The scheduler runs this automatically every 30 minutes; this
    endpoint allows on-demand refresh from the UI.
    """
    from services.scheduler import refresh_analytics

    background_tasks.add_task(refresh_analytics)
    return {"status": "refresh started"}


@router.get("/summary")
async def get_summary(authorization: Optional[str] = Header(None)):
    """Return aggregated totals across all posts."""
    token = authorization.replace("Bearer ", "") if authorization else None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/analytics",
                headers=_headers(token),
                params={"select": "views,likes,comments,shares,subscribers,platform"},
            )
        resp.raise_for_status()
        rows = resp.json()
    except Exception as e:
        logger.error("Error fetching analytics summary: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    totals: Dict[str, Any] = {
        "total_posts": len(rows),
        "total_views": sum(r.get("views", 0) or 0 for r in rows),
        "total_likes": sum(r.get("likes", 0) or 0 for r in rows),
        "total_comments": sum(r.get("comments", 0) or 0 for r in rows),
        "total_shares": sum(r.get("shares", 0) or 0 for r in rows),
        "total_subscribers": max((r.get("subscribers", 0) or 0 for r in rows), default=0),
        "by_platform": {},
    }

    for row in rows:
        p = row.get("platform", "unknown")
        if p not in totals["by_platform"]:
            totals["by_platform"][p] = {
                "posts": 0, "likes": 0, "comments": 0, "shares": 0, "subscribers": 0,
            }
        totals["by_platform"][p]["posts"] += 1
        totals["by_platform"][p]["likes"] += row.get("likes", 0) or 0
        totals["by_platform"][p]["comments"] += row.get("comments", 0) or 0
        totals["by_platform"][p]["shares"] += row.get("shares", 0) or 0
        totals["by_platform"][p]["subscribers"] = max(
            totals["by_platform"][p]["subscribers"],
            row.get("subscribers", 0) or 0,
        )

    return totals


@router.get("/tgstat/{channel_id}")
async def get_tgstat_stats(channel_id: str):
    """Fetch channel stats directly from TGStat API (requires TGSTAT_API_KEY)."""
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
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
