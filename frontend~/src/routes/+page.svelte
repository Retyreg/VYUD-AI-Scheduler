<script>
  import { onMount } from 'svelte';
  
  let posts = [];
  let loading = true;
  let error = '';
  let currentDate = new Date();
  let selectedDay = null;
  let showModal = false;
  
  $: currentMonth = currentDate.getMonth();
  $: currentYear = currentDate.getFullYear();
  $: monthName = currentDate.toLocaleString('ru', { month: 'long', year: 'numeric' });
  $: daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  $: firstDay = (() => {
    const day = new Date(currentYear, currentMonth, 1).getDay();
    return day === 0 ? 6 : day - 1;
  })();
  $: days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  $: emptyDays = Array.from({ length: firstDay }, (_, i) => i);
  
  function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }
  
  onMount(async () => {
    await loadPosts();
  });
  
  async function loadPosts() {
    loading = true;
    error = '';
    try {
      const res = await fetch('/api/posts/', { headers: getAuthHeaders() });
      if (res.status === 401) {
        window.location.href = '/login';
        return;
      }
      if (!res.ok) throw new Error('Failed to load posts');
      posts = await res.json();
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }
  
  function prevMonth() {
    currentDate = new Date(currentYear, currentMonth - 1, 1);
  }
  
  function nextMonth() {
    currentDate = new Date(currentYear, currentMonth + 1, 1);
  }
  
  function getPlatformColor(platform) {
    const colors = { telegram: 'bg-blue-500', linkedin: 'bg-blue-700', vk: 'bg-sky-600' };
    return colors[platform] || 'bg-gray-500';
  }
  
  function formatTime(dateStr) {
    return new Date(dateStr).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' });
  }
  
  function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('ru', { day: 'numeric', month: 'short' });
  }
  
  function isToday(day) {
    const today = new Date();
    return day === today.getDate() && currentMonth === today.getMonth() && currentYear === today.getFullYear();
  }
  
  $: scheduledPosts = posts.filter(p => p.status === 'scheduled').sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));
  
  $: postsMap = posts.reduce((map, post) => {
    const d = new Date(post.scheduled_at);
    const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
    if (!map[key]) map[key] = [];
    map[key].push(post);
    return map;
  }, {});
  
  $: getPostsForDay = (day) => {
    const key = `${currentYear}-${currentMonth}-${day}`;
    return postsMap[key] || [];
  };
  
  // Посты для выбранного дня в модалке
  $: selectedDayPosts = selectedDay ? getPostsForDay(selectedDay) : [];
  
  function openDayModal(day) {
    selectedDay = day;
    showModal = true;
  }
  
  function closeModal() {
    showModal = false;
    selectedDay = null;
  }
</script>

<svelte:head>
  <title>Календарь — VYUD Publisher</title>
</svelte:head>

