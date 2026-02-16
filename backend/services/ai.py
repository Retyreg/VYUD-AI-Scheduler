import os
import httpx
from typing import Optional

class AIService:
    """Универсальный сервис для работы с разными LLM"""
    
    MODELS = {
        # OpenAI
        "gpt-4o": {"provider": "openai", "model": "gpt-4o"},
        "gpt-4o-mini": {"provider": "openai", "model": "gpt-4o-mini"},
        # Anthropic (обновлённые модели)
        "claude-sonnet-4": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
        "claude-3.5-sonnet": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
        "claude-3.5-haiku": {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
        # Google (обновлённые модели)
        "gemini-2.0-flash": {"provider": "google", "model": "gemini-2.0-flash"},
        "gemini-1.5-flash": {"provider": "google", "model": "gemini-1.5-flash"},
        # Groq (актуальные модели)
        "llama-3.3-70b": {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        "llama-3.1-8b": {"provider": "groq", "model": "llama-3.1-8b-instant"},
        "gemma2-9b": {"provider": "groq", "model": "gemma2-9b-it"},
        # HuggingFace (через новый router)
        "qwen-72b": {"provider": "huggingface", "model": "Qwen/Qwen2.5-72B-Instruct"},
        "llama-3.1-70b-hf": {"provider": "huggingface", "model": "meta-llama/Llama-3.1-70B-Instruct"},
    }
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.google_key = os.getenv("GOOGLE_AI_API_KEY", "")
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.huggingface_key = os.getenv("HUGGINGFACE_API_KEY", "")
        self.replicate_key = os.getenv("REPLICATE_API_TOKEN", "")
    
    async def generate(self, prompt: str, model: str = "gpt-4o", system: str = None, max_tokens: int = 2000) -> dict:
        """Генерирует текст используя выбранную модель"""
        if model not in self.MODELS:
            return {"ok": False, "error": f"Unknown model: {model}"}
        
        config = self.MODELS[model]
        provider = config["provider"]
        
        try:
            if provider == "openai":
                return await self._openai(prompt, config["model"], system, max_tokens)
            elif provider == "anthropic":
                return await self._anthropic(prompt, config["model"], system, max_tokens)
            elif provider == "google":
                return await self._google(prompt, config["model"], system, max_tokens)
            elif provider == "groq":
                return await self._groq(prompt, config["model"], system, max_tokens)
            elif provider == "huggingface":
                return await self._huggingface(prompt, config["model"], system, max_tokens)
            else:
                return {"ok": False, "error": f"Unknown provider: {provider}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def _openai(self, prompt: str, model: str, system: str, max_tokens: int) -> dict:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.openai_key}"},
                json={"model": model, "messages": messages, "max_tokens": max_tokens},
                timeout=60
            )
            data = response.json()
            if "choices" in data:
                return {"ok": True, "text": data["choices"][0]["message"]["content"]}
            return {"ok": False, "error": data.get("error", {}).get("message", "Unknown error")}
    
    async def _anthropic(self, prompt: str, model: str, system: str, max_tokens: int) -> dict:
        async with httpx.AsyncClient() as client:
            body = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system:
                body["system"] = system
            
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json=body,
                timeout=60
            )
            data = response.json()
            if "content" in data:
                return {"ok": True, "text": data["content"][0]["text"]}
            return {"ok": False, "error": data.get("error", {}).get("message", str(data))}
    
    async def _google(self, prompt: str, model: str, system: str, max_tokens: int) -> dict:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.google_key}",
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens}
                },
                timeout=60
            )
            data = response.json()
            if "candidates" in data:
                return {"ok": True, "text": data["candidates"][0]["content"]["parts"][0]["text"]}
            return {"ok": False, "error": data.get("error", {}).get("message", str(data))}
    
    async def _groq(self, prompt: str, model: str, system: str, max_tokens: int) -> dict:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.groq_key}"},
                json={"model": model, "messages": messages, "max_tokens": max_tokens},
                timeout=60
            )
            data = response.json()
            if "choices" in data:
                return {"ok": True, "text": data["choices"][0]["message"]["content"]}
            return {"ok": False, "error": data.get("error", {}).get("message", str(data))}
    
    async def _huggingface(self, prompt: str, model: str, system: str, max_tokens: int) -> dict:
        """HuggingFace через новый router API"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://router.huggingface.co/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.huggingface_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens
                },
                timeout=120
            )
            data = response.json()
            if "choices" in data:
                return {"ok": True, "text": data["choices"][0]["message"]["content"]}
            return {"ok": False, "error": str(data)}
    
    def get_available_models(self) -> list:
        """Возвращает список доступных моделей"""
        available = []
        for name, config in self.MODELS.items():
            provider = config["provider"]
            has_key = False
            if provider == "openai" and self.openai_key:
                has_key = True
            elif provider == "anthropic" and self.anthropic_key:
                has_key = True
            elif provider == "google" and self.google_key:
                has_key = True
            elif provider == "groq" and self.groq_key:
                has_key = True
            elif provider == "huggingface" and self.huggingface_key:
                has_key = True
            
            if has_key:
                available.append({"name": name, "provider": provider})
        return available
