from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
import requests

from services.telegram import TelegramService
from services.linkedin import LinkedInService
from services.vk import VKService

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_KEY", ""))

def get_headers(prefer="return=representation"):
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
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
vk = VKService()

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
                elif post["platform"] == "vk":
                    await publish_vk(post)
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
        content += "\n\nvyud.online" + post["utm_tag"]
    result = await telegram.send_message(channel_id, content)
    if result.get("ok"):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Сохраняем message_id для аналитики
        message_id = result.get("result", {}).get("message_id", "")
        sb_update("posts", post["id"], {
            "status": "published", 
            "published_at": ts,
            "platform_post_id": str(message_id)
        })
        print(f"Published {post['id']} to Telegram (message_id: {message_id})")
    else:
        raise Exception(result.get("description", "Unknown error"))

async def publish_linkedin(post):
    content = post["content"]
    if post.get("utm_tag"):
        content += "\n\nvyud.tech" + post["utm_tag"]
    result = await linkedin.post_to_profile(content)
    if result.get("ok"):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Сохраняем share URN для аналитики
        share_urn = result.get("share_urn", "") or result.get("id", "")
        sb_update("posts", post["id"], {
            "status": "published", 
            "published_at": ts,
            "platform_post_id": str(share_urn)
        })
        print(f"Published {post['id']} to LinkedIn (share_urn: {share_urn})")
    else:
        raise Exception(result.get("error", "Unknown error"))

async def publish_vk(post):
    accounts = sb_get("publisher_accounts", "platform=eq.vk&is_active=eq.true")
    if not accounts:
        raise Exception("VK not connected")
    account = accounts[0]
    token = account.get("token", "")
    owner_id = account.get("channel_id", "")
    content = post["content"]
    if post.get("utm_tag"):
        content += "\n\nvyud.tech" + post["utm_tag"]
    result = await vk.post_to_wall(token, owner_id, content)
    if result.get("ok"):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Сохраняем owner_id_post_id для аналитики
        post_id = result.get("post_id", "")
        platform_post_id = f"{owner_id}_{post_id}" if post_id else ""
        sb_update("posts", post["id"], {
            "status": "published", 
            "published_at": ts,
            "platform_post_id": platform_post_id
        })
        print(f"Published {post['id']} to VK (post_id: {platform_post_id})")
    else:
        raise Exception(result.get("error", "Unknown VK error"))

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_and_publish_posts, IntervalTrigger(seconds=30), id="post_publisher", replace_existing=True)
    scheduler.start()
    print("Scheduler started")
    return scheduler
