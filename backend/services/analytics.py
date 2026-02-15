"""
Analytics Service — сбор метрик с социальных платформ
"""
import os
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


class AnalyticsService:
    """Сервис для сбора и сохранения аналитики постов"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.http_client.aclose()
    
    async def fetch_telegram_stats_via_tgstat(
        self,
        channel_username: str,
        message_id: int,
        tgstat_token: str
    ) -> Dict[str, Any]:
        """Получить статистику через TGStat API"""
        if not tgstat_token:
            return {"error": "TGStat token not configured"}
        
        url = "https://api.tgstat.ru/posts/get"
        params = {
            "token": tgstat_token,
            "postId": f"{channel_username}/{message_id}"
        }
        
        try:
            response = await self.http_client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == "ok":
                post_data = data.get("response", {})
                return {
                    "views": post_data.get("views", 0),
                    "shares": post_data.get("forwards", 0),
                    "reactions": post_data.get("reactions", 0),
                    "raw_response": data
                }
            else:
                return {"error": data.get("error", "Unknown error")}
        except Exception as e:
            return {"error": str(e)}
    
    async def fetch_linkedin_stats(
        self,
        access_token: str,
        share_urn: str
    ) -> Dict[str, Any]:
        """Получить статистику поста в LinkedIn"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        url = f"https://api.linkedin.com/v2/socialActions/{share_urn}"
        
        try:
            response = await self.http_client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "likes": data.get("likesSummary", {}).get("totalLikes", 0),
                    "comments": data.get("commentsSummary", {}).get("totalFirstLevelComments", 0),
                    "shares": data.get("sharesSummary", {}).get("totalShares", 0),
                    "views": None,
                    "clicks": None,
                    "raw_response": data
                }
            elif response.status_code == 401:
                return {"error": "LinkedIn token expired", "needs_reauth": True}
            else:
                return {"error": f"LinkedIn API error: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def fetch_vk_stats(
        self,
        access_token: str,
        owner_id: int,
        post_id: int
    ) -> Dict[str, Any]:
        """Получить статистику поста VK"""
        url = "https://api.vk.com/method/wall.getById"
        params = {
            "posts": f"{owner_id}_{post_id}",
            "extended": 1,
            "access_token": access_token,
            "v": "5.199"
        }
        
        try:
            response = await self.http_client.get(url, params=params)
            data = response.json()
            
            if "error" in data:
                return {"error": data["error"].get("error_msg", "VK API error")}
            
            items = data.get("response", {}).get("items", [])
            if items:
                post = items[0]
                return {
                    "views": post.get("views", {}).get("count", 0),
                    "likes": post.get("likes", {}).get("count", 0),
                    "comments": post.get("comments", {}).get("count", 0),
                    "shares": post.get("reposts", {}).get("count", 0),
                    "raw_response": data
                }
            return {"error": "Post not found"}
        except Exception as e:
            return {"error": str(e)}
    
    async def save_analytics(
        self,
        post_id: str,
        platform: str,
        user_id: str,
        stats: Dict[str, Any],
        access_token: str
    ) -> Dict[str, Any]:
        """Сохранить метрики в Supabase"""
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        payload = {
            "post_id": post_id,
            "platform": platform,
            "user_id": user_id,
            "views": stats.get("views") or 0,
            "clicks": stats.get("clicks") or 0,
            "likes": stats.get("likes") or 0,
            "comments": stats.get("comments") or 0,
            "shares": stats.get("shares") or 0,
            "raw_response": stats.get("raw_response"),
            "collected_at": datetime.utcnow().isoformat()
        }
        
        try:
            response = await self.http_client.post(
                f"{SUPABASE_URL}/rest/v1/post_analytics",
                headers=headers,
                json=payload
            )
            
            if response.status_code in (200, 201):
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_analytics_for_post(
        self,
        post_id: str,
        access_token: str
    ) -> Dict[str, Any]:
        """Получить последнюю аналитику для поста"""
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            response = await self.http_client.get(
                f"{SUPABASE_URL}/rest/v1/post_analytics",
                headers=headers,
                params={
                    "post_id": f"eq.{post_id}",
                    "order": "collected_at.desc",
                    "limit": "1"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data[0] if data else None}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_all_analytics(
        self,
        user_id: str,
        access_token: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Получить аналитику всех постов пользователя"""
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            response = await self.http_client.get(
                f"{SUPABASE_URL}/rest/v1/post_analytics",
                headers=headers,
                params={
                    "user_id": f"eq.{user_id}",
                    "select": "*,posts(title,content,platform,scheduled_time,status)",
                    "order": "collected_at.desc",
                    "limit": str(limit)
                }
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}


analytics_service = AnalyticsService()
