import os
import httpx
from typing import Optional

class AIService:
    """Универсальный сервис для работы с разными LLM"""
    
    MODELS = {
        # OpenAI
        "gpt-4o": {"provider": "openai", "model": "gpt-4o"},
        "gpt-4o-mini": {"provider": "openai", "model": "gpt-4o-mini"},
        # Anthropic
        "claude-3.5-sonnet": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
        "claude-3-haiku": {"provider": "anthropic", "model": "claude-3-haiku-20240307"},
        # Google
        "gemini-pro": {"provider": "google", "model": "gemini-1.5-pro"},
        "gemini-flash": {"provider": "google", "model": "gemini-1.5-flash"},
        # Groq (fast inference)
        "llama-3.1-70b": {"provider": "groq", "model": "llama-3.1-70b-versatile"},
        "llama-3.1-8b": {"provider": "groq", "model": "llama-3.1-8b-instant"},
        "mixtral-8x7b": {"provider": "groq", "model": "mixtral-8x7b-32768"},
        # HuggingFace
        "qwen-72b": {"provider": "huggingface", "model": "Qwen/Qwen2.5-72B-Instruct"},
        "llama-3-70b-hf": {"provider": "huggingface", "model": "meta-llama/Meta-Llama-3-70B-Instruct"},
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
            return {"ok": False, "error": data.get("error", {}).get("message", "Unknown error")}
    
    async def _google(self, prompt: str, model: str, system: str, max_tokens: int) -> dict:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.google_key}",
                json={"contents": [{"parts": [{"text": full_prompt}]}]},
                timeout=60
            )
            data = response.json()
            if "candidates" in data:
                return {"ok": True, "text": data["candidates"][0]["content"]["parts"][0]["text"]}
            return {"ok": False, "error": data.get("error", {}).get("message", "Unknown error")}
    
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
            return {"ok": False, "error": data.get("error", {}).get("message", "Unknown error")}
    
    async def _huggingface(self, prompt: str, model: str, system: str, max_tokens: int) -> dict:
        full_prompt = f"{system}\n\nUser: {prompt}\n\nAssistant:" if system else f"User: {prompt}\n\nAssistant:"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers={"Authorization": f"Bearer {self.huggingface_key}"},
                json={"inputs": full_prompt, "parameters": {"max_new_tokens": max_tokens}},
                timeout=120
            )
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                text = data[0].get("generated_text", "")
                # Remove prompt from response
                if "Assistant:" in text:
                    text = text.split("Assistant:")[-1].strip()
                return {"ok": True, "text": text}
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
