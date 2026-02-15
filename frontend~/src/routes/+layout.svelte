<script>
  import '../app.css';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  
  let user = null;
  let loading = true;
  let checked = false;
  const publicPages = ['/login'];
  
  onMount(() => { 
    checkAuth(); 
  });
  
  async function checkAuth() {
    if (checked) return;
    checked = true;
    
    const token = localStorage.getItem('access_token');
    if (!token) {
      loading = false;
      if (!publicPages.includes($page.url.pathname)) {
        goto('/login');
      }
      return;
    }
    
    try {
      const res = await fetch('/api/auth/check', { 
        headers: { 'Authorization': `Bearer ${token}` } 
      });
      if (res.ok) {
        user = { 
          email: localStorage.getItem('user_email'), 
          id: localStorage.getItem('user_id') 
        };
      } else {
        clearAuth();
        if (!publicPages.includes($page.url.pathname)) {
          goto('/login');
        }
      }
    } catch (e) { 
      clearAuth(); 
    } finally { 
      loading = false; 
    }
  }
  
  function clearAuth() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_id');
    user = null;
  }
  
  async function logout() {
    const token = localStorage.getItem('access_token');
    if (token) {
      try { 
        await fetch('/api/auth/logout', { 
          method: 'POST', 
          headers: { 'Content-Type': 'application/json' }, 
          body: JSON.stringify({ access_token: token }) 
        }); 
      } catch (e) {}
    }
    clearAuth();
    goto('/login');
  }
</script>

<div class="min-h-screen bg-gray-900 text-white">
  {#if loading}
    <div class="flex items-center justify-center min-h-screen">
      <div class="animate-spin h-8 w-8 border-4 border-purple-500 border-t-transparent rounded-full"></div>
    </div>
  {:else}
    {#if user || publicPages.includes($page.url.pathname)}
      <header class="border-b border-gray-800 px-6 py-4">
        <div class="max-w-6xl mx-auto flex justify-between items-center">
          <a href="/" class="text-xl font-bold text-purple-400">VYUD Publisher</a>
          {#if user}
            <nav class="flex gap-2 items-center">
              <a href="/" class="px-4 py-2 rounded-lg transition {$page.url.pathname === '/' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'}">Календарь</a>
              <a href="/create" class="px-4 py-2 rounded-lg transition {$page.url.pathname === '/create' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'}">Создать пост</a>
              <a href="/generate" class="px-4 py-2 rounded-lg transition {$page.url.pathname === '/generate' ? 'bg-purple-600 text-white' : 'text-purple-400 hover:text-purple-300'}">✨ AI</a>
              <a href="/settings" class="px-4 py-2 rounded-lg transition {$page.url.pathname === '/settings' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'}">Настройки</a>
              <a href="/analytics" class="px-4 py-2 rounded-lg transition {$page.url.pathname === '/analytics' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'}">📊 Аналитика</a>
              <div class="ml-4 pl-4 border-l border-gray-700 flex items-center gap-3">
                <span class="text-sm text-gray-400">{user.email}</span>
                <button on:click={logout} class="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition">Выйти</button>
              </div>
            </nav>
          {/if}
        </div>
      </header>
    {/if}
    <main class="p-6"><slot /></main>
  {/if}
</div>
