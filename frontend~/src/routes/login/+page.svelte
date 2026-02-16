<script>
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  
  let mode = 'login';
  let email = '';
  let password = '';
  let confirmPassword = '';
  let error = '';
  let success = '';
  let loading = false;
  
  onMount(() => {
    const token = localStorage.getItem('access_token');
    if (token) checkAuth(token);
  });
  
  async function checkAuth(token) {
    try {
      const res = await fetch('/api/auth/check', { headers: { 'Authorization': `Bearer ${token}` } });
      if (res.ok) goto('/');
    } catch (e) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }
  
  async function handleSubmit() {
    error = ''; success = '';
    if (!email || !password) { error = 'Заполните все поля'; return; }
    if (mode === 'register') {
      if (password !== confirmPassword) { error = 'Пароли не совпадают'; return; }
      if (password.length < 6) { error = 'Пароль минимум 6 символов'; return; }
    }
    loading = true;
    try {
      const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register';
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Ошибка');
      if (mode === 'register') {
        success = 'Регистрация успешна! Проверьте email.';
        mode = 'login'; password = ''; confirmPassword = '';
      } else {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user_email', data.user.email);
        localStorage.setItem('user_id', data.user.id);
        goto('/');
      }
    } catch (e) { error = e.message; }
    finally { loading = false; }
  }
</script>

<div class="max-w-md mx-auto mt-20">
  <div class="bg-gray-800 rounded-xl p-8 shadow-xl">
    <div class="text-center mb-8">
      <h1 class="text-2xl font-bold text-purple-400">VYUD Publisher</h1>
      <p class="text-gray-400 mt-2">{mode === 'login' ? 'Войдите в систему' : 'Создайте аккаунт'}</p>
    </div>
    <form on:submit|preventDefault={handleSubmit} class="space-y-4">
      <div>
        <label class="block text-sm text-gray-400 mb-1">Email</label>
        <input type="email" bind:value={email} class="w-full px-4 py-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none text-white" placeholder="your@email.com" disabled={loading} />
      </div>
      <div>
        <label class="block text-sm text-gray-400 mb-1">Пароль</label>
        <input type="password" bind:value={password} class="w-full px-4 py-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none text-white" placeholder="••••••••" disabled={loading} />
      </div>
      {#if mode === 'register'}
        <div>
          <label class="block text-sm text-gray-400 mb-1">Подтвердите пароль</label>
          <input type="password" bind:value={confirmPassword} class="w-full px-4 py-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none text-white" placeholder="••••••••" disabled={loading} />
        </div>
      {/if}
      {#if error}<div class="bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded-lg">{error}</div>{/if}
      {#if success}<div class="bg-green-900/50 border border-green-700 text-green-300 px-4 py-3 rounded-lg">{success}</div>{/if}
      <button type="submit" class="w-full py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium transition disabled:opacity-50" disabled={loading}>
        {loading ? 'Загрузка...' : (mode === 'login' ? 'Войти' : 'Зарегистрироваться')}
      </button>
    </form>
    <div class="mt-6 text-center">
      <button on:click={() => { mode = mode === 'login' ? 'register' : 'login'; error = ''; success = ''; }} class="text-purple-400 hover:text-purple-300">
        {mode === 'login' ? 'Нет аккаунта? Зарегистрируйтесь' : 'Уже есть аккаунт? Войдите'}
      </button>
    </div>
  </div>
</div>
