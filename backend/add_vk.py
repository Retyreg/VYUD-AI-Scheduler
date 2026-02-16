#!/usr/bin/env python3
"""
VYUD Publisher — добавление VK интеграции.
Запустить на сервере: python3 add_vk.py
"""
import os

BASE = "/root/publisher_app/backend"
FRONT = "/root/publisher_app/frontend~/src/routes"

# ============================================================
# 1. services/vk.py — НОВЫЙ ФАЙЛ
# ============================================================
vk_service = '''import httpx
import os

class VKService:
    def __init__(self):
        self.api_url = "https://api.vk.com/method"
        self.api_version = "5.131"

    async def post_to_wall(self, token: str, owner_id: str, text: str) -> dict:
        """
        Публикует пост на стену сообщества VK.
        owner_id: отрицательный ID сообщества (например -123456789)
        token: токен сообщества с правом wall
        """
        params = {
            "owner_id": owner_id,
            "from_group": 1,
            "message": text,
            "access_token": token,
            "v": self.api_version
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/wall.post",
                data=params
            )
            data = response.json()

            if "response" in data:
                return {"ok": True, "post_id": data["response"].get("post_id")}
            else:
                error = data.get("error", {})
                return {
                    "ok": False,
                    "error": error.get("error_msg", "Unknown VK error"),
                    "error_code": error.get("error_code")
                }

    async def get_group_info(self, token: str, group_id: str) -> dict:
        """Получает информацию о сообществе для проверки подключения."""
        params = {
            "group_id": group_id.lstrip("-"),
            "access_token": token,
            "v": self.api_version
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/groups.getById",
                params=params
            )
            data = response.json()

            if "response" in data:
                groups = data["response"].get("groups", data["response"])
                if isinstance(groups, list) and groups:
                    group = groups[0]
                    return {"ok": True, "name": group.get("name"), "id": group.get("id")}
                return {"ok": True, "name": "VK Group", "id": group_id}
            else:
                error = data.get("error", {})
                return {"ok": False, "error": error.get("error_msg", "Unknown error")}
'''

# ============================================================
# 2. models.py — добавить vk в Platform enum
# ============================================================
models_content = '''from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class Platform(str, Enum):
    telegram = "telegram"
    linkedin = "linkedin"
    vk = "vk"

class PostStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"

class PostCreate(BaseModel):
    content: str
    platform: Platform
    scheduled_at: datetime
    channel_id: Optional[str] = None

class PostUpdate(BaseModel):
    content: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[PostStatus] = None

class PostResponse(BaseModel):
    id: str
    content: str
    platform: Platform
    status: PostStatus
    scheduled_at: datetime
    published_at: Optional[datetime] = None
    created_at: datetime
    utm_tag: Optional[str] = None

class AccountCreate(BaseModel):
    platform: Platform
    token: str
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None

class AccountResponse(BaseModel):
    id: str
    platform: Platform
    channel_name: Optional[str]
    is_active: bool
    connected_at: datetime
'''

