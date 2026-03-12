"""VK API integration — post text/images to groups and user walls."""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_VK_API = "https://api.vk.com/method"
_VK_API_VERSION = "5.199"


async def post_to_vk(
    access_token: str,
    owner_id: Optional[str],
    text: str,
    image_url: Optional[str] = None,
) -> dict:
    """Post content to VK wall.

    Args:
        access_token: VK API access token with wall.post permission.
        owner_id: Group ID (negative, e.g. "-123456") or user ID.
                  If None, posts to the authenticated user's wall.
        text: Post text.
        image_url: Optional image URL (public URL for attachment).

    Returns:
        VK API response dict with post ID.

    Raises:
        httpx.HTTPStatusError: On HTTP errors.
        ValueError: On VK API logical errors.
    """
    params: dict = {
        "access_token": access_token,
        "message": text,
        "v": _VK_API_VERSION,
        "from_group": 1,
    }

    if owner_id:
        params["owner_id"] = owner_id

    if image_url:
        params["attachments"] = image_url

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{_VK_API}/wall.post", data=params)

    resp.raise_for_status()
    result = resp.json()

    if "error" in result:
        error = result["error"]
        raise ValueError(f"VK API error {error.get('error_code')}: {error.get('error_msg')}")

    post_id = result.get("response", {}).get("post_id")
    logger.info("VK post published, post_id=%s owner_id=%s", post_id, owner_id)
    return {"post_id": post_id, "status": "published"}
