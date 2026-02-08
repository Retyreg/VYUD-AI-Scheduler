<script>
  import { onMount } from 'svelte';
  
  let content = '';
  let platform = 'telegram';
  let scheduledDate = '';
  let scheduledTime = '12:00';
  let saving = false;
  let error = '';
  let success = false;
  
  const API_URL = 'https://publisher.vyud.tech/api';
  
  const limits = { telegram: 4096, linkedin: 3000 };
  
  $: charCount = content.length;
  $: charLimit = limits[platform];
  $: isOverLimit = charCount > charLimit;
  
  onMount(() => {
    // Загружаем черновик из AI генератора
    const draft = localStorage.getItem('draft_content');
    const draftPlatform = localStorage.getItem('draft_platform');
    if (draft) {
      content = draft;
      localStorage.removeItem('draft_content');
    }
    if (draftPlatform) {
      platform = draftPlatform;
      localStorage.removeItem('draft_platform');
    }
  });
  
  async function handleSubmit() {
    if (!content.trim() || !scheduledDate || isOverLimit) {
      error = 'Заполните все поля';
      return;
    }
    
    saving = true;
    error = '';
    
    try {
      const scheduledAt = new Date(`${scheduledDate}T${scheduledTime}`).toISOString();
      
      const res = await fetch(`${API_URL}/posts/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, platform, scheduled_at: scheduledAt })
      });
      
      if (res.ok) {
        success = true;
        setTimeout(() => { window.location.href = '/'; }, 1500);
      } else {
        const data = await res.json();
        error = data.detail || 'Ошибка сохранения';
      }
    } catch (e) {
      error = 'Ошибка соединения с сервером';
    } finally {
      saving = false;
    }
  }
</script>

<div class="max-w-4xl mx-auto">
  <h1 class="text-2xl font-bold text-purple-400 mb-6">Создать пост</h1>
  
  {#if success}
    <div class="bg-green-500/20 border border-green-500 rounded-lg p-4 mb-6">
      ✅ Пост успешно запланирован!
    </div>
  {/if}
  
  {#if error}
    <div class="bg-red-500/20 border border-red-500 rounded-lg p-4 mb-6">
      ❌ {error}
    </div>
  {/if}
  
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
      <div class="mb-4">
        <label class="block text-sm text-gray-400 mb-1">Платформа</label>
        <div class="flex gap-2">
          <button class="flex-1 py-2 rounded-lg transition {platform === 'telegram' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300'}" on:click={() => platform = 'telegram'}>Telegram</button>
          <button class="flex-1 py-2 rounded-lg transition {platform === 'linkedin' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300'}" on:click={() => platform = 'linkedin'}>LinkedIn</button>
        </div>
      </div>
      
      <div class="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label class="block text-sm text-gray-400 mb-1">Дата</label>
          <input type="date" bind:value={scheduledDate} class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-purple-500 focus:outline-none" />
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-1">Время</label>
          <input type="time" bind:value={scheduledTime} class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-purple-500 focus:outline-none" />
        </div>
      </div>
      
      <div class="mb-4">
        <div class="flex justify-between mb-1">
          <label class="text-sm text-gray-400">Текст поста</label>
          <span class="text-sm {isOverLimit ? 'text-red-400' : 'text-gray-400'}">{charCount} / {charLimit}</span>
        </div>
        <textarea 
          bind:value={content}
          placeholder="Напишите текст поста..."
          rows="8"
          class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none resize-none"
        ></textarea>
      </div>
      
      <button 
        on:click={handleSubmit}
        disabled={saving || !content.trim() || !scheduledDate || isOverLimit}
        class="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white py-3 rounded-lg font-medium transition"
      >
        {saving ? 'Сохранение...' : 'Запланировать пост'}
      </button>
    </div>
    
    <!-- Превью -->
    <div class="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
      <h2 class="text-lg font-semibold text-purple-300 mb-4">Превью</h2>
      
      {#if platform === 'telegram'}
        <div class="bg-gray-900 rounded-lg p-4">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold">V</div>
            <div>
              <p class="font-medium text-white">VYUD AI</p>
              <p class="text-xs text-gray-400">канал</p>
            </div>
          </div>
          <p class="text-gray-200 whitespace-pre-wrap">{content || 'Текст вашего поста появится здесь...'}</p>
          <p class="text-xs text-gray-500 mt-2">{scheduledTime || '12:00'}</p>
        </div>
      {:else}
        <div class="bg-white rounded-lg p-4 text-gray-900">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">V</div>
            <div>
              <p class="font-semibold">VYUD AI</p>
              <p class="text-xs text-gray-500">Company • Technology</p>
            </div>
          </div>
          <p class="whitespace-pre-wrap">{content || 'Текст вашего поста появится здесь...'}</p>
        </div>
      {/if}
      
      <div class="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
        <p class="text-yellow-400 text-sm font-medium">💡 Советы</p>
        <ul class="text-gray-400 text-sm mt-1 space-y-1">
          <li>• Используйте эмодзи для привлечения внимания</li>
          <li>• Неформальный тон работает лучше</li>
          <li>• Добавьте призыв к действию</li>
        </ul>
      </div>
    </div>
  </div>
</div>
