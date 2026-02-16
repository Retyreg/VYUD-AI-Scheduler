<script>
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  
  let content = '';
  let platform = 'telegram';
  let scheduledDate = '';
  let scheduledTime = '12:00';
  let loading = false;
  let error = '';
  let accounts = [];
  
  const platforms = [
    { id: 'telegram', name: 'Telegram', color: 'bg-blue-500' },
    { id: 'linkedin', name: 'LinkedIn', color: 'bg-blue-700' },
    { id: 'vk', name: 'VK', color: 'bg-sky-600' }
  ];
  
  function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }
  
  onMount(async () => {
    // Устанавливаем дату по умолчанию - завтра
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    scheduledDate = tomorrow.toISOString().split('T')[0];
    
    // Читаем draft из AI генератора
    const draftContent = localStorage.getItem('draft_content');
    const draftPlatform = localStorage.getItem('draft_platform');
    
    if (draftContent) {
      content = draftContent;
      localStorage.removeItem('draft_content');
    }
    if (draftPlatform) {
      platform = draftPlatform;
      localStorage.removeItem('draft_platform');
    }
    
    // Загружаем аккаунты
    try {
      const res = await fetch('/api/accounts/', { headers: getAuthHeaders() });
      if (res.ok) {
        accounts = await res.json();
      }
    } catch (e) {
      console.error('Failed to load accounts', e);
    }
  });
  
  async function createPost() {
    if (!content.trim()) {
      error = 'Введите текст поста';
      return;
    }
    if (!scheduledDate || !scheduledTime) {
      error = 'Укажите дату и время публикации';
      return;
    }
    
    loading = true;
    error = '';
    
    try {
      const scheduledAt = new Date(`${scheduledDate}T${scheduledTime}:00`).toISOString();
      const account = accounts.find(a => a.platform === platform && a.is_active);
      
      const res = await fetch('/api/posts/', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          content,
          platform,
          scheduled_at: scheduledAt,
          channel_id: account?.channel_id || null
        })
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Ошибка создания поста');
      }
      
      goto('/');
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }
  
  $: connectedPlatforms = accounts.filter(a => a.is_active).map(a => a.platform);
  $: isPlatformConnected = connectedPlatforms.includes(platform);
</script>

<svelte:head>
  <title>Создать пост — VYUD Publisher</title>
</svelte:head>

<div class="max-w-4xl mx-auto">
  <h1 class="text-2xl font-bold mb-6">Создать пост</h1>
  
  <div class="grid grid-cols-2 gap-6">
    <!-- Editor -->
    <div class="bg-gray-800 rounded-xl p-6">
      <div class="mb-4">
        <label class="block text-sm text-gray-400 mb-2">Платформа</label>
        <div class="flex gap-2">
          {#each platforms as p}
            <button 
              on:click={() => platform = p.id}
              class="px-4 py-2 rounded-lg transition {platform === p.id ? p.color + ' text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}"
            >
              {p.name}
            </button>
          {/each}
        </div>
        {#if !isPlatformConnected && accounts.length > 0}
          <p class="text-yellow-500 text-sm mt-2">⚠️ {platform} не подключён. <a href="/settings" class="underline">Подключить</a></p>
        {/if}
      </div>
      
      <div class="mb-4">
        <label class="block text-sm text-gray-400 mb-2">Текст поста</label>
        <textarea 
          bind:value={content}
          class="w-full h-48 bg-gray-700 rounded-lg p-3 border border-gray-600 focus:border-purple-500 focus:outline-none resize-none"
          placeholder="Введите текст поста..."
        ></textarea>
        <div class="text-right text-sm text-gray-500 mt-1">{content.length} символов</div>
      </div>
      
      <div class="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label class="block text-sm text-gray-400 mb-2">Дата</label>
          <input 
            type="date" 
            bind:value={scheduledDate}
            class="w-full bg-gray-700 rounded-lg p-3 border border-gray-600 focus:border-purple-500 focus:outline-none"
          />
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-2">Время</label>
          <input 
            type="time" 
            bind:value={scheduledTime}
            class="w-full bg-gray-700 rounded-lg p-3 border border-gray-600 focus:border-purple-500 focus:outline-none"
          />
        </div>
      </div>
      
      {#if error}
        <div class="bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded-lg mb-4">{error}</div>
      {/if}
      
      <button 
        on:click={createPost}
        disabled={loading}
        class="w-full py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium transition disabled:opacity-50"
      >
        {loading ? 'Создание...' : 'Запланировать пост'}
      </button>
    </div>
    
    <!-- Preview -->
    <div class="bg-gray-800 rounded-xl p-6">
      <h3 class="text-sm text-gray-400 mb-4">Предпросмотр</h3>
      <div class="bg-gray-700 rounded-lg p-4">
        <div class="flex items-center gap-2 mb-3">
          <div class="w-10 h-10 {platforms.find(p => p.id === platform)?.color} rounded-full flex items-center justify-center font-bold">
            {platform === 'telegram' ? '✈' : platform === 'linkedin' ? 'in' : 'VK'}
          </div>
          <div>
            <div class="font-medium">VYUD AI</div>
            <div class="text-xs text-gray-400">{scheduledDate} {scheduledTime}</div>
          </div>
        </div>
        <p class="whitespace-pre-wrap text-gray-200">{content || 'Текст поста появится здесь...'}</p>
      </div>
    </div>
  </div>
</div>
