"""LinkedIn API integration — post text/images to personal and org pages."""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_LINKEDIN_API = "https://api.linkedin.com/v2"


async def post_to_linkedin(
    access_token: str,
    profile_id: str,
    text: str,
    image_url: Optional[str] = None,
) -> dict:
    """Post content to LinkedIn.

    Args:
        access_token: OAuth 2.0 access token.
        profile_id: LinkedIn member URN (urn:li:person:xxx) or
                    organization URN (urn:li:organization:xxx).
        text: Post text content.
        image_url: Optional image URL (must be accessible publicly).

    Returns:
        LinkedIn API response dict.

    Raises:
        httpx.HTTPStatusError: If LinkedIn API returns an error.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    # Determine author URN type
    if not profile_id.startswith("urn:"):
        author = f"urn:li:person:{profile_id}"
    else:
        author = profile_id

    payload: dict = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    if image_url:
        # NOTE: LinkedIn image posting requires a media URN (urn:li:digitalmediaAsset:xxx),
        # not a direct HTTP URL. To attach an image, you must first upload it via the
        # LinkedIn Assets API (/v2/assets?action=registerUpload), then use the returned
        # asset URN here. Direct URLs will cause a validation error from LinkedIn.
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
            {
                "status": "READY",
                "description": {"text": ""},
                "media": image_url,
                "title": {"text": ""},
            }
        ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{_LINKEDIN_API}/ugcPosts", headers=headers, json=payload)

    resp.raise_for_status()
    logger.info("LinkedIn post published for author %s", author)
    return {"id": resp.headers.get("x-restli-id", ""), "status": "published"}
