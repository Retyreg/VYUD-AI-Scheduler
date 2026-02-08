from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from models import PostCreate, PostUpdate, PostResponse, PostStatus

router = APIRouter()

supabase = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", "")
)

def generate_utm(platform: str) -> str:
    month = datetime.now().strftime("%b").lower()
    year = datetime.now().strftime("%y")
    return f"?utm_source={platform}_{month}{year}"

@router.get("/", response_model=List[PostResponse])
async def get_posts(status: PostStatus = None, limit: int = 50):
    try:
        query = supabase.table("posts").select("*").order("scheduled_at", desc=False).limit(limit)
        if status:
            query = query.eq("status", status.value)
        result = query.execute()
        return result.data
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
        result = supabase.table("posts").insert(data).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str):
    try:
        result = supabase.table("posts").select("*").eq("id", post_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")
        return result.data[0]
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
        result = supabase.table("posts").update(data).eq("id", post_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{post_id}")
async def delete_post(post_id: str):
    try:
        supabase.table("posts").delete().eq("id", post_id).execute()
        return {"deleted": True, "id": post_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
