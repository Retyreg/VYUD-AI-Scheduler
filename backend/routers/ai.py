"""AI router — multi-provider LLM content generation."""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.ai import AVAILABLE_MODELS, generate_text

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── Платформо-специфичные конфигурации ───────────────────────────────────────

PLATFORM_CONFIGS = {
    "telegram": {
        "optimal":  "700–1200 символов",
        "structure": (
            "Структура: жирный заголовок (1 строка) → цепляющее первое предложение → "
            "основной текст с пустыми строками между абзацами → призыв к действию. "
            "Используй **жирный** для ключевых слов. "
            "3–5 эмодзи равномерно по тексту, не в конце кучей. "
            "Хэштеги — только если тема требует, не больше 3."
        ),
        "length_guides": {
            "short":  "300–500 символов. 1 ёмкий абзац.",
            "medium": "700–1200 символов. 2–3 абзаца с чёткой структурой.",
            "long":   "1300–1800 символов. Заголовок + 3–4 абзаца + CTA.",
        },
    },
    "linkedin": {
        "optimal":  "900–1300 символов",
        "structure": (
            "Структура: сильная первая строка без воды — она видна до кнопки 'ещё' → "
            "пустая строка → 3–5 коротких абзацев по 1–3 строки → "
            "инсайт или вывод → вопрос или CTA для комментариев. "
            "Без markdown-bold. Переносы строк для читаемости. "
            "3–5 хэштегов в самом конце."
        ),
        "length_guides": {
            "short":  "500–700 символов. Хук + 2 абзаца + CTA.",
            "medium": "900–1200 символов. Хук + 4 коротких абзаца + вопрос.",
            "long":   "1200–1800 символов. История: ситуация → инсайт → урок → CTA.",
        },
    },
    "vk": {
        "optimal":  "500–1000 символов",
        "structure": (
            "Структура: цепляющая первая строка (видна в ленте до кнопки 'читать далее') → "
            "основной текст короткими абзацами → эмодзи как маркеры разделов → "
            "вопрос или CTA в конце. "
            "Первые 280 символов критичны — они видны до обрезки. "
            "Эмодзи как визуальные разделители между блоками."
        ),
        "length_guides": {
            "short":  "300–500 символов. Ёмко, shareability.",
            "medium": "600–900 символов. Суть + контекст + CTA.",
            "long":   "900–1400 символов. Детально с примерами, структура через эмодзи.",
        },
    },
}

TONE_DESCRIPTIONS = {
    "professional":  "профессиональный, экспертный, но не сухой",
    "casual":        "разговорный, дружелюбный, как будто пишешь другу",
    "funny":         "с юмором, лёгкий, с самоиронией где уместно",
    "motivational":  "вдохновляющий, энергичный, заряжающий на действие",
    "educational":   "обучающий, структурированный, с примерами и объяснениями",
}

LANGUAGE_NAMES = {
    "ru": "русском",
    "en": "английском",
}

def get_platform_config(platform: str) -> Dict:
    return PLATFORM_CONFIGS.get(platform.lower(), PLATFORM_CONFIGS["telegram"])


# ─── Модели запросов ──────────────────────────────────────────────────────────

class GeneratePostRequest(BaseModel):
    topic: str
    platform: str = "telegram"
    model: str = "llama-3.3-70b-versatile"
    prompt_template: Optional[str] = None
    tone: Optional[str] = "professional"
    length: Optional[str] = "medium"
    language: Optional[str] = "ru"       # ← добавлено, фронт уже шлёт

class ContentPlanRequest(BaseModel):
    topic: str
    platform: str = "telegram"
    model: str = "llama-3.3-70b-versatile"
    days: int = 7
    posts_per_day: int = 1
    tone: Optional[str] = "professional"  # ← добавлено
    language: Optional[str] = "ru"        # ← добавлено


# ─── Эндпоинты ────────────────────────────────────────────────────────────────

@router.get("/models", response_model=List[Dict[str, Any]])
async def list_models():
    return AVAILABLE_MODELS


