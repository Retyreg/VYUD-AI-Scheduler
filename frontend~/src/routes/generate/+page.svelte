<script>
  import { onMount } from 'svelte';
  
  let models = [];
  let selectedModel = 'gpt-4o';
  let platform = 'telegram';
  let topic = '';
  let tone = 'professional';
  let generatedContent = '';
  let loading = false;
  let activeTab = 'post';
  let planDays = 7;
  let contentPlan = [];
  
  const API_URL = '/api';
  
  const tones = [
    { value: 'professional', label: 'Профессиональный' },
    { value: 'casual', label: 'Неформальный' },
    { value: 'humorous', label: 'С юмором' },
    { value: 'educational', label: 'Образовательный' },
    { value: 'inspiring', label: 'Вдохновляющий' }
  ];
  
  function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }
  
  onMount(async () => {
    const res = await fetch(`${API_URL}/ai/models`, { headers: getAuthHeaders() });
    models = await res.json();
  });
  
  async function generatePost() {
    if (!topic.trim()) return alert('Введите тему');
    loading = true;
    generatedContent = '';
    
    try {
      const res = await fetch(`${API_URL}/ai/generate-post`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ topic, platform, tone, model: selectedModel })
      });
      const data = await res.json();
      if (data.content) {
        generatedContent = data.content;
      } else {
        alert('Ошибка: ' + (data.detail || 'Unknown'));
      }
    } catch (e) {
      alert('Ошибка генерации');
    } finally {
      loading = false;
    }
  }
  
  async function generatePlan() {
    if (!topic.trim()) return alert('Введите тему');
    loading = true;
    contentPlan = [];
    
    try {
      const res = await fetch(`${API_URL}/ai/content-plan`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ topic, platform, days: planDays, model: selectedModel })
      });
      const data = await res.json();
      if (Array.isArray(data.plan)) {
        contentPlan = data.plan;
      } else {
        alert('Ошибка парсинга плана');
      }
    } catch (e) {
      alert('Ошибка генерации');
    } finally {
      loading = false;
    }
  }
  
  function copyToClipboard() {
    navigator.clipboard.writeText(generatedContent);
    alert('Скопировано!');
  }
  
  function schedulePost() {
    localStorage.setItem('draft_content', generatedContent);
    localStorage.setItem('draft_platform', platform);
    window.location.href = '/create';
  }
</script>

<div class="max-w-4xl mx-auto">
  <h1 class="text-2xl font-bold text-purple-400 mb-6">AI Генератор контента</h1>
  
  <div class="flex gap-2 mb-6">
    <button 
      class="px-4 py-2 rounded-lg font-medium transition {activeTab === 'post' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}"
      on:click={() => activeTab = 'post'}
    >
      Создать пост
    </button>
    <button 
      class="px-4 py-2 rounded-lg font-medium transition {activeTab === 'plan' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}"
      on:click={() => activeTab = 'plan'}
    >
      Контент-план
    </button>
  </div>
  
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
      <h2 class="text-lg font-semibold text-purple-300 mb-4">Настройки</h2>
      
      <div class="mb-4">
        <label class="block text-sm text-gray-400 mb-1">LLM Модель</label>
        <select bind:value={selectedModel} class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-purple-500 focus:outline-none">
          {#each models as m}
            <option value={m.name}>{m.name} ({m.provider})</option>
          {/each}
        </select>
      </div>
      
      <div class="mb-4">
        <label class="block text-sm text-gray-400 mb-1">Платформа</label>
        <div class="flex gap-2">
          <button class="flex-1 py-2 rounded-lg transition {platform === 'telegram' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300'}" on:click={() => platform = 'telegram'}>Telegram</button>
          <button class="flex-1 py-2 rounded-lg transition {platform === 'linkedin' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300'}" on:click={() => platform = 'linkedin'}>LinkedIn</button>
          <button class="flex-1 py-2 rounded-lg transition {platform === 'vk' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300'}" on:click={() => platform = 'vk'}>VK</button>
        </div>
      </div>
      
      <div class="mb-4">
        <label class="block text-sm text-gray-400 mb-1">Тема / Промпт</label>
        <textarea 
          bind:value={topic} 
          placeholder="Опишите тему поста, ключевые тезисы, целевую аудиторию...

Например:
- AI в бизнесе — как автоматизировать рутину
- Продуктивность для предпринимателей
- Кейс: увеличили конверсию на 30%"
          rows="6"
          class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none resize-none"
        ></textarea>
        <div class="text-right text-xs text-gray-500 mt-1">{topic.length} символов</div>
      </div>
      
      {#if activeTab === 'post'}
        <div class="mb-4">
          <label class="block text-sm text-gray-400 mb-1">Тон</label>
          <select bind:value={tone} class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-purple-500 focus:outline-none">
            {#each tones as t}
              <option value={t.value}>{t.label}</option>
            {/each}
          </select>
        </div>
        <button on:click={generatePost} disabled={loading} class="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white py-3 rounded-lg font-medium transition">
          {loading ? 'Генерация...' : '✨ Сгенерировать пост'}
        </button>
      {:else}
        <div class="mb-4">
          <label class="block text-sm text-gray-400 mb-1">Дней: {planDays}</label>
          <input type="range" bind:value={planDays} min="3" max="30" class="w-full" />
        </div>
        <button on:click={generatePlan} disabled={loading} class="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white py-3 rounded-lg font-medium transition">
          {loading ? 'Генерация...' : '📅 Создать контент-план'}
        </button>
      {/if}
    </div>
    
    <div class="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
      <h2 class="text-lg font-semibold text-purple-300 mb-4">{activeTab === 'post' ? 'Результат' : 'Контент-план'}</h2>
      
      {#if activeTab === 'post'}
        {#if generatedContent}
          <div class="bg-gray-900 rounded-lg p-4 mb-4 min-h-[200px] max-h-[400px] overflow-y-auto whitespace-pre-wrap text-gray-200">{generatedContent}</div>
          <div class="flex gap-2">
            <button on:click={copyToClipboard} class="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg transition">📋 Копировать</button>
            <button on:click={schedulePost} class="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg transition">📅 Запланировать</button>
          </div>
        {:else}
          <div class="text-gray-500 text-center py-12">{loading ? '⏳ Генерируем...' : 'Введите тему и нажмите "Сгенерировать"'}</div>
        {/if}
      {:else}
        {#if contentPlan.length > 0}
          <div class="space-y-3 max-h-[400px] overflow-y-auto">
            {#each contentPlan as item}
              <div class="bg-gray-900 rounded-lg p-3 hover:bg-gray-800 transition cursor-pointer" on:click={() => { topic = item.title; activeTab = 'post'; generatePost(); }}>
                <div class="flex justify-between items-start mb-1">
                  <span class="text-purple-400 font-medium">День {item.day}</span>
                  <span class="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300">{item.type}</span>
                </div>
                <p class="text-white font-medium">{item.title}</p>
                <p class="text-gray-400 text-sm">{item.description}</p>
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-gray-500 text-center py-12">{loading ? '⏳ Создаём план...' : 'Укажите тему и создайте план'}</div>
        {/if}
      {/if}
    </div>
  </div>
</div>
