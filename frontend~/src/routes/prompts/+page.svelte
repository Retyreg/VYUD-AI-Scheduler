<script>
  import { onMount } from 'svelte';

  const API_URL = 'https://publisher.vyud.tech/api';
  let prompts = [];
  let loading = true;
  let error = '';
  let filterType = 'all';

  const typeLabels = {
    post: 'Генерация поста',
    content_plan: 'Контент-план', 
    tone: 'Тон/стиль'
  };

  const typeColors = {
    post: 'bg-purple-600',
    content_plan: 'bg-emerald-600',
    tone: 'bg-amber-600'
  };

  onMount(loadPrompts);

  async function loadPrompts() {
    loading = true;
    try {
      const res = await fetch(`${API_URL}/prompts/`);
      prompts = await res.json();
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  $: filteredPrompts = filterType === 'all' 
    ? prompts 
    : prompts.filter(p => p.type === filterType);
</script>

<div class="max-w-5xl mx-auto">
  <div class="flex justify-between items-center mb-6">
    <div>
      <h1 class="text-2xl font-bold text-white">Шаблоны промптов</h1>
      <p class="text-gray-400 text-sm mt-1">Управляйте промптами для AI-генерации</p>
    </div>
    <button class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition">
      + Новый шаблон
    </button>
  </div>

  {#if error}
    <div class="bg-red-500/20 text-red-400 px-4 py-2 rounded-lg mb-4">
      {error}
    </div>
  {/if}

  <!-- Фильтры -->
  <div class="flex gap-2 mb-6">
    {#each [['all', 'Все'], ['post', 'Посты'], ['content_plan', 'Контент-план'], ['tone', 'Тон/стиль']] as [val, label]}
      <button
        on:click={() => filterType = val}
        class="px-3 py-1.5 rounded-lg text-sm transition {filterType === val ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'}"
      >
        {label}
      </button>
    {/each}
  </div>

  <!-- Список промптов -->
  {#if loading}
    <p class="text-gray-500 text-center py-12">Загрузка...</p>
  {:else if filteredPrompts.length === 0}
    <div class="text-center py-12 bg-gray-800/50 rounded-xl border border-gray-700">
      <p class="text-gray-500 mb-3">Нет шаблонов</p>
      <button class="text-purple-400 hover:text-purple-300">Создать первый</button>
    </div>
  {:else}
    <div class="space-y-3">
      {#each filteredPrompts as prompt (prompt.id)}
        <div class="bg-gray-800/50 rounded-xl border border-gray-700 p-4">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs px-2 py-0.5 rounded text-white {typeColors[prompt.type] || 'bg-gray-600'}">
                  {typeLabels[prompt.type] || prompt.type}
                </span>
                {#if prompt.platform}
                  <span class="text-xs px-2 py-0.5 rounded bg-gray-600 text-gray-300">
                    {prompt.platform}
                  </span>
                {/if}
                {#if prompt.is_default}
                  <span class="text-xs px-2 py-0.5 rounded bg-yellow-600/30 text-yellow-400">по умолчанию</span>
                {/if}
              </div>
              <h3 class="text-white font-medium">{prompt.name}</h3>
              <p class="text-gray-400 text-sm mt-1 line-clamp-2">{prompt.content.substring(0, 150)}{prompt.content.length > 150 ? '...' : ''}</p>
              {#if prompt.variables && prompt.variables.length > 0}
                <div class="flex gap-1 mt-2">
                  {#each prompt.variables as v}
                    <span class="text-xs px-1.5 py-0.5 rounded bg-gray-700 text-gray-400 font-mono">{`{{${v}}}`}</span>
                  {/each}
                </div>
              {/if}
            </div>
            <div class="flex gap-1 ml-4">
              <button class="p-2 rounded hover:bg-gray-700 text-gray-400 transition" title="Редактировать">
                ✏️
              </button>
              <button class="p-2 rounded hover:bg-gray-700 text-gray-400 transition" title="Дублировать">
                📋
              </button>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
