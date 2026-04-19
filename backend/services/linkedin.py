"""LinkedIn API integration — post text/images to personal and org pages."""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_LINKEDIN_REST_API = "https://api.linkedin.com/rest"
_LINKEDIN_VERSION = "202401"


async def post_to_linkedin(
    access_token: str,
    profile_id: str,
    text: str,
    image_url: Optional[str] = None,
) -> dict:
    """Post content to LinkedIn using the new REST Posts API (v202401).

    Args:
        access_token: OAuth 2.0 access token with w_member_social scope.
        profile_id: LinkedIn member URN (urn:li:person:xxx) or
                    organization URN (urn:li:organization:xxx).
        text: Post text content.
        image_url: Optional image URL (not yet supported by this integration).

    Returns:
        Dict with post id and status.

    Raises:
        httpx.HTTPStatusError: If LinkedIn API returns an error.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": _LINKEDIN_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
    }

    if not profile_id.startswith("urn:"):
        author = f"urn:li:person:{profile_id}"
    else:
        author = profile_id

    payload: dict = {
        "author": author,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    # NOTE: Image posting via new API requires uploading through /rest/images first
    # (initializeUpload → uploadUrl → finalize), then attaching the image URN.
    # Direct HTTP URLs are not supported. Image support is tracked as a separate task.
    if image_url:
        logger.warning("Image posting is not yet supported in REST API v202401; posting text only.")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{_LINKEDIN_REST_API}/posts", headers=headers, json=payload)

    if not resp.is_success:
        logger.error("LinkedIn API error %s: %s", resp.status_code, resp.text)
    resp.raise_for_status()

    post_id = resp.headers.get("x-restli-id", "")
    logger.info("LinkedIn post published for author %s, post id=%s", author, post_id)
    return {"id": post_id, "status": "published"}
