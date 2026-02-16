from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from datetime import datetime
import os
import sys
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import PostCreate, PostUpdate, PostResponse, PostStatus
from services.auth import verify_token

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")
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
async def get_posts(
    status: PostStatus = None, 
    limit: int = 50,
    user: dict = Depends(verify_token)
):
    try:
        # Фильтруем по user_id
        url = BASE_URL + f"?user_id=eq.{user['user_id']}&order=scheduled_at.asc&limit={limit}"
        if status:
            url += f"&status=eq.{status.value}"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=PostResponse)
async def create_post(post: PostCreate, user: dict = Depends(verify_token)):
    try:
        utm_tag = generate_utm(post.platform.value)
        data = {
            "content": post.content,
            "platform": post.platform.value,
            "status": PostStatus.scheduled.value,
            "scheduled_at": post.scheduled_at.isoformat(),
            "utm_tag": utm_tag,
            "channel_id": post.channel_id,
            "user_id": user["user_id"]  # Привязываем к пользователю
        }
        response = requests.post(BASE_URL, json=data, headers=get_headers())
        response.raise_for_status()
        return response.json()[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str, user: dict = Depends(verify_token)):
    try:
        # Проверяем что пост принадлежит пользователю
        response = requests.get(
            f"{BASE_URL}?id=eq.{post_id}&user_id=eq.{user['user_id']}", 
            headers=get_headers()
        )
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
async def update_post(post_id: str, post: PostUpdate, user: dict = Depends(verify_token)):
    try:
        data = post.model_dump(exclude_unset=True)
        if "scheduled_at" in data and data["scheduled_at"]:
            data["scheduled_at"] = data["scheduled_at"].isoformat()
        if "status" in data and data["status"]:
            data["status"] = data["status"].value
        # Обновляем только свой пост
        response = requests.patch(
            f"{BASE_URL}?id=eq.{post_id}&user_id=eq.{user['user_id']}", 
            json=data, 
            headers=get_headers()
        )
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
async def delete_post(post_id: str, user: dict = Depends(verify_token)):
    try:
        # Удаляем только свой пост
        response = requests.delete(
            f"{BASE_URL}?id=eq.{post_id}&user_id=eq.{user['user_id']}", 
            headers=get_headers()
        )
        response.raise_for_status()
        return {"deleted": True, "id": post_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
