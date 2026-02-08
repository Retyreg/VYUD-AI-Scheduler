<script>
  import { onMount } from 'svelte';
  
  let accounts = [];
  let loading = true;
  
  // Telegram form
  let tgBotToken = '';
  let tgChannelId = '';
  let tgConnecting = false;
  
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
          <button 
            on:click={() => disconnectAccount('telegram')}
            class="text-red-400 hover:text-red-300 text-sm"
          >
            Отключить
          </button>
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
          <button 
            on:click={() => disconnectAccount('linkedin')}
            class="text-red-400 hover:text-red-300 text-sm"
          >
            Отключить
          </button>
        {:else}
          <button 
            on:click={connectLinkedIn}
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
          >
            Подключить
          </button>
        {/if}
      </div>
      
      <!-- Instagram -->
      <div class="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg opacity-50">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
            <span class="text-white text-lg">📷</span>
          </div>
          <div>
            <p class="font-medium text-white">Instagram</p>
            <p class="text-sm text-gray-400">Не подключён</p>
          </div>
        </div>
        <span class="text-gray-500 text-sm">Март 2026</span>
      </div>
    {/if}
  </div>
  
  <!-- Подключить Telegram -->
  {#if !isConnected('telegram')}
  <div class="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
    <h2 class="text-lg font-semibold text-purple-300 mb-4">Подключить Telegram</h2>
    
    <div class="space-y-4">
      <div>
        <label class="block text-sm text-gray-400 mb-1">Bot Token</label>
        <input 
          type="text" 
          bind:value={tgBotToken}
          placeholder="123456:ABC-DEF..."
          class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none"
        />
        <p class="text-xs text-gray-500 mt-1">Получите у @BotFather</p>
      </div>
      
      <div>
        <label class="block text-sm text-gray-400 mb-1">Channel ID</label>
        <input 
          type="text" 
          bind:value={tgChannelId}
          placeholder="@channel или -100123456789"
          class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none"
        />
        <p class="text-xs text-gray-500 mt-1">Бот должен быть админом канала</p>
      </div>
      
      <button 
        on:click={connectTelegram}
        disabled={tgConnecting}
        class="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white py-3 rounded-lg font-medium transition"
      >
        {tgConnecting ? 'Подключение...' : 'Подключить Telegram'}
      </button>
    </div>
  </div>
  {/if}
</div>