@router.post("/generate-post")
async def generate_post(req: GeneratePostRequest):
    """Generate a social media post using the specified LLM."""
    cfg = get_platform_config(req.platform)
    length_guide = cfg["length_guides"].get(req.length or "medium", cfg["length_guides"]["medium"])
    tone_desc = TONE_DESCRIPTIONS.get(req.tone or "professional", req.tone or "professional")
    lang_name = LANGUAGE_NAMES.get(req.language or "ru", req.language or "ru")

    if req.prompt_template:
        prompt = (
            req.prompt_template
            .replace("{topic}", req.topic)
            .replace("{platform}", req.platform)
            .replace("{length}", length_guide)
            .replace("{tone}", tone_desc)
            .replace("{language}", lang_name)
        )
    else:
        prompt = (
            f"Напиши пост для {req.platform} на тему: {req.topic}\n\n"
            f"Язык поста: {lang_name}\n"
            f"Тон: {tone_desc}\n"
            f"Целевой объём: {length_guide}\n\n"
            f"Правила форматирования:\n{cfg['structure']}\n\n"
            "Напиши только сам пост. Без вступлений типа 'Вот ваш пост:'. "
            "Без пояснений. Только текст поста."
        )

    system = (
        f"Ты — опытный SMM-специалист и копирайтер для {req.platform} с 10+ годами опыта. "
        f"Ты знаешь, что работает в {req.platform} и как писать тексты, которые читают до конца. "
        "Ты никогда не пишешь шаблонный AI-контент — каждый пост звучит живо и по-человечески. "
        "Отвечай ТОЛЬКО текстом поста, без каких-либо пояснений."
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
    """Generate a multi-day content plan with ready-to-publish posts."""
    cfg = get_platform_config(req.platform)
    total_posts = req.days * req.posts_per_day
    tone_desc = TONE_DESCRIPTIONS.get(req.tone or "professional", req.tone or "professional")
    lang_name = LANGUAGE_NAMES.get(req.language or "ru", req.language or "ru")

    prompt = (
        f"Создай контент-план на {req.days} дней для {req.platform} на тему: {req.topic}\n"
        f"Язык постов: {lang_name}\n"
        f"Тон: {tone_desc}\n"
        f"Количество постов: ровно {total_posts} штук, по {req.posts_per_day} в день.\n\n"
        f"Каждый пост должен быть ГОТОВЫМ к публикации текстом, не идеей и не тезисами.\n"
        f"Целевой объём каждого поста: {cfg['optimal']}.\n"
        f"Правила форматирования: {cfg['structure']}\n\n"
        "Верни JSON-массив. Каждый элемент содержит поля:\n"
        "  - day: число (от 1 до N)\n"
        "  - title: короткое название темы поста (для внутреннего использования)\n"
        "  - content: ПОЛНЫЙ готовый текст поста (не краткое описание — именно пост)\n"
        "  - suggested_time: оптимальное время публикации, например '10:00' или '19:00'\n\n"
        "Чередуй форматы: образовательный, личная история, мнение, полезные советы, кейс.\n\n"
        "ВАЖНО: верни ТОЛЬКО JSON-массив. Никакого markdown. Никакого текста до или после. "
        "Массив начинается с [ и заканчивается ]."
    )

    system = (
        f"Ты — профессиональный контент-стратег и копирайтер для {req.platform}. "
        "Ты создаёшь разнообразный контент — чередуешь форматы и подходы. "
        f"Пишешь на {lang_name} языке. "
        "Возвращаешь ТОЛЬКО валидный JSON-массив, без ничего лишнего."
    )

    try:
        text = await generate_text(prompt=prompt, model=req.model, system=system)

        # Чистим markdown-обёртки если модель их добавила
        clean = text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1]
            clean = clean.rsplit("```", 1)[0].strip()

        try:
            plan = json.loads(clean)
            is_json = True
        except json.JSONDecodeError:
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
