"""Analytics service — fetch real post metrics from Telegram and LinkedIn."""

import logging
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


async def fetch_telegram_channel_stats(bot_token: str, channel_id: str) -> Dict[str, Any]:
    """Get subscriber count for a Telegram channel via Bot API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"https://api.telegram.org/bot{bot_token}/getChatMemberCount",
            params={"chat_id": channel_id},
        )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise ValueError(data.get("description", "Telegram API error"))
    return {
        "subscribers": data["result"],
        "views": 0,
        "likes": 0,
        "comments": 0,
        "shares": 0,
    }


async def fetch_linkedin_post_stats(access_token: str, post_id: str) -> Dict[str, Any]:
    """Get engagement stats for a LinkedIn post via socialMetadata API.

    post_id can be a bare numeric ID or a full URN (urn:li:ugcPost:...).
    Returns dict with likes, comments, shares, views.
    """
    if not post_id.startswith("urn:"):
        post_urn = f"urn:li:ugcPost:{post_id}"
    else:
        post_urn = post_id

    # URL-encode the URN for use as a path segment
    encoded = post_urn.replace(":", "%3A").replace(",", "%2C")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    # Remove the parentheses
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"https://api.linkedin.com/rest/socialMetadata/{encoded}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "LinkedIn-Version": "202401",
                "X-Restli-Protocol-Version": "2.0.0"
            },
        )

    if resp.status_code == 401:
        raise ValueError("LinkedIn token expired or missing r_member_social scope")

    if resp.status_code != 200:
        logger.warning("LinkedIn socialMetadata returned %s for %s", resp.status_code, post_id)
        return {"likes": 0, "comments": 0, "shares": 0, "views": 0, "subscribers": 0}

    data = resp.json()
    counts = (
        data.get("socialDetail", {})
        .get("totalSocialActivityCounts", {})
    )
    return {
        "likes": counts.get("numLikes", 0),
        "comments": counts.get("numComments", 0),
        "shares": counts.get("numShares", 0),
        "views": 0,     # requires r_organization_social scope; not fetched here
        "subscribers": 0,
    }
