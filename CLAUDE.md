# CLAUDE.md

> Контекст-файл для Claude Code / агентов AI при работе с VYUD Publisher. Автоматически читается в начале каждой сессии.

---

## 📌 Проект

**VYUD Publisher** — внутренний SaaS для автоматизации создания, планирования и публикации контента в соцсетях с помощью AI.

- **URL:** https://publisher.vyud.tech
- **Репозиторий:** https://github.com/Retyreg/VYUD-AI-Scheduler
- **Версия:** v2.1
- **Сервер:** `38.180.243.126` (Ubuntu 22.04)
- **Часть экосистемы:** VYUD AI (vyud.tech, app.vyud.online, crm.vyud.online)

### Целевые платформы постинга
- ✅ Telegram (каналы через Bot API) — работает
- ✅ LinkedIn (OAuth) — работает
- 🔜 VK (API, group numeric IDs) — в роадмапе
- 🔜 Instagram (Graph API) — в роадмапе

### Конкурентное преимущество vs Postiz/Buffer
1. **Мультимодельный AI** — 11 LLM (Anthropic, OpenAI, Google, Groq, HuggingFace, Replicate)
2. **Русский рынок первым** — Telegram-каналы + VK приоритетнее Twitter/Threads
3. **Интеграция с VYUD AI** — курсы из документов → автопромо в соцсетях

---

## 🏗️ Архитектура

### Высокоуровневая схема

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   SvelteKit     │────▶│    FastAPI       │────▶│   Supabase       │
│   (port 3000)   │     │   (port 8000)    │     │   (PostgreSQL)   │
│   Frontend      │◀────│    Backend       │◀────│   + Auth + RLS   │
└─────────────────┘     └──────────────────┘     └──────────────────┘
        │                        │                        
        │                        ├──▶ APScheduler (автопостинг)
        │                        ├──▶ AI Service (11 LLM)
        │                        ├──▶ Telegram Bot API
        │                        └──▶ LinkedIn API
        │
        └──▶ Nginx (SSL, reverse proxy)
```

### Технологический стек (ОБЯЗАТЕЛЬНЫЙ)

**Frontend:**
- SvelteKit + `@sveltejs/adapter-node`
- TailwindCSS (только utility-классы, никакого Bootstrap)
- systemd сервис `publisher-frontend` (порт 3000)

**Backend:**
- FastAPI (Python 3.10+)
- Uvicorn + systemd сервис `publisher-api` (порт 8000)
- Supabase REST API (HTTP, **НЕ SDK** — см. ниже "Критические решения")
- APScheduler для автопостинга

**База данных:**
- Supabase (PostgreSQL + GoTrue Auth + RLS)
- Доступ через прямые HTTP-запросы к REST API с JWT
- Для конфликтов RLS (settings/accounts) — service role key

**AI-провайдеры:**
| Провайдер | Модели | Назначение |
|-----------|--------|------------|
| Anthropic | claude-opus-4-7, claude-sonnet-4-6, claude-haiku-4-5 | Сложная генерация + дешёвый массовый контент |
| OpenAI | gpt-4o, gpt-4o-mini | Качественный текст, DALL-E 3 |
| Google AI | gemini-pro, gemini-flash | Быстрый текст |
| Groq | llama-3.1-70b/8b, mixtral-8x7b | Быстрая генерация |
| HuggingFace | qwen-72b, llama-3-70b-hf | Open-source |
| Replicate | Flux, SDXL | Генерация изображений |

**Инфраструктура:**
- Nginx + Let's Encrypt SSL
- Systemd watchdog (каждые 5 мин) → автоматический рестарт `publisher-api` при падении event loop
- UptimeRobot для внешнего health-мониторинга
- Journald capped at 100MB

---

## 📂 Структура проекта

```
/root/publisher_app/
├── backend/
│   ├── main.py                 # FastAPI entrypoint (v2.1.0)
│   ├── .env                    # API ключи (НИКОГДА не в Git)
│   ├── venv/                   # Python venv
│   ├── routers/
│   │   ├── posts.py            # CRUD постов + расписание
│   │   ├── accounts.py         # Подключение TG/LinkedIn
│   │   ├── ai.py               # AI генерация (мультипровайдер)
│   │   └── analytics.py        # Аналитика постов
│   └── services/
│       ├── scheduler.py        # APScheduler + статусная машина
│       ├── telegram.py         # Telegram Bot API
│       ├── linkedin.py         # LinkedIn API
│       ├── ai.py               # Универсальный AI-клиент
│       └── supabase_client.py  # HTTP-клиент к Supabase REST
├── frontend~/
│   ├── src/
│   │   └── routes/
│   │       ├── +layout.svelte          # Навигация
│   │       ├── +page.svelte            # Календарь постов
│   │       ├── create/+page.svelte     # Создание с превью
│   │       ├── generate/+page.svelte   # AI + контент-план
│   │       ├── analytics/+page.svelte  # Аналитика
│   │       └── settings/+page.svelte   # Аккаунты
│   ├── svelte.config.js
│   └── package.json
└── nginx/
    └── publisher.vyud.tech.conf
