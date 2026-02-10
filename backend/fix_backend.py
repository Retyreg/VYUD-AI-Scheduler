#!/usr/bin/env python3
"""
VYUD Publisher — миграция с supabase SDK на requests.
Запустить на сервере: python3 fix_backend.py
"""
import os

BASE = "/root/publisher_app/backend"

files = {}

# ============================================================
# 1. routers/posts.py
# ============================================================
files[f"{BASE}/routers/posts.py"] = '''from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
import os
import sys
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import PostCreate, PostUpdate, PostResponse, PostStatus

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
BASE_URL = f"{SUPABASE_URL}/rest/v1/posts"

def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def generate_utm(platform: str) -> str:
    month = datetime.now().strftime("%b").lower()
    year = datetime.now().strftime("%y")
    return f"?utm_source={platform}_{month}{year}"

@router.get("/", response_model=List[PostResponse])
async def get_posts(status: PostStatus = None, limit: int = 50):
    try:
        url = BASE_URL + f"?order=scheduled_at.asc&limit={limit}"
        if status:
            url += f"&status=eq.{status.value}"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=PostResponse)
async def create_post(post: PostCreate):
    try:
        utm_tag = generate_utm(post.platform.value)
        data = {
            "content": post.content,
            "platform": post.platform.value,
            "status": PostStatus.scheduled.value,
            "scheduled_at": post.scheduled_at.isoformat(),
            "utm_tag": utm_tag,
            "channel_id": post.channel_id
        }
        response = requests.post(BASE_URL, json=data, headers=get_headers())
        response.raise_for_status()
        return response.json()[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str):
    try:
        response = requests.get(f"{BASE_URL}?id=eq.{post_id}", headers=get_headers())
        response.raise_for_status()
        data = response.json()
        if not data:
            raise HTTPException(status_code=404, detail="Post not found")
        return data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(post_id: str, post: PostUpdate):
    try:
        data = post.model_dump(exclude_unset=True)
        if "scheduled_at" in data and data["scheduled_at"]:
            data["scheduled_at"] = data["scheduled_at"].isoformat()
        if "status" in data and data["status"]:
            data["status"] = data["status"].value
        response = requests.patch(f"{BASE_URL}?id=eq.{post_id}", json=data, headers=get_headers())
        response.raise_for_status()
        result = response.json()
        if not result:
            raise HTTPException(status_code=404, detail="Post not found")
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{post_id}")
async def delete_post(post_id: str):
    try:
        response = requests.delete(f"{BASE_URL}?id=eq.{post_id}", headers=get_headers())
        response.raise_for_status()
        return {"deleted": True, "id": post_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''

# ============================================================
# 2. routers/accounts.py
# ============================================================
files[f"{BASE}/routers/accounts.py"] = '''from fastapi import APIRouter, HTTPException
from typing import List
import os
import sys
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import AccountCreate, AccountResponse, Platform

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
BASE_URL = f"{SUPABASE_URL}/rest/v1/publisher_accounts"

def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

@router.get("/", response_model=List[AccountResponse])
async def get_accounts():
    try:
        response = requests.get(BASE_URL, headers=get_headers())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=AccountResponse)
async def connect_account(account: AccountCreate):
    try:
        check_url = f"{BASE_URL}?platform=eq.{account.platform.value}"
        check_resp = requests.get(check_url, headers=get_headers())
        check_resp.raise_for_status()
        existing = check_resp.json()

        data = {
            "token": account.token,
            "channel_id": account.channel_id,
            "channel_name": account.channel_name,
            "is_active": True
        }

        if existing:
            url = f"{BASE_URL}?id=eq.{existing[0]['id']}"
            response = requests.patch(url, json=data, headers=get_headers())
        else:
            data["platform"] = account.platform.value
            response = requests.post(BASE_URL, json=data, headers=get_headers())

        response.raise_for_status()
        return response.json()[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{account_id}")
async def disconnect_account(account_id: str):
    try:
        url = f"{BASE_URL}?id=eq.{account_id}"
        data = {"is_active": False}
        response = requests.patch(url, json=data, headers=get_headers())
        response.raise_for_status()
        return {"disconnected": True, "id": account_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''

# ============================================================
# 3. services/scheduler.py
# ============================================================
files[f"{BASE}/services/scheduler.py"] = '''from datetime import datetime, timezone
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
        posts = sb_get("posts", f"status=eq.scheduled&scheduled_at=lte.{now.isoformat()}&order=scheduled_at.asc")
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
        content += f"\\n\\nvyud.online{post['utm_tag']}"
    result = await telegram.send_message(channel_id, content)
    if result.get("ok"):
        sb_update("posts", post["id"], {"status": "published", "published_at": datetime.now(timezone.utc).isoformat()})
        print(f"Published {post['id']} to Telegram")
    else:
        raise Exception(result.get("description", "Unknown error"))

async def publish_linkedin(post):
    content = post["content"]
    if post.get("utm_tag"):
        content += f"\\n\\nvyud.tech{post['utm_tag']}"
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
'''

# ============================================================
# 4. main.py
# ============================================================
files[f"{BASE}/main.py"] = '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()

from services.scheduler import start_scheduler

scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    scheduler = start_scheduler()
    print("Publisher API started")
    yield
    if scheduler:
        scheduler.shutdown()
    print("Publisher API stopped")

app = FastAPI(
    title="VYUD Publisher API",
    description="API for autoposting and AI content generation",
    version="2.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import posts, accounts, ai, prompts

app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])

@app.get("/")
async def root():
    return {"status": "ok", "service": "VYUD Publisher API", "version": "2.2.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "scheduler": "running" if scheduler else "stopped"}
'''

# ============================================================
# Записываем файлы
# ============================================================
if __name__ == "__main__":
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content.strip() + '\n')
        print(f"OK  {path}")

    print(f"\n=== {len(files)} files written ===")
    print("Now run:")
    print("  systemctl restart publisher-api")