# ============================================================
# 3. services/scheduler.py — добавить VK публикацию
# ============================================================
scheduler_content = '''from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
import requests

from services.telegram import TelegramService
from services.linkedin import LinkedInService
from services.vk import VKService

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_headers(prefer="return=representation"):
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": prefer
    }

def sb_get(table, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    resp = requests.get(url, headers=get_headers())
    resp.raise_for_status()
    return resp.json()

def sb_update(table, record_id, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{record_id}"
    resp = requests.patch(url, json=data, headers=get_headers())
    resp.raise_for_status()
    return resp.json()

telegram = TelegramService(os.getenv("TELEGRAM_BOT_TOKEN", ""))
linkedin = LinkedInService()
vk = VKService()

async def check_and_publish_posts():
    try:
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        posts = sb_get("posts", f"status=eq.scheduled&scheduled_at=lte.{ts}&order=scheduled_at.asc")
        for post in posts:
            try:
                if post["platform"] == "telegram":
                    await publish_telegram(post)
                elif post["platform"] == "linkedin":
                    await publish_linkedin(post)
                elif post["platform"] == "vk":
                    await publish_vk(post)
            except Exception as e:
                print(f"Error publishing {post['id']}: {e}")
                sb_update("posts", post["id"], {"status": "failed"})
    except Exception as e:
        print(f"Scheduler error: {e}")

async def publish_telegram(post):
    accounts = sb_get("publisher_accounts", "platform=eq.telegram&is_active=eq.true")
    if not accounts:
        raise Exception("Telegram not connected")
    channel_id = accounts[0].get("channel_id") or "@vyud_ai"
    content = post["content"]
    if post.get("utm_tag"):
        content += "\\n\\nvyud.online" + post["utm_tag"]
    result = await telegram.send_message(channel_id, content)
    if result.get("ok"):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        sb_update("posts", post["id"], {"status": "published", "published_at": ts})
        print(f"Published {post['id']} to Telegram")
    else:
        raise Exception(result.get("description", "Unknown error"))

async def publish_linkedin(post):
    content = post["content"]
    if post.get("utm_tag"):
        content += "\\n\\nvyud.tech" + post["utm_tag"]
    result = await linkedin.post_to_profile(content)
    if result.get("ok"):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        sb_update("posts", post["id"], {"status": "published", "published_at": ts})
        print(f"Published {post['id']} to LinkedIn")
    else:
        raise Exception(result.get("error", "Unknown error"))

async def publish_vk(post):
    accounts = sb_get("publisher_accounts", "platform=eq.vk&is_active=eq.true")
    if not accounts:
        raise Exception("VK not connected")
    account = accounts[0]
    token = account.get("token", "")
    owner_id = account.get("channel_id", "")
    content = post["content"]
    if post.get("utm_tag"):
        content += "\\n\\nvyud.tech" + post["utm_tag"]
    result = await vk.post_to_wall(token, owner_id, content)
    if result.get("ok"):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        sb_update("posts", post["id"], {"status": "published", "published_at": ts})
        print(f"Published {post['id']} to VK (post_id: {result.get('post_id')})")
    else:
        raise Exception(result.get("error", "Unknown VK error"))

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_and_publish_posts, IntervalTrigger(seconds=30), id="post_publisher", replace_existing=True)
    scheduler.start()
    print("Scheduler started")
    return scheduler
'''

