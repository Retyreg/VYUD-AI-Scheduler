from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
import requests

from services.telegram import TelegramService
from services.linkedin import LinkedInService

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_headers(prefer="return=representation"):
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": prefer
    }

def sb_get(table, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    resp = requests.get(url, headers=get_headers())
    resp.raise_for_status()
    return resp.json()

def sb_update(table, record_id, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{record_id}"
    resp = requests.patch(url, json=data, headers=get_headers())
    resp.raise_for_status()
    return resp.json()

telegram = TelegramService(os.getenv("TELEGRAM_BOT_TOKEN", ""))
linkedin = LinkedInService()

async def check_and_publish_posts():
    try:
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        posts = sb_get("posts", f"status=eq.scheduled&scheduled_at=lte.{ts}&order=scheduled_at.asc")
        for post in posts:
            try:
                if post["platform"] == "telegram":
                    await publish_telegram(post)
                elif post["platform"] == "linkedin":
                    await publish_linkedin(post)
            except Exception as e:
                print(f"Error publishing {post['id']}: {e}")
                sb_update("posts", post["id"], {"status": "failed"})
    except Exception as e:
        print(f"Scheduler error: {e}")

async def publish_telegram(post):
    accounts = sb_get("publisher_accounts", "platform=eq.telegram&is_active=eq.true")
    if not accounts:
        raise Exception("Telegram not connected")
    channel_id = accounts[0].get("channel_id") or "@vyud_ai"
    content = post["content"]
    if post.get("utm_tag"):
        content += f"\n\nvyud.online{post['utm_tag']}"
    result = await telegram.send_message(channel_id, content)
    if result.get("ok"):
        sb_update("posts", post["id"], {"status": "published", "published_at": datetime.now(timezone.utc).isoformat()})
        print(f"Published {post['id']} to Telegram")
    else:
        raise Exception(result.get("description", "Unknown error"))

async def publish_linkedin(post):
    content = post["content"]
    if post.get("utm_tag"):
        content += f"\n\nvyud.tech{post['utm_tag']}"
    result = await linkedin.post_to_organization(content)
    if result.get("ok"):
        sb_update("posts", post["id"], {"status": "published", "published_at": datetime.now(timezone.utc).isoformat()})
        print(f"Published {post['id']} to LinkedIn")
    else:
        raise Exception(result.get("error", "Unknown error"))

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_and_publish_posts, IntervalTrigger(seconds=30), id="post_publisher", replace_existing=True)
    scheduler.start()
    print("Scheduler started")
    return scheduler