```

---

## 🔑 Критические архитектурные решения (ПРОЧИТАЙ ОБЯЗАТЕЛЬНО)

1. **Supabase Python SDK не используем.** Был конфликт websockets с Python 3.10 — перешли на прямые HTTP-запросы к REST API. НЕ предлагай вернуться к SDK без явного запроса.

2. **Service role key используется только в backend и только для операций с конфликтом RLS** (settings, accounts). Для user-facing операций — JWT пользователя.

3. **APScheduler + watchdog.** Uvicorn event loop может «умереть» при работающем процессе. Решение: systemd-таймер каждые 5 мин проверяет `/health`, при неуспехе рестартует сервис. `TimeoutStopSec=15` в unit-файле.

4. **Localstorage ключ для access_token — это `'access_token'`**, не `'supabase_session'`. Частая ошибка.

5. **Nginx `proxy_read_timeout` расширен до 180s** для долгих AI-запросов. Не уменьшать.

6. **Double-prefix routing gotcha.** Если роутер объявлен с `prefix="/x"` и `main.py` подключает его с `prefix="/api/x"`, роуты резолвятся в `/api/x/x/...`. Проверяй префиксы при добавлении роутеров.

7. **VK API требует numeric group ID** (например `-235903023`), а не текстовый username. Всегда резолвим через `groups.getById` при подключении.

8. **`.gitignore` обязан покрывать `.env`.** Один раз были утечки API-ключей через git — все ключи были ротированы. Перед коммитом — проверяй `git status`.

---

## 🎯 Стандарты кода

### Безопасность (приоритет №1)

```python
# ✅ Правильно
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set")

# ❌ Никогда
api_key = "sk-proj-..."
```

### Обработка ошибок

**Backend (FastAPI):**
```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

try:
    result = await ai.generate(prompt, model, system)
except ProviderError as e:
    logger.error(f"AI provider failed: {e}")
    raise HTTPException(status_code=502, detail=f"AI provider error: {e}")
except Exception as e:
    logger.exception("Unexpected error in ai.generate")
    raise HTTPException(status_code=500, detail="Internal server error")
