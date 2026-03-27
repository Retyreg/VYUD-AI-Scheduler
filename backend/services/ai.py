"""Multi-provider AI client supporting 11 LLM models."""

import logging
import os
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# NOTE: Model IDs must be kept in sync with provider releases.
# Check for updates periodically:
#   OpenAI: https://platform.openai.com/docs/models
#   Anthropic: https://docs.anthropic.com/en/docs/about-claude/models
#   Google AI: https://ai.google.dev/gemini-api/docs/models/gemini
#   Groq: https://console.groq.com/docs/models
#   HuggingFace: https://huggingface.co/models
AVAILABLE_MODELS: List[Dict[str, Any]] = [
    # OpenAI
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai", "description": "Best quality"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai", "description": "Fast & cheap"},
    # Anthropic
    {"id": "claude-sonnet-4-5", "name": "Claude Sonnet 4.5", "provider": "anthropic", "description": "High quality"},
    {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "provider": "anthropic", "description": "Fast"},
    # Google AI
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "google", "description": "Google flagship"},
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "google", "description": "Fast Google"},
    # Groq
    {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "provider": "groq", "description": "Fast open-source"},
    {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B", "provider": "groq", "description": "Fastest"},
    {"id": "gemma2-9b-it", "name": "Gemma 2 9B", "provider": "groq", "description": "Google open-source"},
    # HuggingFace
    {"id": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen 2.5 72B", "provider": "huggingface", "description": "Open-source"},
    {"id": "meta-llama/Llama-3.1-70B-Instruct", "name": "Llama 3.1 70B", "provider": "huggingface", "description": "Meta open-source"},
]

_PROVIDER_MAP = {m["id"]: m["provider"] for m in AVAILABLE_MODELS}


async def generate_text(prompt: str, model: str, system: str = "") -> str:
    """Generate text using the specified model. Dispatches to the correct provider."""
    provider = _PROVIDER_MAP.get(model)
    if provider is None:
        raise ValueError(f"Unknown model: {model}")

    logger.info("Generating text with model=%s provider=%s", model, provider)

    if provider == "openai":
        return await _openai(prompt, model, system)
    elif provider == "anthropic":
        return await _anthropic(prompt, model, system)
    elif provider == "google":
        return await _google(prompt, model, system)
    elif provider == "groq":
        return await _groq(prompt, model, system)
    elif provider == "huggingface":
        return await _huggingface(prompt, model, system)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


async def _openai(prompt: str, model: str, system: str) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": model, "messages": messages, "max_tokens": 1024},
        )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


async def _anthropic(prompt: str, model: str, system: str) -> str:
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not configured")
    payload: Dict[str, Any] = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"].strip()


async def _google(prompt: str, model: str, system: str) -> str:
    if not GOOGLE_AI_API_KEY:
        raise ValueError("GOOGLE_AI_API_KEY not configured")
    parts = []
    if system:
        parts.append({"text": system + "\n\n"})
    parts.append({"text": prompt})

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": GOOGLE_AI_API_KEY},
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": parts}]},
        )
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


async def _groq(prompt: str, model: str, system: str) -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": model, "messages": messages, "max_tokens": 1024},
        )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


async def _huggingface(prompt: str, model: str, system: str) -> str:
    if not HUGGINGFACE_API_KEY:
        raise ValueError("HUGGINGFACE_API_KEY not configured")
    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "messages": [{"role": "user", "content": full_prompt}],
                "max_tokens": 1024,
            },
        )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()
