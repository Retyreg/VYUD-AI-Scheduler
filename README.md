# VYUD Publisher

**AI-powered social media automation platform** — create, schedule, and publish content across Telegram, LinkedIn and VK using 11 language models.

[![Version](https://img.shields.io/badge/version-2.3.0-blue.svg)](https://github.com/Retyreg/VYUD-AI-Scheduler/releases/tag/v2.3.0)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Live](https://img.shields.io/badge/live-publisher.vyud.tech-blueviolet.svg)](https://publisher.vyud.tech)

Part of the **VYUD AI ecosystem** — [vyud.tech](https://vyud.tech)

---

## ✨ What's New in v2.3

| Feature | Details |
|---------|---------|
| 🤖 **AI → Publish in one flow** | After generating a post, immediately draft / schedule / publish to a channel |
| 📋 **Content plan → Supabase** | Save AI content plan items as scheduled posts with auto-calculated dates |
| 📊 **Real analytics** | Live metrics from Telegram (`getChatMemberCount`) and LinkedIn (`socialMetadata`) |
| 🌐 **EN / RU localization** | Full interface toggle — all pages, nav, toasts, labels |
| 🎨 **Brand identity** | SVG favicon, logo mark, Syne + DM Sans fonts, VYUD blue `#0D7EFF` |
| 🧠 **Educational tone** | New "Scientific / Educational" tone of voice added to AI generation |
| 📝 **Larger topic field** | Topic / Idea textarea expanded to 5 rows |

---

## 🏗️ Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | SvelteKit + TailwindCSS, Syne / DM Sans fonts |
| **Backend** | FastAPI (Python 3.11), APScheduler |
| **Database** | Supabase (PostgreSQL) + Row Level Security |
| **Auth** | Supabase JWT — auto-refresh on 401 / expiry |
| **AI** | OpenAI, Anthropic, Google AI, Groq, HuggingFace (11 models) |
| **Platforms** | Telegram Bot API, LinkedIn UGC API, VK API |
| **Infrastructure** | Ubuntu VPS, Nginx reverse-proxy, systemd |

---

## 🚀 Deploy (VPS)

> All commands run **on the server** (`ssh root@<server-ip>`), not on your local machine.

```bash
cd /root/publisher_app

# 1. Pull latest
git pull origin main

# 2. Rebuild frontend
cd frontend~ && npm run build && systemctl restart publisher-frontend && cd ..

# 3. Restart backend (if backend changed)
systemctl restart publisher-api

# 4. Health check
curl -s http://localhost:8000/health
```

### First-time setup

```bash
# Backend venv
python3 -m venv backend/venv
backend/venv/bin/pip install -r backend/requirements.txt

# Frontend
cd frontend~
npm install
npm run build
```

### Diagnostics

```bash
systemctl status publisher-api --no-pager -l | head -20
journalctl -u publisher-api -n 50 --no-pager
df -h   # check disk — full disk silently kills uvicorn
```

---

## 🔌 API Reference

### Posts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/posts/` | List posts (`?status=scheduled&platform=telegram`) |
| `POST` | `/api/posts/` | Create post (`content`, `platform`, `status`, `scheduled_at`, `account_id`) |
| `PATCH` | `/api/posts/{id}` | Update post |
| `DELETE` | `/api/posts/{id}` | Delete post |

### AI Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ai/models` | List available LLM models (11 total) |
| `POST` | `/api/ai/generate-post` | Generate post (`topic`, `platform`, `tone`, `language`, `model`) |
| `POST` | `/api/ai/content-plan` | Generate content plan (`days` 1–30) |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/analytics/` | All analytics rows |
| `GET` | `/api/analytics/summary` | Totals + per-platform breakdown |
| `POST` | `/api/analytics/refresh` | Trigger background metrics refresh |

### Accounts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/accounts/telegram` | Connect Telegram channel |
| `POST` | `/api/accounts/linkedin` | Connect LinkedIn profile |
| `POST` | `/api/accounts/vk` | Connect VK group |

---

## 🗄️ Database Migrations

Run once in **Supabase SQL Editor**:

```bash
# Analytics table + platform_post_id column
scripts/analytics_migration.sql
```

---

## 🛣️ Roadmap

### v2.3 ✅ Released — March 2026
- [x] Real analytics from Telegram + LinkedIn
- [x] AI generation → direct publish / schedule / draft
- [x] Content plan save as scheduled posts
- [x] EN / RU full UI localization
- [x] Brand identity (favicon, logo, fonts)
- [x] Educational tone of voice
- [x] JWT expiry handling with auto-redirect

### v2.4 (Q2 2026)
- [ ] Instagram integration via Graph API
- [ ] VK publishing support
- [ ] Advanced analytics charts
- [ ] Team collaboration (multi-user)

### v2.5 (Q3 2026)
- [ ] AI image generation (DALL-E, Midjourney)
- [ ] Content A/B testing
- [ ] Webhook integrations
- [ ] Mobile app (React Native)

---

## 🏢 VYUD AI Ecosystem

| Product | Link |
|---------|------|
| VYUD AI | [vyud.online](https://vyud.online) — documents → interactive courses |
| VYUD Bot | [t.me/VyudAiBot](https://t.me/VyudAiBot) — Telegram AI assistant |
| VYUD CRM | [crm.vyud.online](https://crm.vyud.online) — AI-powered CRM |

**Issues / feedback:** [GitHub Issues](https://github.com/Retyreg/VYUD-AI-Scheduler/issues) · support@vyud.tech

---

Built with ❤️ by [VYUD AI](https://vyud.tech)
