import httpx
import os

class LinkedInService:
    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.base_url = "https://api.linkedin.com"
    
    async def get_user_id(self) -> str:
        """Получает ID пользователя"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/v2/userinfo", headers=headers)
            data = response.json()
            return data.get("sub")
    
    async def post_to_profile(self, text: str) -> dict:
        """Публикует пост от имени пользователя"""
        user_id = await self.get_user_id()
        if not user_id:
            return {"ok": False, "error": "Could not get user ID"}
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202401"
        }
        
        payload = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2/ugcPosts",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 201:
                return {"ok": True, "id": response.headers.get("x-restli-id")}
            else:
                return {"ok": False, "error": response.text, "status": response.status_code}

    async def post_to_organization(self, text: str) -> dict:
        """Алиас для совместимости"""
        return await self.post_to_profile(text)
