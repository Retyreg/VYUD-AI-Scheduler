from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.ai import AIService

router = APIRouter()
ai = AIService()

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "gpt-4o"
    system: Optional[str] = None

class ContentPlanRequest(BaseModel):
    topic: str
    platform: str = "telegram"
    days: int = 7
    model: str = "gpt-4o"

class GeneratePostRequest(BaseModel):
    topic: str
    platform: str = "telegram"
    tone: str = "professional"
    model: str = "gpt-4o"

@router.get("/models")
async def get_models():
    """Список доступных LLM моделей"""
    return ai.get_available_models()

@router.post("/generate")
async def generate_text(req: GenerateRequest):
    """Генерация текста через выбранную LLM"""
    result = await ai.generate(req.prompt, req.model, req.system)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"text": result["text"], "model": req.model}

@router.post("/content-plan")
async def generate_content_plan(req: ContentPlanRequest):
    """Генерация контент-плана на N дней"""
    system = """Ты — эксперт по SMM и контент-маркетингу. 
Создавай контент-планы в формате JSON массива."""

    prompt = f"""Создай контент-план на {req.days} дней для {req.platform} на тему: "{req.topic}"

Верни JSON массив постов в формате:
[
  {{"day": 1, "title": "Заголовок", "description": "Краткое описание поста", "type": "educational/entertaining/promotional/engaging"}},
  ...
]

Только JSON, без пояснений."""

    result = await ai.generate(prompt, req.model, system)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Пытаемся распарсить JSON
    import json
    try:
        text = result["text"].strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        plan = json.loads(text)
    except:
        plan = result["text"]
    
    return {"plan": plan, "model": req.model, "days": req.days}

@router.post("/generate-post")
async def generate_post(req: GeneratePostRequest):
    """Генерация поста для соцсетей"""
    platform_limits = {
        "telegram": 4096,
        "linkedin": 3000,
        "twitter": 280
    }
    max_chars = platform_limits.get(req.platform, 2000)
    
    system = f"""Ты — профессиональный SMM-копирайтер.
Пиши посты для {req.platform} в {req.tone} тоне.
Максимум {max_chars} символов.
Используй эмодзи уместно.
Добавляй призыв к действию."""

    prompt = f"""Напиши пост для {req.platform} на тему: "{req.topic}"

Тон: {req.tone}
Платформа: {req.platform}

Верни только текст поста, без пояснений."""

    result = await ai.generate(prompt, req.model, system)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"content": result["text"], "model": req.model, "platform": req.platform}
