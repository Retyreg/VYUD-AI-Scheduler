"""AI router — multi-provider LLM content generation.

Supports 11 models: OpenAI, Anthropic, Google AI, Groq, HuggingFace.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.ai import AVAILABLE_MODELS, generate_text

logger = logging.getLogger(__name__)

router = APIRouter()


class GeneratePostRequest(BaseModel):
    topic: str
    platform: str = "telegram"
    model: str = "llama-3.3-70b-versatile"
    prompt_template: Optional[str] = None
    tone: Optional[str] = None
    length: Optional[str] = "medium"


class ContentPlanRequest(BaseModel):
    topic: str
    platform: str = "telegram"
    model: str = "llama-3.3-70b-versatile"
    days: int = 7
    posts_per_day: int = 1


@router.get("/models", response_model=List[Dict[str, Any]])
async def list_models():
    """Return all available LLM models grouped by provider."""
    return AVAILABLE_MODELS


@router.post("/generate-post")
async def generate_post(req: GeneratePostRequest):
    """Generate a social media post using the specified LLM."""
    length_guide = {
        "short": "1-2 sentences, very concise",
        "medium": "3-5 sentences",
        "long": "6-10 sentences, detailed",
    }.get(req.length, "3-5 sentences")

    tone_part = f" Tone: {req.tone}." if req.tone else ""

    if req.prompt_template:
        prompt = req.prompt_template.replace("{topic}", req.topic)
    else:
        prompt = (
            f"Write a {req.platform} post about: {req.topic}."
            f"{tone_part} Length: {length_guide}."
            " Use appropriate emojis and formatting for the platform."
        )

    system = (
        f"You are an expert social media content creator for {req.platform}. "
        "Write engaging, platform-appropriate content. "
        "Return only the post text, no extra commentary."
    )

    try:
        text = await generate_text(prompt=prompt, model=req.model, system=system)
        return {"content": text, "model": req.model, "platform": req.platform}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("AI generation error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content-plan")
async def generate_content_plan(req: ContentPlanRequest):
    """Generate a multi-day content plan."""
    total_posts = req.days * req.posts_per_day

    prompt = (
        f"Create a {req.days}-day content plan for {req.platform} about: {req.topic}. "
        f"Generate exactly {total_posts} post ideas, {req.posts_per_day} per day. "
        "For each post provide: day number, title, brief content (2-3 sentences), "
        "best posting time. Format as JSON array with fields: "
        "day, title, content, suggested_time."
    )

    system = (
        "You are a professional content strategist. "
        "Return ONLY valid JSON array, no markdown, no extra text."
    )

    try:
        text = await generate_text(prompt=prompt, model=req.model, system=system)
        # Try to parse as JSON for validation
        import json

        try:
            plan = json.loads(text)
            is_json = True
        except json.JSONDecodeError:
            # AI returned non-JSON despite instructions; return raw text with warning flag
            plan = text
            is_json = False
        return {
            "plan": plan,
            "is_json": is_json,
            "topic": req.topic,
            "days": req.days,
            "model": req.model,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Content plan generation error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
