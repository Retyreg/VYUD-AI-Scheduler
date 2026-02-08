<script lang="ts">
  let content = '';
  let platform: 'telegram' | 'linkedin' = 'telegram';
  let scheduledDate = '';
  let scheduledTime = '12:00';
  let saving = false;
  let error = '';
  let success = false;
  
  const API_URL = 'http://38.180.243.126:8000';
  
  // Лимиты символов
  const limits = {
    telegram: 4096,
    linkedin: 3000
  };
  
  $: charCount = content.length;
  $: charLimit = limits[platform];
  $: isOverLimit = charCount > charLimit;
  
  async function handleSubmit() {
    if (!content.trim() || !scheduledDate || isOverLimit) return;
    
    saving = true;
    error = '';
    
    try {
      const scheduledAt = new Date(`${scheduledDate}T${scheduledTime}`).toISOString();
      
      const res = await fetch(`${API_URL}/api/posts/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          platform,
          scheduled_at: scheduledAt
        })
      });
      
      if (res.ok) {
        success = true;
        setTimeout(() => {
          window.location.href = '/';
        }, 1500);
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

<div class="min-h-screen bg-gray-900">
  <!-- Header -->
  <header class="border-b border-gray-800 px-6 py-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">
        VYUD Publisher
      </h1>
      <nav class="flex gap-4">
        <a href="/" class="text-gray-400 hover:text-white px-4 py-2">Календарь</a>
        <a href="/create" class="text-white px-4 py-2 rounded-lg bg-gray-800">Создать пост</a>
        <a href="/settings" class="text-gray-400 hover:text-white px-4 py-2">Настройки</a>
      </nav>
    </div>
  </header>

  <main class="p-6 max-w-4xl mx-auto">
    <h2 class="text-2xl font-bold mb-6">Создать пост</h2>
    
    {#if success}
      <div class="bg-green-500/20 border border-green-500 rounded-lg p-4 mb-6">
        ✅ Пост успешно запланирован! Перенаправление...
      </div>
    {/if}
    
    {#if error}
      <div class="bg-red-500/20 border border-red-500 rounded-lg p-4 mb-6">
        ❌ {error}
      </div>
    {/if}
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Форма -->
      <div class="bg-gray-800 rounded-xl p-6">
        <!-- Выбор платформы -->
        <div class="mb-6">
          <label class="block text-sm text-gray-400 mb-2">Платформа</label>
          <div class="flex gap-2">
            <button
              class="flex-1 py-3 px-4 rounded-lg transition-colors {platform === 'telegram' ? 'bg-indigo-500 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'}"
              on:click={() => platform = 'telegram'}
            >
              Telegram
            </button>
            <button
              class="flex-1 py-3 px-4 rounded-lg transition-colors {platform === 'linkedin' ? 'bg-indigo-500 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'}"
              on:click={() => platform = 'linkedin'}
            >
              LinkedIn
            </button>
          </div>
        </div>
        
        <!-- Дата и время -->
        <div class="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label class="block text-sm text-gray-400 mb-2">Дата</label>
            <input
              type="date"
              bind:value={scheduledDate}
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-2">Время</label>
            <input
              type="time"
              bind:value={scheduledTime}
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white"
            />
          </div>
        </div>
        
        <!-- Текст поста -->
        <div class="mb-6">
          <div class="flex justify-between items-center mb-2">
            <label class="text-sm text-gray-400">Текст поста</label>
            <span class="text-sm {isOverLimit ? 'text-red-500' : 'text-gray-500'}">
              {charCount} / {charLimit}
            </span>
          </div>
          <textarea
            bind:value={content}
            rows="8"
            placeholder="Напишите текст поста..."
            class="w-full bg-gray-700 border rounded-lg px-4 py-3 text-white resize-none
              {isOverLimit ? 'border-red-500' : 'border-gray-600 focus:border-indigo-500'}"
          ></textarea>
        </div>
        
        <!-- Кнопка -->
        <button
          on:click={handleSubmit}
          disabled={saving || !content.trim() || !scheduledDate || isOverLimit}
          class="w-full py-4 rounded-lg font-semibold transition-all
            {saving || !content.trim() || !scheduledDate || isOverLimit
              ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white hover:opacity-90'}"
        >
          {saving ? 'Сохранение...' : 'Запланировать пост'}
        </button>
      </div>
      
      <!-- Превью -->
      <div class="bg-gray-800 rounded-xl p-6">
        <h3 class="text-lg font-semibold mb-4">Превью</h3>
        
        {#if platform === 'telegram'}
          <!-- Telegram Preview -->
          <div class="bg-[#1c2733] rounded-lg p-4">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-center font-bold">
                V
              </div>
              <div>
                <div class="font-semibold">VYUD AI</div>
                <div class="text-xs text-gray-500">канал</div>
              </div>
            </div>
            <p class="text-sm whitespace-pre-wrap">{content || 'Текст вашего поста появится здесь...'}</p>
            <div class="text-xs text-gray-500 mt-2 text-right">
              {scheduledTime || '12:00'}
            </div>
          </div>
        {:else}
          <!-- LinkedIn Preview -->
          <div class="bg-white text-gray-900 rounded-lg p-4">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-12 h-12 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold">
                V
              </div>
              <div>
                <div class="font-semibold">VYUD AI</div>
                <div class="text-xs text-gray-500">SaaS • EdTech</div>
              </div>
            </div>
            <p class="text-sm whitespace-pre-wrap mb-4">{content || 'Текст вашего поста появится здесь...'}</p>
            <div class="flex gap-4 text-gray-500 text-sm border-t pt-3">
              <span>👍 Нравится</span>
              <span>💬 Комментировать</span>
              <span>🔄 Поделиться</span>
            </div>
          </div>
        {/if}
        
        <!-- Советы -->
        <div class="mt-6 p-4 bg-gray-700/50 rounded-lg">
          <h4 class="text-sm font-semibold text-indigo-400 mb-2">💡 Советы</h4>
          {#if platform === 'telegram'}
            <ul class="text-sm text-gray-400 space-y-1">
              <li>• Используйте эмодзи для привлечения внимания</li>
              <li>• Неформальный тон работает лучше</li>
              <li>• Добавьте призыв к действию</li>
            </ul>
          {:else}
            <ul class="text-sm text-gray-400 space-y-1">
              <li>• Профессиональный тон</li>
              <li>• Используйте хештеги (3-5 штук)</li>
              <li>• Первые 2 строки — самые важные</li>
            </ul>
          {/if}
        </div>
      </div>
    </div>
  </main>
</div>
