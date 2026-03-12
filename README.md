# VYUD Publisher

**AI-powered social media automation platform** for content creation, scheduling, and multi-platform publishing.

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](https://github.com/Retyreg/VYUD-AI-Scheduler/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/demo-publisher.vyud.tech-purple.svg)](https://publisher.vyud.tech)

Part of the **VYUD AI ecosystem** ([vyud.tech](https://vyud.tech)) - transforming content creation through artificial intelligence.

## ⚡ Quick Start (Local Development)

### Prerequisites
- Python 3.8+
- Git

### 1. Clone the repository
```bash
git clone https://github.com/Retyreg/VYUD-AI-Scheduler.git
cd VYUD-AI-Scheduler
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
```
Open `.env` in your terminal editor and replace the placeholder values with your real API keys.

**Choose any editor you like:**

```bash
# nano — simplest, beginner-friendly (save: Ctrl+O → Enter → Ctrl+X)
nano .env

# vim — classic terminal editor (save & exit: Esc → :wq → Enter)
vim .env

# VS Code (if installed)
code .env

# macOS default app (opens in TextEdit or your associated editor)
open .env
```

The file contains these variables — fill in the real values:
```
GROQ_API_KEY=your-groq-api-key-here
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
TELEGRAM_CHAT_ID=your-telegram-chat-id-here
LINKEDIN_ACCESS_TOKEN=your-linkedin-access-token-here
LINKEDIN_PROFILE_ID=your-linkedin-profile-id-here
```

*(Optional)* If you use the Google Gemini integration in Streamlit, also copy the Streamlit secrets template:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Then open `.streamlit/secrets.toml` and add your `GEMINI_API_KEY`.

### 4. Run the application

**Flask API server** (port 5000):
```bash
python app.py
```

**Streamlit UI** (port 8501) — in a separate terminal:
```bash
streamlit run streamlit_app.py
```

**Auto-posting script** (generate and post AI content):
```bash
python auto_post.py
```

> **Note:** The Flask API must be running before starting the Streamlit UI.

---

## 🚀 Features

### Content Management
- **📅 Visual Calendar** - Drag-and-drop scheduling with monthly/weekly views
- **✨ AI Generation** - 11 LLM models including GPT-4o, Claude, Gemini, Llama
- **📝 Post Editor** - Rich text editing with real-time preview
- **🔄 Batch Operations** - Bulk scheduling and content planning

### AI-Powered Content
- **🤖 Multi-Model Support** - OpenAI, Anthropic, Google AI, Groq, HuggingFace
- **📋 Template Library** - Customizable prompt templates with variables
- **🎯 Platform Optimization** - Content tailored for each social platform
- **📊 Content Planning** - AI-generated editorial calendars

### Multi-Platform Publishing
- **📱 Telegram** - Channel automation with Bot API
- **💼 LinkedIn** - Professional content publishing  
- **🔜 Instagram & VK** - Coming soon

### Management & Analytics
- **👥 Account Management** - Multi-account support with unified dashboard
- **📈 Performance Tracking** - UTM tracking and engagement metrics
- **🔐 Secure Storage** - Encrypted credentials and API keys
- **⚡ Real-time Updates** - Live status tracking and notifications

## 🏗️ Architecture

### Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | SvelteKit + TailwindCSS | Reactive UI with modern styling |
| **Backend** | FastAPI + Python | High-performance async API |
| **Database** | Supabase (PostgreSQL) | Real-time data with built-in auth |
| **Scheduling** | APScheduler | Automated post publishing |
| **AI Integration** | Multiple LLM APIs | Content generation |
| **Infrastructure** | Ubuntu VPS + Nginx | Production deployment |

## 🔌 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/posts/` | List posts; filter with `?status=scheduled` or `?platform=Telegram` |
| `POST` | `/api/posts/` | Create new post (`status` defaults to `"scheduled"`) |
| `PATCH` | `/api/posts/{id}` | Update post fields (status, content, timestamp) |
| `DELETE` | `/api/posts/{id}` | Delete post |

> **Legacy endpoints** (kept for backward compatibility):
> `POST /post` and `GET /post/history` still work but return tuple arrays instead of objects.

### AI Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ai/models` | Available LLM models |
| `POST` | `/api/ai/generate-post` | Generate social media post |
| `POST` | `/api/ai/content-plan` | Create content calendar |

### Prompt Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/prompts/` | List prompt templates |
| `POST` | `/api/prompts/` | Create new template |
| `PATCH` | `/api/prompts/{id}` | Update template |
| `DELETE` | `/api/prompts/{id}` | Delete template |

## ✅ Recent Fixes & Next Steps

### What was fixed (PR: copilot/fix-posts-calendar-issue)

| # | File | Problem | Fix |
|---|------|---------|-----|
| 1 | `auto_post.py` | Published posts were **never saved to the database** — invisible in any calendar | Implement `scheduled → success/error` lifecycle: save post as `scheduled` before publishing, PATCH to `success`/`error` after |
| 2 | `app.py` | `timestamp` stored as `NULL` when caller omitted the field — calendar silently skipped those rows | Auto-fill with `datetime.now(UTC)` when field is absent |
| 3 | `app.py` | Only `/post` and `/post/history` existed — publisher.vyud.tech needs `/api/posts/` with status/platform filtering and PATCH/DELETE | Added full REST `/api/posts/` endpoints; added PostgreSQL support via `DATABASE_URL` env var |
| 4 | `streamlit_app.py` | Free-text timestamp input could be blank or malformed | Replaced with `st.date_input` + `st.time_input`; calendar header shows **Всего / Запланировано** counter |

### Deploy to server (v2.1 FastAPI)

> **Если видишь `bash: scripts/deploy.sh: No such file or directory`** — сервер на ветке `main`, а скрипты
> живут в PR-ветке. Используй **Путь A** ниже (переключить ветку — 10 секунд).

---

#### 🆘 Если попал в merge conflict (CONFLICT modify/delete: .streamlit/secrets.toml)

Сервер завис с незавершённым мержем. Выполни **по очереди**:

```bash
cd ~/publisher_app

# 1. Прерываем мерж — возвращаем ветку в чистое состояние
git merge --abort

# 2. Проверяем что всё чисто
git status   # должно быть "nothing to commit, working tree clean"

# 3. Теперь деплоим (исправленный скрипт тянет с правильной ветки)
bash scripts/deploy.sh --setup-venv
```

> ℹ️ **Почему возник конфликт:** старая версия `deploy.sh` всегда тянула `origin main`, даже когда сервер
> находится на PR-ветке. Это вызывало modify/delete конфликт в `.streamlit/secrets.toml` (файл удалён
> в PR-ветке, но существует в истории `main`). Исправлено — новый `deploy.sh` определяет текущую ветку
> автоматически (`CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)`).

---

#### ✅ Путь A — переключить сервер на PR-ветку (скрипты появятся сразу)

```bash
cd ~/publisher_app
git fetch origin
git checkout copilot/fix-posts-calendar-issue   # скрипты появятся немедленно
bash scripts/deploy.sh --setup-venv             # теперь работает
```

После мержа PR в `main` переключись обратно:
```bash
git checkout main && git pull --no-rebase origin main
```

---

#### ✅ Путь B — без переключения ветки (полностью ручной)

Если нельзя менять ветку, выполни **по очереди**:

```bash
cd ~/publisher_app

# 1. Подтянуть код
git pull --no-rebase origin main

# 2. Создать venv и поставить зависимости (~2 мин)
python3 -m venv backend/venv
backend/venv/bin/pip install --upgrade pip
backend/venv/bin/pip install -r backend/requirements.txt

# 3. Запустить сервис
systemctl restart publisher-api

# 4. Проверить — должно вернуть {"status":"ok","version":"2.1.0"}
curl -s http://localhost:8000/health
```

> ⚠️ Команды — строго по очереди. `systemctl restart` до создания venv → сервис упадёт с `203/EXEC`.

---

#### После мержа PR — стандартный деплой

```bash
cd ~/publisher_app
bash scripts/deploy.sh                  # бэкенд (обычный деплой)
bash scripts/deploy.sh --setup-venv     # пересоздать venv
bash scripts/deploy.sh --with-frontend  # бэкенд + пересборка фронтенда
```

`scripts/deploy.sh` делает автоматически: git pull → проверка venv → pip install → systemctl restart → health check.

---

#### 🔍 Диагностика — почему упал publisher-api

```bash
# 1. Статус сервиса
systemctl status publisher-api --no-pager -l | head -20

# 2. Последние логи
journalctl -u publisher-api -n 50 --no-pager

# 3. Health check
curl -s http://localhost:8000/health

# 4. Проверка диска (переполнение диска молча убивает uvicorn!)
df -h && du -sh /var/log/journal/
```

Частые причины падения сервиса:
| Симптом | Причина | Фикс |
|---------|---------|------|
| `203/EXEC` в статусе | venv не существует или uvicorn не установлен | Пересоздать venv (Путь A или B выше) |
| Сервис active но API не отвечает | uvicorn event loop умер | `systemctl restart publisher-api` |
| Диск заполнен (df показывает 100%) | journald логи переполнили диск | `journalctl --vacuum-size=50M && systemctl restart publisher-api` |
| Запросы зависают | nginx timeout < времени AI-генерации | Проверить `proxy_read_timeout 120s` в nginx конфиге |

#### Фронтенд (если нужно пересобрать)

```bash
cd ~/publisher_app/frontend~
npm install          # только первый раз или после обновления package.json
npm run build        # собрать
systemctl restart publisher-frontend
```

> **Примечание:** Фронтенд не нужно пересобирать при каждом деплое — он стабилен пока не меняются `.svelte` файлы.

### Fix NULL timestamps in existing posts

```bash
# Run once after deploying — safe to run multiple times (idempotent)
python scripts/fix_null_timestamps.py

# Or point at a specific DB path:
python scripts/fix_null_timestamps.py /var/data/posts.db
```

Posts that had no timestamp are set to `1970-01-01T00:00:00` so they appear
in the calendar rather than disappearing silently.  
Update them to the correct date via the Streamlit UI or:

```bash
curl -X PATCH http://localhost:5000/api/posts/{id} \
  -H "Content-Type: application/json" \
  -d '{"timestamp": "2026-03-01T10:00:00"}'
```

### Migrate to Supabase (PostgreSQL)

`app.py` now supports PostgreSQL transparently — just set `DATABASE_URL` in `.env`:

```bash
# .env
DATABASE_URL=postgresql://postgres:your-password@db.xxxx.supabase.co:5432/postgres
```

Steps:
1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Copy the **Connection string** from Settings → Database → Connection string → URI
3. Paste it as `DATABASE_URL` in your server `.env`
4. Restart Flask — `init_db()` will create the `post_history` table automatically

No code changes needed. SQLite remains the default when `DATABASE_URL` is not set.

---

## 🛣️ Roadmap

### v2.3 (Q2 2026)
- [ ] Instagram integration via Graph API
- [ ] VK.com publishing support
- [ ] Advanced analytics dashboard
- [ ] Team collaboration features

### v2.4 (Q3 2026)
- [ ] AI image generation (DALL-E, Midjourney)
- [ ] Content A/B testing
- [ ] Webhook integrations
- [ ] Mobile app (React Native)

## 🏢 About VYUD AI

VYUD Publisher is part of the VYUD AI ecosystem, transforming how content creators and businesses leverage artificial intelligence for digital marketing.

**Other VYUD Products:**
- [VYUD AI](https://vyud.online) - Turn documents into interactive courses
- [VYUD Bot](https://t.me/VyudAiBot) - Telegram AI assistant
- [VYUD CRM](https://crm.vyud.online) - AI-powered customer management

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Retyreg/VYUD-AI-Scheduler/issues)
- **Email**: support@vyud.tech

---

**Built with ❤️ by the VYUD AI Team**

[Website](https://vyud.tech) • [LinkedIn](https://linkedin.com/company/vyud-ai)
