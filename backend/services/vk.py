import httpx
import os

class VKService:
    def __init__(self):
        self.api_url = "https://api.vk.com/method"
        self.api_version = "5.131"

    async def post_to_wall(self, token: str, owner_id: str, text: str) -> dict:
        """
        Публикует пост на стену сообщества VK.
        owner_id: отрицательный ID сообщества (например -123456789)
        token: токен сообщества с правом wall
        """
        params = {
            "owner_id": owner_id,
            "from_group": 1,
            "message": text,
            "access_token": token,
            "v": self.api_version
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/wall.post",
                data=params
            )
            data = response.json()

            if "response" in data:
                return {"ok": True, "post_id": data["response"].get("post_id")}
            else:
                error = data.get("error", {})
                return {
                    "ok": False,
                    "error": error.get("error_msg", "Unknown VK error"),
                    "error_code": error.get("error_code")
                }

    async def get_group_info(self, token: str, group_id: str) -> dict:
        """Получает информацию о сообществе для проверки подключения."""
        params = {
            "group_id": group_id.lstrip("-"),
            "access_token": token,
            "v": self.api_version
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/groups.getById",
                params=params
            )
            data = response.json()

            if "response" in data:
                groups = data["response"].get("groups", data["response"])
                if isinstance(groups, list) and groups:
                    group = groups[0]
                    return {"ok": True, "name": group.get("name"), "id": group.get("id")}
                return {"ok": True, "name": "VK Group", "id": group_id}
            else:
                error = data.get("error", {})
                return {"ok": False, "error": error.get("error_msg", "Unknown error")}
