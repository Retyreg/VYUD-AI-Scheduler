"""APScheduler-based auto-posting service.

Checks for scheduled posts every minute and publishes them via the
appropriate platform service (Telegram / LinkedIn / VK).
"""

import logging
import os
from typing import Any, Dict, Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Import platform services at module level so import errors surface at startup
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
        if platform == "telegram":
            token = account.get("token", os.getenv("TELEGRAM_BOT_TOKEN", ""))
            channel = account.get("channel_id", os.getenv("TELEGRAM_CHAT_ID", ""))
            await send_message(
                bot_token=token,
                channel_id=channel,
                text=content,
                image_url=image_url,
            )

        elif platform == "linkedin":
            token = account.get("token", os.getenv("LINKEDIN_ACCESS_TOKEN", ""))
            profile_id = account.get("channel_id", os.getenv("LINKEDIN_PROFILE_ID", ""))
            await post_to_linkedin(
                access_token=token,
                profile_id=profile_id,
                text=content,
                image_url=image_url,
            )

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

        await _mark_post_published(post_id)
        logger.info("Post %s published successfully on %s", post_id, platform)

    except Exception as e:
        logger.error("Failed to publish post %s: %s", post_id, e)
        await _mark_post_failed(post_id, str(e))


async def _mark_post_published(post_id: str) -> None:
    try:
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=_service_headers(),
                params={"id": f"eq.{post_id}"},
                json={"status": "published"},
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
    _scheduler.start()
    logger.info("APScheduler started — checking posts every minute")


async def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