# ============================================================
# 4. settings/+page.svelte — добавить VK в UI
# ============================================================
settings_page = '''<script>
  import { onMount } from 'svelte';

  let accounts = [];
  let loading = true;

  // Telegram form
  let tgBotToken = '';
  let tgChannelId = '';
  let tgConnecting = false;

  // VK form
  let vkToken = '';
  let vkGroupId = '';
  let vkConnecting = false;

  const API_URL = 'https://publisher.vyud.tech/api';

  onMount(async () => {
    await loadAccounts();
  });

  async function loadAccounts() {
    try {
      const res = await fetch(`${API_URL}/accounts/`);
      accounts = await res.json();
    } catch (e) {
      console.error('Failed to load accounts:', e);
    } finally {
      loading = false;
    }
  }

  function isConnected(platform) {
    return accounts.some(a => a.platform === platform && a.is_active);
  }

  function getAccount(platform) {
    return accounts.find(a => a.platform === platform);
  }

  async function connectTelegram() {
    if (!tgBotToken || !tgChannelId) {
      alert('Заполните Bot Token и Channel ID');
      return;
    }

    tgConnecting = true;
    try {
      const res = await fetch(`${API_URL}/accounts/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform: 'telegram',
          token: tgBotToken,
          channel_id: tgChannelId,
          channel_name: 'Telegram Channel'
        })
      });

      if (res.ok) {
        tgBotToken = '';
        tgChannelId = '';
        await loadAccounts();
        alert('Telegram подключён!');
      } else {
        const err = await res.json();
        alert('Ошибка: ' + (err.detail || 'Unknown error'));
      }
    } catch (e) {
      alert('Ошибка подключения');
    } finally {
      tgConnecting = false;
    }
  }

  async function connectVK() {
    if (!vkToken || !vkGroupId) {
      alert('Заполните токен сообщества и ID группы');
      return;
    }

    vkConnecting = true;
    try {
      // ID группы должен быть отрицательным для wall.post
      let groupId = vkGroupId.trim();
      if (!groupId.startsWith('-')) {
        groupId = '-' + groupId;
      }

      const res = await fetch(`${API_URL}/accounts/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform: 'vk',
          token: vkToken,
          channel_id: groupId,
          channel_name: 'VK Community'
        })
      });

      if (res.ok) {
        vkToken = '';
        vkGroupId = '';
        await loadAccounts();
        alert('VK подключён!');
      } else {
        const err = await res.json();
        alert('Ошибка: ' + (err.detail || 'Unknown error'));
      }
    } catch (e) {
      alert('Ошибка подключения');
    } finally {
      vkConnecting = false;
    }
  }

  async function disconnectAccount(platform) {
    const account = getAccount(platform);
    if (!account) return;

    if (!confirm(`Отключить ${platform}?`)) return;

    try {
      await fetch(`${API_URL}/accounts/${account.id}`, { method: 'DELETE' });
      await loadAccounts();
    } catch (e) {
      alert('Ошибка отключения');
    }
  }

  function connectLinkedIn() {
    const clientId = '781f302zs0hfbz';
    const redirectUri = encodeURIComponent('https://publisher.vyud.tech/api/linkedin/callback');
    const scope = encodeURIComponent('w_member_social openid profile');
    const url = `https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`;
    window.open(url, '_blank', 'width=600,height=700');
  }
</script>

<div class="max-w-2xl mx-auto">
  <h1 class="text-2xl font-bold text-purple-400 mb-8">Настройки</h1>

  <!-- Подключённые аккаунты -->
  <div class="bg-gray-800/50 rounded-xl p-6 mb-6 border border-gray-700">
    <h2 class="text-lg font-semibold text-purple-300 mb-4">Подключённые аккаунты</h2>

    {#if loading}
      <p class="text-gray-400">Загрузка...</p>
    {:else}
      <!-- Telegram -->
      <div class="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg mb-3">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.18 1.897-.962 6.502-1.359 8.627-.168.9-.5 1.201-.82 1.23-.697.064-1.226-.461-1.901-.903-1.056-.692-1.653-1.123-2.678-1.799-1.185-.781-.417-1.21.258-1.911.177-.184 3.247-2.977 3.307-3.23.007-.032.015-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.139-5.062 3.345-.479.329-.913.489-1.302.481-.428-.009-1.252-.242-1.865-.442-.752-.244-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.831-2.529 6.998-3.015 3.333-1.386 4.025-1.627 4.477-1.635.099-.002.321.023.465.141.121.1.154.234.17.331.015.098.034.322.019.496z"/>
            </svg>
          </div>
          <div>
            <p class="font-medium text-white">Telegram</p>
            {#if isConnected('telegram')}
              <p class="text-sm text-green-400">Подключён • {getAccount('telegram')?.channel_name || getAccount('telegram')?.channel_id}</p>
            {:else}
              <p class="text-sm text-gray-400">Не подключён</p>
            {/if}
          </div>
        </div>
        {#if isConnected('telegram')}
          <button on:click={() => disconnectAccount('telegram')} class="text-red-400 hover:text-red-300 text-sm">Отключить</button>
        {:else}
          <span class="text-gray-500 text-sm">Настройте ниже</span>
        {/if}
      </div>

      <!-- LinkedIn -->
      <div class="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg mb-3">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
            <span class="text-white font-bold text-sm">in</span>
          </div>
          <div>
            <p class="font-medium text-white">LinkedIn</p>
            {#if isConnected('linkedin')}
              <p class="text-sm text-green-400">Подключён</p>
            {:else}
              <p class="text-sm text-gray-400">Не подключён</p>
            {/if}
          </div>
        </div>
        {#if isConnected('linkedin')}
          <button on:click={() => disconnectAccount('linkedin')} class="text-red-400 hover:text-red-300 text-sm">Отключить</button>
        {:else}
          <button on:click={connectLinkedIn} class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm">Подключить</button>
        {/if}
      </div>

      <!-- VK -->
      <div class="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg mb-3">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-sky-500 rounded-full flex items-center justify-center">
            <span class="text-white font-bold text-sm">VK</span>
          </div>
          <div>
            <p class="font-medium text-white">ВКонтакте</p>
            {#if isConnected('vk')}
              <p class="text-sm text-green-400">Подключён • {getAccount('vk')?.channel_name || 'VK Community'}</p>
            {:else}
              <p class="text-sm text-gray-400">Не подключён</p>
            {/if}
          </div>
        </div>
        {#if isConnected('vk')}
          <button on:click={() => disconnectAccount('vk')} class="text-red-400 hover:text-red-300 text-sm">Отключить</button>
        {:else}
          <span class="text-gray-500 text-sm">Настройте ниже</span>
        {/if}
      </div>

      <!-- Instagram (скоро) -->
      <div class="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg opacity-50">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
            <span class="text-white text-lg">📷</span>
          </div>
          <div>
            <p class="font-medium text-white">Instagram</p>
            <p class="text-sm text-gray-400">Скоро</p>
          </div>
        </div>
        <span class="text-gray-500 text-sm">В разработке</span>
      </div>

      <!-- Facebook (скоро) -->
      <div class="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg opacity-50 mt-3">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-700 rounded-full flex items-center justify-center">
            <span class="text-white font-bold text-sm">f</span>
          </div>
          <div>
            <p class="font-medium text-white">Facebook</p>
            <p class="text-sm text-gray-400">Скоро</p>
          </div>
        </div>
        <span class="text-gray-500 text-sm">В разработке</span>
      </div>
    {/if}
  </div>

  <!-- Подключить Telegram -->
  {#if !isConnected('telegram')}
  <div class="bg-gray-800/50 rounded-xl p-6 mb-6 border border-gray-700">
    <h2 class="text-lg font-semibold text-purple-300 mb-4">Подключить Telegram</h2>
    <div class="space-y-4">
      <div>
        <label class="block text-sm text-gray-400 mb-1">Bot Token</label>
        <input type="text" bind:value={tgBotToken} placeholder="123456:ABC-DEF..."
          class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none" />
        <p class="text-xs text-gray-500 mt-1">Получите у @BotFather</p>
      </div>
      <div>
        <label class="block text-sm text-gray-400 mb-1">Channel ID</label>
        <input type="text" bind:value={tgChannelId} placeholder="@channel или -100123456789"
          class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none" />
        <p class="text-xs text-gray-500 mt-1">Бот должен быть админом канала</p>
      </div>
      <button on:click={connectTelegram} disabled={tgConnecting}
        class="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white py-3 rounded-lg font-medium transition">
        {tgConnecting ? 'Подключение...' : 'Подключить Telegram'}
      </button>
    </div>
  </div>
  {/if}

  <!-- Подключить VK -->
  {#if !isConnected('vk')}
  <div class="bg-gray-800/50 rounded-xl p-6 mb-6 border border-gray-700">
    <h2 class="text-lg font-semibold text-purple-300 mb-4">Подключить ВКонтакте</h2>
    <div class="space-y-4">
      <div>
        <label class="block text-sm text-gray-400 mb-1">Токен сообщества</label>
        <input type="text" bind:value={vkToken} placeholder="vk1.a.abc123..."
          class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-sky-500 focus:outline-none" />
        <p class="text-xs text-gray-500 mt-1">Настройки сообщества → Работа с API → Ключи доступа</p>
      </div>
      <div>
        <label class="block text-sm text-gray-400 mb-1">ID сообщества</label>
        <input type="text" bind:value={vkGroupId} placeholder="123456789"
          class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-sky-500 focus:outline-none" />
        <p class="text-xs text-gray-500 mt-1">Числовой ID группы (без минуса)</p>
      </div>
      <button on:click={connectVK} disabled={vkConnecting}
        class="w-full bg-sky-500 hover:bg-sky-600 disabled:bg-gray-600 text-white py-3 rounded-lg font-medium transition">
        {vkConnecting ? 'Подключение...' : 'Подключить ВКонтакте'}
      </button>
    </div>
  </div>
  {/if}
</div>
'''

# ============================================================
# Записываем файлы
# ============================================================
if __name__ == "__main__":
    files = {
        f"{BASE}/services/vk.py": vk_service,
        f"{BASE}/models.py": models_content,
        f"{BASE}/services/scheduler.py": scheduler_content,
        f"{FRONT}/settings/+page.svelte": settings_page,
    }

    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content.strip() + '\n')
        print(f"OK  {path}")

    print(f"\n=== {len(files)} files written ===")
    print()
    print("Next steps:")
    print("  1. systemctl restart publisher-api")
    print("  2. cd /root/publisher_app/frontend~ && npm run build && systemctl restart publisher-frontend")
    print("  3. Test: curl -s http://localhost:8000/api/accounts/ | python3 -m json.tool")
