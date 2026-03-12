"""Telegram Bot API integration — post text/media to channels."""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


async def send_message(
    bot_token: str,
    channel_id: str,
    text: str,
    image_url: Optional[str] = None,
    parse_mode: str = "HTML",
) -> dict:
    """Send a message (optionally with image) to a Telegram channel.

    Args:
        bot_token: Telegram Bot API token.
        channel_id: Channel username (@channel) or numeric ID.
        text: Message text (HTML or Markdown formatting).
        image_url: Optional URL of image to attach.
        parse_mode: "HTML" or "Markdown".

    Returns:
        Telegram API response dict.

    Raises:
        httpx.HTTPStatusError: If Telegram API returns an error.
    """
    base_url = f"https://api.telegram.org/bot{bot_token}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        if image_url:
            resp = await client.post(
                f"{base_url}/sendPhoto",
                json={
                    "chat_id": channel_id,
                    "photo": image_url,
                    "caption": text,
                    "parse_mode": parse_mode,
                },
            )
        else:
            resp = await client.post(
                f"{base_url}/sendMessage",
                json={
                    "chat_id": channel_id,
                    "text": text,
                    "parse_mode": parse_mode,
                },
            )

    resp.raise_for_status()
    result = resp.json()
    if not result.get("ok"):
        raise ValueError(f"Telegram API error: {result.get('description', 'Unknown error')}")

    logger.info("Telegram message sent to %s", channel_id)
    return result
