<script>
  import { onMount } from 'svelte';
  
  let posts = [];
  let loading = true;
  let error = '';
  let currentMonth = new Date();
  let selectedDay = null;
  let editingPost = null;
  let newScheduledDate = '';
  let newScheduledTime = '';
  let deleteConfirm = null;
  
  const API_URL = 'https://publisher.vyud.tech/api';
  
  const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
  const dayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
  
  onMount(async () => {
    await loadPosts();
  });
  
  async function loadPosts() {
    try {
      const res = await fetch(`${API_URL}/posts/`);
      const data = await res.json();
      posts = [...data];
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }
  
  function getDaysInMonth(date) {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    let startDay = firstDay.getDay() - 1;
    if (startDay < 0) startDay = 6;
    
    const days = [];
    for (let i = 0; i < startDay; i++) days.push(null);
    for (let i = 1; i <= daysInMonth; i++) days.push(i);
    return days;
  }
  
  $: calendarCells = getDaysInMonth(currentMonth).map(day => ({
    day,
    posts: day ? posts.filter(p => {
      const d = new Date(p.scheduled_at);
      return d.getFullYear() === currentMonth.getFullYear() && 
             d.getMonth() === currentMonth.getMonth() && 
             d.getDate() === day;
    }) : []
  }));

  $: scheduledPosts = posts.filter(p => p.status === 'scheduled').sort((a, b) => 
    new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()
  );

  $: selectedDayPosts = selectedDay ? (calendarCells.find(c => c.day === selectedDay)?.posts || []) : [];
  
  function isToday(day) {
    if (!day) return false;
    const today = new Date();
    return today.getFullYear() === currentMonth.getFullYear() &&
           today.getMonth() === currentMonth.getMonth() &&
           today.getDate() === day;
  }
  
  function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('ru-RU', { 
      day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' 
    });
  }
  
  function formatTime(dateStr) {
    return new Date(dateStr).toLocaleTimeString('ru-RU', { 
      hour: '2-digit', minute: '2-digit' 
    });
  }
  
  function getStatusColor(status) {
    if (status === 'published') return 'bg-green-500';
    if (status === 'scheduled') return 'bg-blue-500';
    if (status === 'failed') return 'bg-red-500';
    return 'bg-gray-500';
  }

  function getStatusLabel(status) {
    if (status === 'published') return 'Опубликован';
    if (status === 'scheduled') return 'Запланирован';
    if (status === 'failed') return 'Ошибка';
    return status;
  }

  function getPlatformIcon(platform) {
    if (platform === 'telegram') return '✈';
    if (platform === 'linkedin') return 'in';
    return '?';
  }
  
  function getPlatformColor(platform) {
    if (platform === 'telegram') return 'bg-sky-500';
    if (platform === 'linkedin') return 'bg-blue-700';
    return 'bg-gray-500';
  }

  function selectDay(day) {
    if (!day) return;
    selectedDay = selectedDay === day ? null : day;
    editingPost = null;
    deleteConfirm = null;
  }

  async function deletePost(postId) {
    try {
      const res = await fetch(`${API_URL}/posts/${postId}`, { method: 'DELETE' });
      if (res.ok) {
        posts = posts.filter(p => p.id !== postId);
        deleteConfirm = null;
        if (selectedDayPosts.length <= 1) selectedDay = null;
      } else {
        const data = await res.json().catch(() => ({}));
        alert('Ошибка удаления: ' + (data.detail || res.statusText));
      }
    } catch (e) {
      alert('Ошибка: ' + e.message);
    }
  }

  function startReschedule(post) {
    editingPost = post.id;
    const dt = new Date(post.scheduled_at);
    newScheduledDate = dt.toISOString().split('T')[0];
    newScheduledTime = dt.toTimeString().slice(0, 5);
  }

  function cancelReschedule() {
    editingPost = null;
    newScheduledDate = '';
    newScheduledTime = '';
  }

  async function reschedulePost(postId) {
    if (!newScheduledDate || !newScheduledTime) return;
    const newDt = new Date(newScheduledDate + 'T' + newScheduledTime + ':00');
    const isoStr = newDt.toISOString();
    
    try {
      const res = await fetch(`${API_URL}/posts/${postId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scheduled_at: isoStr })
      });
      if (res.ok) {
        const updated = await res.json();
        posts = posts.map(p => p.id === postId ? { ...p, scheduled_at: updated.scheduled_at || isoStr } : p);
        editingPost = null;
        selectedDay = null;
      } else {
        const data = await res.json().catch(() => ({}));
        alert('Ошибка переноса: ' + (data.detail || res.statusText));
      }
    } catch (e) {
      alert('Ошибка: ' + e.message);
    }
  }
</script>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
  <div class="lg:col-span-2 bg-gray-800/50 rounded-xl p-6 border border-gray-700">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-bold text-white">{monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()} г.</h2>
      <div class="flex gap-2">
        <button on:click={() => { currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1); selectedDay = null; }} class="p-2 hover:bg-gray-700 rounded-lg text-gray-400">&#8592;</button>
        <button on:click={() => { currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1); selectedDay = null; }} class="p-2 hover:bg-gray-700 rounded-lg text-gray-400">&#8594;</button>
      </div>
    </div>
    
    <div class="grid grid-cols-7 gap-1 mb-2">
      {#each dayNames as name}
        <div class="text-center text-sm text-gray-500 py-2">{name}</div>
      {/each}
    </div>
    
    <div class="grid grid-cols-7 gap-1">
      {#each calendarCells as cell}
        <button 
          class="aspect-square p-1.5 rounded-lg text-left transition-all
            {cell.day ? 'bg-gray-700/50 hover:bg-gray-600/50 cursor-pointer' : 'cursor-default'} 
            {isToday(cell.day) ? 'ring-2 ring-purple-500' : ''} 
            {selectedDay === cell.day && cell.day ? 'ring-2 ring-white bg-gray-600/70' : ''}"
          on:click={() => selectDay(cell.day)}
        >
          {#if cell.day}
            <div class="h-full flex flex-col">
              <span class="text-sm text-gray-300">{cell.day}</span>
              {#if cell.posts.length > 0}
                <div class="flex flex-wrap gap-0.5 mt-1">
                  {#each cell.posts as post}
                    <span 
                      class="inline-flex items-center justify-center w-5 h-5 rounded text-[9px] font-bold text-white {getPlatformColor(post.platform)} {post.status === 'failed' ? 'opacity-50' : ''}"
                      title="{post.platform} ({getStatusLabel(post.status)}): {post.content.substring(0, 80)}"
                    >
                      {getPlatformIcon(post.platform)}
                    </span>
                  {/each}
                </div>
              {/if}
            </div>
          {/if}
        </button>
      {/each}
    </div>
    
    <div class="mt-4 flex flex-wrap items-center gap-4 text-xs text-gray-500">
      <span>Всего: {posts.length} | Запланировано: {scheduledPosts.length}</span>
      <span class="flex items-center gap-1"><span class="w-4 h-4 rounded bg-sky-500 inline-flex items-center justify-center text-[8px] text-white font-bold">&#9992;</span> Telegram</span>
      <span class="flex items-center gap-1"><span class="w-4 h-4 rounded bg-blue-700 inline-flex items-center justify-center text-[8px] text-white font-bold">in</span> LinkedIn</span>
    </div>

    {#if selectedDay && selectedDayPosts.length > 0}
      <div class="mt-4 bg-gray-900/70 rounded-xl p-4 border border-gray-600">
        <div class="flex justify-between items-center mb-3">
          <h3 class="text-white font-semibold">{selectedDay} {monthNames[currentMonth.getMonth()]} — {selectedDayPosts.length} пост{selectedDayPosts.length > 1 ? (selectedDayPosts.length < 5 ? 'а' : 'ов') : ''}</h3>
          <button on:click={() => { selectedDay = null; editingPost = null; deleteConfirm = null; }} class="text-gray-500 hover:text-white text-lg">&#10005;</button>
        </div>
        
        <div class="space-y-3">
          {#each selectedDayPosts as post (post.id)}
            <div class="bg-gray-800 rounded-lg p-3 border border-gray-700">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <span class="text-xs px-2 py-1 rounded font-medium text-white {getPlatformColor(post.platform)}">{post.platform}</span>
                  <span class="text-xs px-2 py-0.5 rounded {getStatusColor(post.status)} text-white">{getStatusLabel(post.status)}</span>
                  <span class="text-xs text-gray-500">{formatTime(post.scheduled_at)}</span>
                </div>
              </div>
              
              <p class="text-sm text-gray-300 mb-3 whitespace-pre-wrap">{post.content.substring(0, 200)}{post.content.length > 200 ? '...' : ''}</p>
              
              <div class="flex gap-2">
                {#if post.status === 'scheduled'}
                  <button 
                    on:click={() => startReschedule(post)} 
                    class="text-xs px-3 py-1.5 rounded bg-gray-700 hover:bg-gray-600 text-gray-300 transition"
                  >
                    &#128197; Перенести
                  </button>
                {/if}
                
                {#if deleteConfirm === post.id}
                  <span class="text-xs text-red-400 py-1.5">Точно удалить?</span>
                  <button 
                    on:click={() => deletePost(post.id)} 
                    class="text-xs px-3 py-1.5 rounded bg-red-600 hover:bg-red-700 text-white transition"
                  >
                    Да
                  </button>
                  <button 
                    on:click={() => deleteConfirm = null} 
                    class="text-xs px-3 py-1.5 rounded bg-gray-700 hover:bg-gray-600 text-gray-300 transition"
                  >
                    Отмена
                  </button>
                {:else}
                  <button 
                    on:click={() => deleteConfirm = post.id} 
                    class="text-xs px-3 py-1.5 rounded bg-gray-700 hover:bg-red-600/20 text-red-400 transition"
                  >
                    &#128465; Удалить
                  </button>
                {/if}
              </div>

              {#if editingPost === post.id}
                <div class="mt-3 p-3 bg-gray-900 rounded-lg border border-gray-600">
                  <p class="text-xs text-gray-400 mb-2">Новая дата и время:</p>
                  <div class="flex flex-wrap gap-2 items-center">
                    <input type="date" bind:value={newScheduledDate} class="text-sm bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-white" />
                    <input type="time" bind:value={newScheduledTime} class="text-sm bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-white" />
                    <button on:click={() => reschedulePost(post.id)} class="text-xs px-3 py-1.5 rounded bg-purple-600 hover:bg-purple-700 text-white transition">Сохранить</button>
                    <button on:click={cancelReschedule} class="text-xs px-3 py-1.5 rounded bg-gray-700 hover:bg-gray-600 text-gray-300 transition">Отмена</button>
                  </div>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {:else if selectedDay}
      <div class="mt-4 bg-gray-900/70 rounded-xl p-4 border border-gray-600">
        <div class="flex justify-between items-center">
          <p class="text-gray-500 text-sm">{selectedDay} {monthNames[currentMonth.getMonth()]} — нет постов</p>
          <button on:click={() => selectedDay = null} class="text-gray-500 hover:text-white text-lg">&#10005;</button>
        </div>
        <a href="/create" class="text-purple-400 hover:text-purple-300 text-sm mt-2 inline-block">+ Создать пост на этот день</a>
      </div>
    {/if}
  </div>
  
  <div class="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-white">Запланировано</h2>
      <a href="/create" class="text-purple-400 hover:text-purple-300 text-sm">+ Добавить</a>
    </div>
    
    {#if loading}
      <p class="text-gray-500 text-center py-8">Загрузка...</p>
    {:else if scheduledPosts.length === 0}
      <div class="text-center py-8">
        <p class="text-gray-500 mb-2">Нет запланированных постов</p>
        <a href="/create" class="text-purple-400 hover:text-purple-300">Создать первый пост</a>
      </div>
    {:else}
      <div class="space-y-3 max-h-[600px] overflow-y-auto">
        {#each scheduledPosts as post (post.id)}
          <div class="bg-gray-900/50 rounded-lg p-3 hover:bg-gray-900 transition">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-xs px-2 py-1 rounded font-medium text-white {getPlatformColor(post.platform)}">{post.platform}</span>
              <span class="text-xs text-gray-500">{formatDate(post.scheduled_at)}</span>
            </div>
            <p class="text-sm text-gray-300 line-clamp-2">{post.content.substring(0, 100)}...</p>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<a href="/create" class="fixed bottom-6 right-6 w-14 h-14 bg-purple-600 hover:bg-purple-700 rounded-full flex items-center justify-center text-white text-2xl shadow-lg transition">+</a>
