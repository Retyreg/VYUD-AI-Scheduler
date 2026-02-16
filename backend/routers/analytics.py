"""
Analytics Router — API эндпоинты для аналитики постов
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/analytics", tags=["analytics"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


class RefreshAnalyticsRequest(BaseModel):
    post_id: str
    platform: str


class AnalyticsResponse(BaseModel):
    post_id: str
    platform: str
    views: int = 0
    clicks: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    collected_at: Optional[str] = None
    error: Optional[str] = None


async def get_current_user(authorization: str = Header(...)):
    """Извлечь user_id из JWT токена"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {token}"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_data = response.json()
        return {"id": user_data["id"], "token": token}


async def get_account_credentials(user_id: str, platform: str, token: str):
    """Получить credentials аккаунта"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/publisher_accounts",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {token}"
            },
            params={
                "user_id": f"eq.{user_id}",
                "platform": f"eq.{platform}",
                "limit": "1"
            }
        )
        
        if response.status_code == 200:
            accounts = response.json()
            return accounts[0] if accounts else None
        return None


async def get_post_details(post_id: str, token: str):
    """Получить детали поста"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/posts",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {token}"
            },
            params={
                "id": f"eq.{post_id}",
                "limit": "1"
            }
        )
        
        if response.status_code == 200:
            posts = response.json()
            return posts[0] if posts else None
        return None


@router.post("/refresh", response_model=AnalyticsResponse)
async def refresh_analytics(
    request: RefreshAnalyticsRequest,
    user: dict = Depends(get_current_user)
):
    """Обновить статистику для поста"""
    from services.analytics import analytics_service
    
    post = await get_post_details(request.post_id, user["token"])
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.get("status") != "published":
        raise HTTPException(status_code=400, detail="Analytics available only for published posts")
    
    account = await get_account_credentials(user["id"], request.platform, user["token"])
    if not account:
        raise HTTPException(status_code=400, detail=f"No {request.platform} account connected")
    
    platform_post_id = post.get("platform_post_id")
    if not platform_post_id:
        raise HTTPException(status_code=400, detail="Platform post ID not found")
    
    stats = {}
    
    if request.platform == "telegram":
        tgstat_token = os.getenv("TGSTAT_TOKEN")
        if tgstat_token:
            channel_username = account.get("channel_username", "").replace("@", "")
            stats = await analytics_service.fetch_telegram_stats_via_tgstat(
                channel_username=channel_username,
                message_id=int(platform_post_id),
                tgstat_token=tgstat_token
            )
        else:
            stats = {"views": 0, "clicks": 0, "error": "TGStat API not configured"}
    
    elif request.platform == "linkedin":
        stats = await analytics_service.fetch_linkedin_stats(
            access_token=account.get("access_token"),
            share_urn=platform_post_id
        )
    
    elif request.platform == "vk":
        parts = platform_post_id.split("_")
        if len(parts) == 2:
            stats = await analytics_service.fetch_vk_stats(
                access_token=account.get("access_token"),
                owner_id=int(parts[0]),
                post_id=int(parts[1])
            )
        else:
            stats = {"error": "Invalid VK post ID format"}
    
    if "error" not in stats:
        await analytics_service.save_analytics(
            post_id=request.post_id,
            platform=request.platform,
            user_id=user["id"],
            stats=stats,
            access_token=user["token"]
        )
    
    return AnalyticsResponse(
        post_id=request.post_id,
        platform=request.platform,
        views=stats.get("views", 0) or 0,
        clicks=stats.get("clicks", 0) or 0,
        likes=stats.get("likes", 0) or 0,
        comments=stats.get("comments", 0) or 0,
        shares=stats.get("shares", 0) or 0,
        error=stats.get("error")
    )


@router.get("/post/{post_id}")
async def get_post_analytics(post_id: str, user: dict = Depends(get_current_user)):
    """Получить аналитику для поста"""
    from services.analytics import analytics_service
    
    result = await analytics_service.get_analytics_for_post(post_id, user["token"])
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result["data"]


@router.get("/all")
async def get_all_analytics(limit: int = 50, user: dict = Depends(get_current_user)):
    """Получить аналитику всех постов"""
    from services.analytics import analytics_service
    
    result = await analytics_service.get_all_analytics(user["id"], user["token"], limit)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result["data"]


@router.get("/summary")
async def get_analytics_summary(user: dict = Depends(get_current_user)):
    """Сводная статистика"""
    from services.analytics import analytics_service
    
    result = await analytics_service.get_all_analytics(user["id"], user["token"], 1000)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    data = result["data"]
    summary = {
        "total_posts": len(data),
        "total_views": sum(item.get("views", 0) or 0 for item in data),
        "total_clicks": sum(item.get("clicks", 0) or 0 for item in data),
        "by_platform": {}
    }
    
    platforms = set(item["platform"] for item in data)
    for platform in platforms:
        platform_data = [item for item in data if item["platform"] == platform]
        summary["by_platform"][platform] = {
            "posts": len(platform_data),
            "views": sum(item.get("views", 0) or 0 for item in platform_data),
            "clicks": sum(item.get("clicks", 0) or 0 for item in platform_data)
        }
    
    return summary
