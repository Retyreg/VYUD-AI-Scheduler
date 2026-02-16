<script>
  import { onMount } from 'svelte';
  
  let accounts = [];
  let loading = true;
  let error = '';
  
  let telegramToken = '';
  let telegramChannelId = '';
  let telegramChannelName = '';
  
  let linkedinToken = '';
  let linkedinOrgId = '';
  let linkedinOrgName = '';
  
  let vkToken = '';
  let vkGroupId = '';
  let vkGroupName = '';
  
  let saving = { telegram: false, linkedin: false, vk: false };
  
  function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }
  
  onMount(async () => {
    await loadAccounts();
  });
  
  async function loadAccounts() {
    loading = true;
    try {
      const res = await fetch('/api/accounts/', { headers: getAuthHeaders() });
      if (res.ok) {
        accounts = await res.json();
        console.log('Loaded accounts:', accounts);
      }
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }
  
  async function connectPlatform(platform) {
    let token, channelId, channelName;
    
    if (platform === 'telegram') {
      token = telegramToken;
      channelId = telegramChannelId;
      channelName = telegramChannelName || 'Telegram Channel';
    } else if (platform === 'linkedin') {
      token = linkedinToken;
      channelId = linkedinOrgId;
      channelName = linkedinOrgName || 'LinkedIn Org';
    } else if (platform === 'vk') {
      token = vkToken;
      channelId = vkGroupId;
      channelName = vkGroupName || 'VK Group';
    }
    
    if (!token) {
      error = 'Введите токен';
      return;
    }
    
    saving[platform] = true;
    error = '';
    
    try {
      const res = await fetch('/api/accounts/', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ platform, token, channel_id: channelId, channel_name: channelName })
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Ошибка подключения');
      }
      
      await loadAccounts();
      
      if (platform === 'telegram') { telegramToken = ''; telegramChannelId = ''; telegramChannelName = ''; }
      else if (platform === 'linkedin') { linkedinToken = ''; linkedinOrgId = ''; linkedinOrgName = ''; }
      else if (platform === 'vk') { vkToken = ''; vkGroupId = ''; vkGroupName = ''; }
    } catch (e) {
      error = e.message;
    } finally {
      saving[platform] = false;
    }
  }
  
  // Reactive getters
  $: telegramAccount = accounts.find(a => a.platform === 'telegram' && a.is_active);
  $: linkedinAccount = accounts.find(a => a.platform === 'linkedin' && a.is_active);
  $: vkAccount = accounts.find(a => a.platform === 'vk' && a.is_active);
</script>

<svelte:head>
  <title>Настройки — VYUD Publisher</title>
</svelte:head>

<div class="max-w-4xl mx-auto">
  <h1 class="text-2xl font-bold mb-6">Настройки</h1>
  
  {#if error}
    <div class="bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded-lg mb-6">{error}</div>
  {/if}
  
  {#if loading}
    <div class="text-gray-400">Загрузка...</div>
  {:else}
    <div class="space-y-6">
      <!-- Telegram -->
      <div class="bg-gray-800 rounded-xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center text-xl">✈</div>
          <div>
            <h3 class="font-semibold">Telegram</h3>
            {#if telegramAccount}
              <span class="text-green-400 text-sm">✓ Подключён: {telegramAccount.channel_name}</span>
            {:else}
              <span class="text-gray-400 text-sm">Не подключён</span>
            {/if}
          </div>
        </div>
        
        {#if !telegramAccount}
          <div class="space-y-3">
            <input type="text" bind:value={telegramToken} placeholder="Bot Token (от @BotFather)" class="w-full bg-gray-700 rounded-lg p-3 border border-gray-600 focus:border-purple-500 focus:outline-none" />
            <input type="text" bind:value={telegramChannelId} placeholder="Channel ID (например: -1001234567890)" class="w-full bg-gray-700 rounded-lg p-3 border border-gray-600 focus:border-purple-500 focus:outline-none" />
            <input type="text" bind:value={telegramChannelName} placeholder="Название канала" class="w-full bg-gray-700 rounded-lg p-3 border border-gray-600 focus:border-purple-500 focus:outline-none" />
            <button on:click={() => connectPlatform('telegram')} disabled={saving.telegram} class="px-6 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg transition disabled:opacity-50">
              {saving.telegram ? 'Подключение...' : 'Подключить'}
            </button>
          </div>
        {/if}
      </div>
      
      <!-- LinkedIn -->
      <div class="bg-gray-800 rounded-xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-blue-700 rounded-lg flex items-center justify-center font-bold">in</div>
          <div>
            <h3 class="font-semibold">LinkedIn</h3>
            {#if linkedinAccount}
              <span class="text-green-400 text-sm">✓ Подключён: {linkedinAccount.channel_name}</span>
            {:else}
              <span class="text-gray-400 text-sm">Не подключён</span>
            {/if}
          </div>
        </div>
        
        {#if !linkedinAccount}
          <div class="space-y-3">
            <input type="text" bind:value={linkedinToken} placeholder="Access Token" class="w-full bg-gray-700 rounded-lg p-3 border border-gray-600 focus:border-purple-500 focus:outline-none" />
            <input type="text" bind:value={linkedinOrgId} placeholder="Organization ID" class="w-full bg-gray-700 rounded-lg p-3 border border-gray-600 focus:border-purple-500 focus:outline-none" />
            <input type="text" bind:value={linkedinOrgName} placeholder="Название организации" class="w-full bg-gray-700 rounded-lg p-3 border border-gray-600 focus:border-purple-500 focus:outline-none" />
            <button on:click={() => connectPlatform('linkedin')} disabled={saving.linkedin} class="px-6 py-2 bg-blue-700 hover:bg-blue-800 rounded-lg transition disabled:opacity-50">
              {saving.linkedin ? 'Подключение...' : 'Подключить'}
            </button>
          </div>
        {/if}
      </div>
      
      <!-- VK -->
      <div class="bg-gray-800 rounded-xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-sky-600 rounded-lg flex items-center justify-center font-bold text-sm">VK</div>
          <div>
            <h3 class="font-semibold">ВКонтакте</h3>
            {#if vkAccount}
              <span class="text-green-400 text-sm">✓ Подключён: {vkAccount.channel_name}</span>
            {:else}
              <span class="text-gray-400 text-sm">Не подключён</span>
            {/if}
          </div>
        </div>
        
        {#if !vkAccount}
          <div class="space-y-3">
            <input type="text" bind:value={vkToken} placeholder="Access Token сообщества" class="w-full bg-gray-700 rounded-lg p-3 border border-gray-600 focus:border-purple-500 focus:outline-none" />
            <input type="text" bind:value={vkGroupId} placeholder="ID группы (например: -123456789)" class="w-full bg-gray-700 rounded-lg p-3 border border-gray-600 focus:border-purple-500 focus:outline-none" />
            <input type="text" bind:value={vkGroupName} placeholder="Название группы" class="w-full bg-gray-700 rounded-lg p-3 border border-gray-600 focus:border-purple-500 focus:outline-none" />
            <button on:click={() => connectPlatform('vk')} disabled={saving.vk} class="px-6 py-2 bg-sky-600 hover:bg-sky-700 rounded-lg transition disabled:opacity-50">
              {saving.vk ? 'Подключение...' : 'Подключить'}
            </button>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>
