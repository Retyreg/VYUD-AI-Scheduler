"""APScheduler-based auto-posting service.

Checks for scheduled posts every minute and publishes them via the
appropriate platform service (Telegram / LinkedIn / VK).
Refreshes analytics metrics every 30 minutes.
"""

import logging
import os
from typing import Any, Dict, Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.linkedin import post_to_linkedin
from services.telegram import send_message
from services.vk import post_to_vk

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

_scheduler: Optional[AsyncIOScheduler] = None


def _service_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


async def _publish_post(post: Dict[str, Any]) -> None:
    """Publish a single post via the correct platform service."""
    platform = post.get("platform", "")
    content = post.get("content", "")
    post_id = post.get("id")
    account_id = post.get("account_id")
    image_url = post.get("image_url")

    logger.info("Publishing post id=%s platform=%s", post_id, platform)

    # Fetch account credentials
    account: Dict[str, Any] = {}
    if account_id:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{SUPABASE_URL}/rest/v1/publisher_accounts",
                    headers=_service_headers(),
                    params={"id": f"eq.{account_id}"},
                )
            resp.raise_for_status()
            accounts_list = resp.json()
            if accounts_list:
                account = accounts_list[0]
        except Exception as e:
            logger.error("Failed to fetch account %s: %s", account_id, e)
            await _mark_post_failed(post_id, str(e))
            return

    try:
        platform_post_id: Optional[str] = None

        if platform == "telegram":
            token = account.get("token", os.getenv("TELEGRAM_BOT_TOKEN", ""))
            channel = account.get("channel_id", os.getenv("TELEGRAM_CHAT_ID", ""))
            result = await send_message(
                bot_token=token,
                channel_id=channel,
                text=content,
                image_url=image_url,
            )
            # Capture Telegram message_id for analytics
            message_id = result.get("result", {}).get("message_id")
            if message_id:
                platform_post_id = str(message_id)

        elif platform == "linkedin":
            token = account.get("token", os.getenv("LINKEDIN_ACCESS_TOKEN", ""))
            profile_id = account.get("channel_id", os.getenv("LINKEDIN_PROFILE_ID", ""))
            result = await post_to_linkedin(
                access_token=token,
                profile_id=profile_id,
                text=content,
                image_url=image_url,
            )
            # Capture LinkedIn post URN for analytics
            platform_post_id = result.get("id") or None

        elif platform == "vk":
            token = account.get("token", os.getenv("VK_ACCESS_TOKEN", ""))
            owner_id = account.get("channel_id") or None
            await post_to_vk(
                access_token=token,
                owner_id=owner_id,
                text=content,
                image_url=image_url,
            )

        else:
            raise ValueError(f"Unsupported platform: {platform}")

        await _mark_post_published(post_id, platform_post_id)
        logger.info("Post %s published on %s (platform_post_id=%s)", post_id, platform, platform_post_id)

    except Exception as e:
        logger.error("Failed to publish post %s: %s", post_id, e)
        await _mark_post_failed(post_id, str(e))


async def _mark_post_published(post_id: str, platform_post_id: Optional[str] = None) -> None:
    update: Dict[str, Any] = {"status": "published"}
    if platform_post_id:
        update["platform_post_id"] = platform_post_id
    try:
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=_service_headers(),
                params={"id": f"eq.{post_id}"},
                json=update,
            )
    except Exception as e:
        logger.error("Failed to mark post %s as published: %s", post_id, e)


async def _mark_post_failed(post_id: str, reason: str) -> None:
    try:
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=_service_headers(),
                params={"id": f"eq.{post_id}"},
                json={"status": "failed", "error_message": reason[:500]},
            )
    except Exception as e:
        logger.error("Failed to mark post %s as failed: %s", post_id, e)


