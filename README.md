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
| `GET` | `/api/posts/` | List scheduled posts |
| `POST` | `/api/posts/` | Create new post |
| `PATCH` | `/api/posts/{id}` | Update post |
| `DELETE` | `/api/posts/{id}` | Delete post |

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
