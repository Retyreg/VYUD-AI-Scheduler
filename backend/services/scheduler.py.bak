import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
from supabase import create_client
from services.telegram import TelegramService
from services.linkedin import LinkedInService

supabase = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", "")
)

telegram = TelegramService(os.getenv("TELEGRAM_BOT_TOKEN", ""))
linkedin = LinkedInService()

async def check_and_publish_posts():
    try:
        now = datetime.now(timezone.utc)
        result = supabase.table("posts").select("*").eq("status", "scheduled").lte("scheduled_at", now.isoformat()).execute()
        for post in result.data:
            try:
                if post["platform"] == "telegram":
                    await publish_telegram(post)
                elif post["platform"] == "linkedin":
                    await publish_linkedin(post)
            except Exception as e:
                print(f"Error publishing {post['id']}: {e}")
                supabase.table("posts").update({"status": "failed"}).eq("id", post["id"]).execute()
    except Exception as e:
        print(f"Scheduler error: {e}")

async def publish_telegram(post: dict):
    account = supabase.table("publisher_accounts").select("*").eq("platform", "telegram").eq("is_active", True).execute()
    if not account.data:
        raise Exception("Telegram not connected")
    channel_id = account.data[0].get("channel_id") or "@vyud_ai"
    content = post["content"]
    if post.get("utm_tag"):
        content += f"\n\nvyud.online{post['utm_tag']}"
    result = await telegram.send_message(channel_id, content)
    if result.get("ok"):
        supabase.table("posts").update({"status": "published", "published_at": datetime.now(timezone.utc).isoformat()}).eq("id", post["id"]).execute()
        print(f"Published {post['id']} to Telegram")
    else:
        raise Exception(result.get("description", "Unknown error"))

async def publish_linkedin(post: dict):
    content = post["content"]
    if post.get("utm_tag"):
        content += f"\n\nvyud.tech{post['utm_tag']}"
    result = await linkedin.post_to_organization(content)
    if result.get("ok"):
        supabase.table("posts").update({"status": "published", "published_at": datetime.now(timezone.utc).isoformat()}).eq("id", post["id"]).execute()
        print(f"Published {post['id']} to LinkedIn")
    else:
        raise Exception(result.get("error", "Unknown error"))

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_and_publish_posts, IntervalTrigger(seconds=30), id="post_publisher", replace_existing=True)
    scheduler.start()
    print("Scheduler started")
    return scheduler