async def check_and_publish_scheduled_posts() -> None:
    """Check for posts due for publishing and send them."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    logger.debug("Checking scheduled posts at %s", now)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=_service_headers(),
                params={
                    "status": "eq.scheduled",
                    "scheduled_at": f"lte.{now}",
                    "order": "scheduled_at.asc",
                },
            )
        resp.raise_for_status()
        due_posts = resp.json()
    except Exception as e:
        logger.error("Failed to fetch scheduled posts: %s", e)
        return

    if not due_posts:
        return

    logger.info("Found %d post(s) ready to publish", len(due_posts))
    for post in due_posts:
        await _publish_post(post)


async def refresh_analytics() -> None:
    """Fetch fresh metrics for all published posts and upsert into analytics table."""
    from services.analytics import fetch_telegram_channel_stats, fetch_linkedin_post_stats
    from datetime import datetime, timezone

    logger.info("Starting analytics refresh")

    # Fetch all published posts that have a linked account
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=_service_headers(),
                params={
                    "status": "eq.published",
                    "select": "id,platform,account_id,platform_post_id,content",
                    "order": "created_at.desc",
                    "limit": "100",
                },
            )
        resp.raise_for_status()
        posts = resp.json()
    except Exception as e:
        logger.error("Analytics refresh: failed to fetch posts: %s", e)
        return

    if not posts:
        logger.debug("Analytics refresh: no published posts found")
        return

    # Collect unique account IDs to batch-fetch credentials
    account_ids = list({p["account_id"] for p in posts if p.get("account_id")})
    accounts_map: Dict[str, Dict[str, Any]] = {}
    if account_ids:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{SUPABASE_URL}/rest/v1/publisher_accounts",
                    headers=_service_headers(),
                    params={"id": f"in.({','.join(account_ids)})"},
                )
            resp.raise_for_status()
            for acc in resp.json():
                accounts_map[acc["id"]] = acc
        except Exception as e:
            logger.error("Analytics refresh: failed to fetch accounts: %s", e)

    now = datetime.now(timezone.utc).isoformat()
    refreshed = 0

    for post in posts:
        post_id = post["id"]
        platform = post.get("platform", "")
        account = accounts_map.get(post.get("account_id", ""), {})
        platform_post_id = post.get("platform_post_id")

        try:
            metrics: Dict[str, Any] = {}

            if platform == "telegram":
                token = account.get("token", os.getenv("TELEGRAM_BOT_TOKEN", ""))
                channel = account.get("channel_id", os.getenv("TELEGRAM_CHAT_ID", ""))
                if token and channel:
                    metrics = await fetch_telegram_channel_stats(token, channel)

            elif platform == "linkedin" and platform_post_id:
                token = account.get("token", os.getenv("LINKEDIN_ACCESS_TOKEN", ""))
                if token:
                    metrics = await fetch_linkedin_post_stats(token, platform_post_id)

            if not metrics:
                continue

            # Upsert into analytics table (match on post_id)
            row = {
                "post_id": post_id,
                "platform": platform,
                "views": metrics.get("views", 0),
                "likes": metrics.get("likes", 0),
                "comments": metrics.get("comments", 0),
                "shares": metrics.get("shares", 0),
                "subscribers": metrics.get("subscribers", 0),
                "fetched_at": now,
                "updated_at": now,
                "post_content": (post.get("content") or "")[:200],
            }

            async with httpx.AsyncClient() as client:
                upsert_resp = await client.post(
                    f"{SUPABASE_URL}/rest/v1/analytics",
                    headers={**_service_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
                    json=row,
                )
            upsert_resp.raise_for_status()
            refreshed += 1

        except Exception as e:
            logger.warning("Analytics refresh: failed for post %s: %s", post_id, e)

    logger.info("Analytics refresh complete — updated %d/%d posts", refreshed, len(posts))


async def start_scheduler() -> None:
    global _scheduler
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.warning(
            "SUPABASE_URL or SUPABASE_SERVICE_KEY not set — scheduler disabled"
        )
        return

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        check_and_publish_scheduled_posts,
        trigger="interval",
        minutes=1,
        id="auto_publish",
        replace_existing=True,
    )
    _scheduler.add_job(
        refresh_analytics,
        trigger="interval",
        minutes=30,
        id="analytics_refresh",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("APScheduler started — publishing every 1 min, analytics every 30 min")


async def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
