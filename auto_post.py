import logging
import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from groq import Groq

from linkedin_poster import LinkedinPoster
from telegram_poster import TelegramPoster

load_dotenv()

logger = logging.getLogger(__name__)

FLASK_API_URL = os.environ.get("FLASK_API_URL", "http://127.0.0.1:5000")
REQUEST_TIMEOUT = 10


def generate_post(topic):
    groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt = (
        f"Создай пост для социальных сетей на тему: {topic}. "
        "Пост должен быть информативным, engaging и не длиннее 200 символов."
    )
    response = groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


def schedule_post(platform, content):
    """
    Save a post to the DB with status='scheduled' BEFORE publishing.
    Returns the new post ID, or None on failure.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        response = requests.post(
            f"{FLASK_API_URL}/api/posts/",
            json={
                "platform": platform,
                "content": content,
                "status": "scheduled",
                "timestamp": timestamp,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 201:
            post_id = response.json().get("id")
            logger.info("Scheduled %s post id=%s in database", platform, post_id)
            return post_id
        logger.warning(
            "Unexpected response scheduling %s post: %s %s",
            platform, response.status_code, response.text,
        )
    except requests.exceptions.RequestException as e:
        logger.error("Failed to schedule post in database: %s", e)
    return None


def update_post_status(post_id, status):
    """
    Update the status of an existing post after it has been published.
    Transitions: scheduled → success | error
    """
    if post_id is None:
        return
    try:
        response = requests.patch(
            f"{FLASK_API_URL}/api/posts/{post_id}",
            json={"status": status},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 200:
            logger.info("Updated post id=%s status to '%s'", post_id, status)
        else:
            logger.warning(
                "Unexpected response updating post %s: %s %s",
                post_id, response.status_code, response.text,
            )
    except requests.exceptions.RequestException as e:
        logger.error("Failed to update post %s status: %s", post_id, e)


def main():
    topic = "Искусственный интеллект в бизнесе"  # Можно сделать параметром или случайным
    post_content = generate_post(topic)

    # Постинг в Telegram: сначала сохраняем как scheduled, потом публикуем
    tg_id = schedule_post("Telegram", post_content)
    tg_result = TelegramPoster().post_text(post_content)
    print("Telegram post result:", tg_result)
    update_post_status(tg_id, tg_result.get("status", "error"))

    # Постинг в LinkedIn: сначала сохраняем как scheduled, потом публикуем
    li_id = schedule_post("LinkedIn", post_content)
    li_result = LinkedinPoster().post_text(post_content)
    print("LinkedIn post result:", li_result)
    update_post_status(li_id, li_result.get("status", "error"))


if __name__ == "__main__":
    main()