<div class="max-w-6xl mx-auto flex gap-6">
  <div class="flex-1 bg-gray-800 rounded-xl p-6">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-semibold capitalize">{monthName}</h2>
      <div class="flex gap-2">
        <button on:click={prevMonth} class="p-2 hover:bg-gray-700 rounded-lg">←</button>
        <button on:click={nextMonth} class="p-2 hover:bg-gray-700 rounded-lg">→</button>
      </div>
    </div>
    
    <div class="grid grid-cols-7 gap-1 mb-2">
      {#each ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'] as dayName}
        <div class="text-center text-gray-500 text-sm py-2">{dayName}</div>
      {/each}
    </div>
    
    {#key posts.length + currentMonth}
    <div class="grid grid-cols-7 gap-1">
      {#each emptyDays as _, i}
        <div class="aspect-square"></div>
      {/each}
      
      {#each days as day}
        {@const dayPosts = getPostsForDay(day)}
        <button 
          on:click={() => openDayModal(day)}
          class="aspect-square bg-gray-700/50 rounded-lg p-1 text-left hover:bg-gray-600/50 transition cursor-pointer {isToday(day) ? 'ring-2 ring-purple-500' : ''}"
        >
          <div class="text-xs text-gray-400">{day}</div>
          {#if dayPosts.length > 0}
            <div class="flex flex-wrap gap-0.5 mt-1">
              {#each dayPosts.slice(0, 4) as post}
                <div class="w-5 h-5 {getPlatformColor(post.platform)} rounded text-[10px] flex items-center justify-center text-white font-bold">
                  {#if post.platform === 'telegram'}✈{:else if post.platform === 'linkedin'}in{:else}V{/if}
                </div>
              {/each}
              {#if dayPosts.length > 4}
                <div class="w-5 h-5 bg-gray-600 rounded text-[10px] flex items-center justify-center">+{dayPosts.length - 4}</div>
              {/if}
            </div>
          {/if}
        </button>
      {/each}
    </div>
    {/key}
    
    <div class="mt-4 text-sm text-gray-500">Всего: {posts.length} | Запланировано: {scheduledPosts.length}</div>
  </div>
  
  <div class="w-80 bg-gray-800 rounded-xl p-6">
    <div class="flex justify-between items-center mb-4">
      <h3 class="font-semibold">Запланировано</h3>
      <a href="/create" class="text-purple-400 hover:text-purple-300 text-sm">+ Добавить</a>
    </div>
    
    {#if loading}
      <div class="text-gray-400">Загрузка...</div>
    {:else if scheduledPosts.length === 0}
      <div class="text-gray-400">Нет запланированных постов</div>
    {:else}
      <div class="space-y-3 max-h-[600px] overflow-y-auto">
        {#each scheduledPosts as post}
          <div class="bg-gray-700/50 rounded-lg p-3">
            <div class="flex items-center gap-2 mb-2">
              <span class="px-2 py-0.5 {getPlatformColor(post.platform)} rounded text-xs">{post.platform}</span>
              <span class="text-xs text-gray-400">{formatDate(post.scheduled_at)}, {formatTime(post.scheduled_at)}</span>
            </div>
            <p class="text-sm text-gray-300 line-clamp-3">{post.content}</p>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<!-- Modal для просмотра постов дня -->
{#if showModal}
<div class="fixed inset-0 bg-black/70 flex items-center justify-center z-50" on:click={closeModal}>
  <div class="bg-gray-800 rounded-xl p-6 w-full max-w-lg max-h-[80vh] overflow-y-auto" on:click|stopPropagation>
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-lg font-semibold">
        {selectedDay} {currentDate.toLocaleString('ru', { month: 'long' })} {currentYear}
      </h3>
      <button on:click={closeModal} class="text-gray-400 hover:text-white text-2xl">&times;</button>
    </div>
    
    {#if selectedDayPosts.length === 0}
      <p class="text-gray-400 text-center py-8">Нет постов на этот день</p>
      <a href="/create" class="block text-center py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition">
        + Создать пост
      </a>
    {:else}
      <div class="space-y-4">
        {#each selectedDayPosts as post}
          <div class="bg-gray-700/50 rounded-lg p-4">
            <div class="flex items-center gap-2 mb-2">
              <span class="px-2 py-1 {getPlatformColor(post.platform)} rounded text-xs font-medium">{post.platform}</span>
              <span class="text-sm text-gray-400">{formatTime(post.scheduled_at)}</span>
              <span class="text-xs px-2 py-0.5 rounded {post.status === 'published' ? 'bg-green-600' : post.status === 'scheduled' ? 'bg-yellow-600' : 'bg-gray-600'}">{post.status}</span>
            </div>
            <p class="text-gray-200 whitespace-pre-wrap">{post.content}</p>
          </div>
        {/each}
      </div>
      <a href="/create" class="block text-center py-3 mt-4 bg-purple-600 hover:bg-purple-700 rounded-lg transition">
        + Добавить ещё
      </a>
    {/if}
  </div>
</div>
{/if}
