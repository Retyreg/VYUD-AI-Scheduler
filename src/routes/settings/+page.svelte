<script lang="ts">
  import { onMount } from 'svelte';
  
  let accounts: any[] = [];
  let loading = true;
  let telegramToken = '';
  let telegramChannelId = '';
  let saving = false;
  
  const API_URL = 'http://38.180.243.126:8000';
  
  onMount(async () => {
    await loadAccounts();
  });
  
  async function loadAccounts() {
    try {
      const res = await fetch(`${API_URL}/api/accounts/`);
      if (res.ok) {
        accounts = await res.json();
      }
    } catch (e) {
      console.error('Error loading accounts:', e);
    } finally {
      loading = false;
    }
  }
  
  async function connectTelegram() {
    if (!telegramToken.trim()) return;
    
    saving = true;
    try {
      const res = await fetch(`${API_URL}/api/accounts/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform: 'telegram',
          token: telegramToken,
          channel_id: telegramChannelId || null,
          channel_name: 'Telegram Channel'
        })
      });
      
      if (res.ok) {
        telegramToken = '';
        telegramChannelId = '';
        await loadAccounts();
      }
    } catch (e) {
      console.error('Error:', e);
    } finally {
      saving = false;
    }
  }
  
  async function disconnectAccount(id: string) {
    try {
      await fetch(`${API_URL}/api/accounts/${id}`, { method: 'DELETE' });
      await loadAccounts();
    } catch (e) {
      console.error('Error:', e);
    }
  }
  
  function isConnected(platform: string): boolean {
    return accounts.some(a => a.platform === platform && a.is_active);
  }
</script>

<div class="min-h-screen bg-gray-900">
  <!-- Header -->
  <header class="border-b border-gray-800 px-6 py-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">
        VYUD Publisher
      </h1>
      <nav class="flex gap-4">
        <a href="/" class="text-gray-400 hover:text-white px-4 py-2">Календарь</a>
        <a href="/create" class="text-gray-400 hover:text-white px-4 py-2">Создать пост</a>
        <a href="/settings" class="text-white px-4 py-2 rounded-lg bg-gray-800">Настройки</a>
      </nav>
    </div>
  </header>

  <main class="p-6 max-w-2xl mx-auto">
    <h2 class="text-2xl font-bold mb-6">Настройки</h2>
    
    <!-- Подключённые аккаунты -->
    <div class="bg-gray-800 rounded-xl p-6 mb-6">
      <h3 class="text-lg font-semibold mb-4">Подключённые аккаунты</h3>
      
      {#if loading}
        <p class="text-gray-500">Загрузка...</p>
      {:else}
        <div class="space-y-4">
          <!-- Telegram -->
          <div class="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center">
                ✈️
              </div>
              <div>
                <div class="font-medium">Telegram</div>
                <div class="text-sm text-gray-400">
                  {isConnected('telegram') ? 'Подключён' : 'Не подключён'}
                </div>
              </div>
            </div>
            {#if isConnected('telegram')}
              {@const acc = accounts.find(a => a.platform === 'telegram')}
              <button 
                on:click={() => disconnectAccount(acc.id)}
                class="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30"
              >
                Отключить
              </button>
            {:else}
              <span class="text-sm text-gray-500">Настройте ниже</span>
            {/if}
          </div>
          
          <!-- LinkedIn -->
          <div class="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-blue-700 flex items-center justify-center">
                in
              </div>
              <div>
                <div class="font-medium">LinkedIn</div>
                <div class="text-sm text-gray-400">
                  {isConnected('linkedin') ? 'Подключён' : 'Не подключён'}
                </div>
              </div>
            </div>
            <span class="text-sm text-yellow-500">Скоро</span>
          </div>
          
          <!-- Instagram -->
          <div class="flex items-center justify-between p-4 bg-gray-700 rounded-lg opacity-50">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                📷
              </div>
              <div>
                <div class="font-medium">Instagram</div>
                <div class="text-sm text-gray-400">Не подключён</div>
              </div>
            </div>
            <span class="text-sm text-gray-500">Март 2026</span>
          </div>
        </div>
      {/if}
    </div>
    
    <!-- Настройка Telegram -->
    {#if !isConnected('telegram')}
      <div class="bg-gray-800 rounded-xl p-6">
        <h3 class="text-lg font-semibold mb-4">Подключить Telegram</h3>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-400 mb-2">Bot Token</label>
            <input
              type="password"
              bind:value={telegramToken}
              placeholder="123456:ABC-DEF..."
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white"
            />
            <p class="text-xs text-gray-500 mt-1">Получите у @BotFather</p>
          </div>
          
          <div>
            <label class="block text-sm text-gray-400 mb-2">Channel ID (опционально)</label>
            <input
              type="text"
              bind:value={telegramChannelId}
              placeholder="@channel или -100123456789"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white"
            />
          </div>
          
          <button
            on:click={connectTelegram}
            disabled={saving || !telegramToken.trim()}
            class="w-full py-3 rounded-lg font-semibold transition-all
              {saving || !telegramToken.trim()
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-indigo-500 text-white hover:bg-indigo-600'}"
          >
            {saving ? 'Подключение...' : 'Подключить Telegram'}
          </button>
        </div>
      </div>
    {/if}
  </main>
</div>