```

**Frontend (SvelteKit):**
```svelte
<script>
  let error = null;
  let loading = false;

  async function submit() {
    loading = true;
    error = null;
    try {
      const res = await fetch('/api/posts/', { method: 'POST', ... });
      if (!res.ok) throw new Error((await res.json()).detail);
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }
</script>

{#if error}
  <div class="text-red-400 bg-red-900/20 p-3 rounded">{error}</div>
{/if}
```

### Типизация

- Python: `from pydantic import BaseModel` для всех DTO и API-моделей
- TypeScript/Svelte: строгая типизация, никаких `any` без комментария-обоснования

---

## 🚀 API-эндпоинты (текущие)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Healthcheck (используется watchdog) |
| GET | `/api/posts/` | Список постов |
| POST | `/api/posts/` | Создать пост |
| GET | `/api/posts/{id}` | Получить пост |
| PATCH | `/api/posts/{id}` | Обновить пост |
| DELETE | `/api/posts/{id}` | Удалить пост |
| GET | `/api/accounts/` | Список аккаунтов |
| POST | `/api/accounts/telegram` | Подключить Telegram |
| POST | `/api/accounts/linkedin` | Подключить LinkedIn |
| GET | `/api/ai/models` | Список доступных LLM |
| POST | `/api/ai/generate-post` | Сгенерировать пост |
| POST | `/api/ai/content-plan` | Сгенерировать контент-план |
| GET | `/api/analytics/` | Аналитика постов |

---

## 📊 Схема БД (Supabase)

**Основные таблицы:**
- `posts` — посты (id, content, platform, status, scheduled_at, published_at, platform_post_id, user_id)
- `accounts` — подключённые соцсети (id, platform, credentials_encrypted, user_id)
- `post_analytics` — аналитика (post_id, views, likes, shares, clicks, fetched_at)
- `prompts` — AI-шаблоны (планируется)

**RLS:**
- Все таблицы имеют RLS-политики на `auth.uid() = user_id`
- `service_role` может обходить RLS — используется только в backend

**Статусная машина поста:**
```
draft → scheduled → publishing → published
                 ↓              ↓
              cancelled      failed → retrying → published
```

---

## 🛠️ Команды деплоя

### Backend
```bash
ssh root@38.180.243.126 '
  cd /root/publisher_app && \
  git pull origin main && \
  systemctl restart publisher-api && \
  sleep 2 && \
  systemctl status publisher-api --no-pager | head -20
'
```

### Frontend
```bash
ssh root@38.180.243.126 '
  cd /root/publisher_app/frontend~ && \
  git pull origin main && \
  npm run build && \
  systemctl restart publisher-frontend
'
```

### Healthcheck
```bash
curl -s https://publisher.vyud.tech/api/health
curl -s http://38.180.243.126:8000/api/ai/models | jq
```

### Логи
```bash
ssh root@38.180.243.126 'journalctl -u publisher-api -f --since "5 min ago"'
ssh root@38.180.243.126 'journalctl -u publisher-frontend -f --since "5 min ago"'
```

### Экстренный рестарт
```bash
ssh root@38.180.243.126 'systemctl restart publisher-api publisher-frontend nginx'
```

---

## 📌 Текущий функционал (v2.1)

| Функция | Статус |
|---------|--------|
| Календарь постов | ✅ |
| Создание постов с превью | ✅ |
| Telegram автопостинг | ✅ |
| LinkedIn автопостинг | ✅ |
| AI генерация постов (11 LLM) | ✅ |
| AI контент-план | ✅ |
| UTM-метки | ✅ |
| SSL (HTTPS) | ✅ |
| Управление аккаунтами | ✅ |
| Аналитика постов (Telegram через TGStat) | ✅ |

---

## 🗺️ Роадмап

| Фича | Приоритет | Описание |
|------|-----------|----------|
| Рефакторинг провайдеров в `SocialProvider` паттерн | 🔥 Высокий | Единый интерфейс для всех соцсетей (готовит почву для VK/Instagram) |
| VK интеграция | 🔥 Высокий | Автопостинг через API, numeric group IDs |
| Статусная машина постов + ретраи | 🔥 Высокий | `draft → scheduled → publishing → published/failed → retrying` с exponential backoff |
| Редактор промптов | Высокий | Таблица `prompts` + UI управления шаблонами |
| Instagram интеграция | Средний | Graph API, только business-аккаунты |
| Медиа (картинки/видео) | Средний | Supabase Storage + превью + компрессия |
| Аналитика для LinkedIn/VK | Средний | Бесплатные API платформ |
| Rich text редактор | Средний | Tiptap для Svelte или Editor.js |
| Генерация изображений | Средний | DALL-E 3 / Flux / SDXL через Replicate |
| Public REST API + API-keys | Средний | Для интеграций с N8N/Make.com |
| Browser extension | Низкий | Chrome MV3 для быстрого постинга |
| Монетизация Publisher | Низкий | Отдельный SaaS, Stripe, tiers |

---

## 🤝 Связь с экосистемой VYUD

| Продукт | URL / Адрес | Назначение |
|---------|-------------|------------|
| **VYUD AI** (web) | app.vyud.online | Основное приложение (Streamlit) — курсы из документов |
| **VYUD Bot** | @VyudAiBot | Telegram-бот для генерации тестов |
| **VYUD Publisher** | publisher.vyud.tech | AI-контент + автопостинг (этот проект) |
| **VYUD CRM** | crm.vyud.online | CRM для экспертов (Streamlit, порт 8502) |
| **B2B лендинг** | vyud.tech | Корпоративные клиенты |
| **B2C лендинг** | vyud.online | Индивидуальные пользователи |
| **Админ-панель** | :8503 | Аналитика пользователей |
|**VYUD HIRE**| @VyudHireBot | AI-powered платформа управления талантами

**VPS основной VYUD AI:** `38.180.229.254`
**VPS Publisher:** `38.180.243.126`
**VPS VYUD HIRE:** 78.140.246.158
---

## ⚖️ Приоритеты при конфликтах

1. **Безопасность** > Скорость (ключи только в `.env`, никогда в Git)
2. **Стабильность** > Новые фичи (сначала чиним, потом добавляем)
3. **Простота** > Элегантность (работающий код лучше красивого неработающего)
4. **Сначала core, потом fancy UI** (нет смысла в Tiptap, если автопостинг иногда молча падает)

---

## 🧭 Правила работы для агента AI

### При написании кода
1. Краткое объяснение (1-2 предложения)
2. Полный рабочий код с комментариями в ключевых местах
3. Инструкция по интеграции (какой файл, куда вставить, как задеплоить)

### При дебаге
Структурный подход:
```
1. Симптом: [что сломалось]
2. Вероятная причина: [гипотеза]
3. Диагностика: [команды для проверки]
4. Решение: [конкретные шаги]
```

Начинай всегда с: health → systemd status → journalctl → curl endpoint → код.

### При ревью идеи
- Если идея хорошая → поддержи и предложи реализацию
- Если есть риски → назови их прямо + альтернатива
- Если идея плохая → скажи честно, объясни почему, дай лучший путь

### Чего НЕ делать
- ❌ НЕ предлагать Prisma, Next.js, Temporal или NestJS — наш стек зафиксирован
- ❌ НЕ возвращаться к Supabase Python SDK без явного запроса
- ❌ НЕ писать маркетинговые тексты / копирайтинг / UX-копи (это зона партнёра)
- ❌ НЕ коммитить `.env` или любые секреты
- ❌ НЕ делать massive refactors за один PR — дробим на маленькие этапы

### Стиль общения
- Прямо, по делу, без воды
- Технически точно — если не уверен, говори «не знаю, нужно проверить»
- Код первым, объяснения вторым (если партнёр знает контекст)

---

## 📚 Полезные ссылки

- Supabase docs: https://supabase.com/docs
- FastAPI: https://fastapi.tiangolo.com
- SvelteKit: https://svelte.dev/docs/kit/introduction
- Anthropic API: https://docs.claude.com
- Telegram Bot API: https://core.telegram.org/bots/api
- LinkedIn API: https://learn.microsoft.com/en-us/linkedin/
- VK API: https://dev.vk.com/ru/method
