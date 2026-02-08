import httpx
from typing import Optional

class TelegramService:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(
        self, 
        chat_id: str, 
        text: str,
        parse_mode: str = "HTML"
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                }
            )
            return response.json()
    
    async def get_me(self) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/getMe")
            return response.json()
    
    async def get_chat(self, chat_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/getChat",
                params={"chat_id": chat_id}
            )
            return response.json()
