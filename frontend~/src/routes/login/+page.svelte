<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let email = '';
	let password = '';
	let error = '';
	let loading = false;
	let isRegister = false;

	onMount(() => {
		if (typeof localStorage !== 'undefined' && localStorage.getItem('access_token')) {
			goto('/');
		}
	});

	async function submit() {
		error = '';
		loading = true;
		const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';
		try {
			const res = await fetch(endpoint, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email, password })
			});
			const data = await res.json();
			if (!res.ok) {
				error = data.detail || 'Ошибка входа';
				return;
			}
			if (data.access_token) {
				localStorage.setItem('access_token', data.access_token);
				goto('/');
			} else {
				error = 'Не получен токен авторизации';
			}
		} catch (e) {
			error = 'Ошибка сети. Попробуйте снова.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Вход — VYUD Publisher</title>
</svelte:head>

<div class="min-h-screen bg-gray-950 flex items-center justify-center p-4">
	<div class="w-full max-w-sm">
		<h1 class="text-center text-violet-400 text-2xl font-bold mb-1">VYUD Publisher</h1>
		<p class="text-center text-gray-400 text-sm mb-8">
			{isRegister ? 'Создайте аккаунт' : 'Войдите в систему'}
		</p>

		<div class="bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-xl">
			<form on:submit|preventDefault={submit} class="flex flex-col gap-4">
				<div class="flex flex-col gap-1">
					<label for="email" class="text-sm text-gray-400">Email</label>
					<input
						id="email"
						type="email"
						bind:value={email}
						required
						autocomplete="email"
						class="bg-gray-50 text-gray-900 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-violet-500"
						placeholder="you@example.com"
					/>
				</div>

				<div class="flex flex-col gap-1">
					<label for="password" class="text-sm text-gray-400">Пароль</label>
					<input
						id="password"
						type="password"
						bind:value={password}
						required
						autocomplete={isRegister ? 'new-password' : 'current-password'}
						class="bg-gray-50 text-gray-900 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-violet-500"
						placeholder="••••••••"
					/>
				</div>

				{#if error}
					<div class="bg-red-900/50 border border-red-700 rounded-xl px-4 py-3 text-sm text-red-300">
						{error}
					</div>
				{/if}

				<button
					type="submit"
					disabled={loading}
					class="bg-violet-600 hover:bg-violet-500 disabled:opacity-60 text-white font-semibold rounded-xl py-3 transition-colors"
				>
					{loading ? 'Подождите...' : isRegister ? 'Зарегистрироваться' : 'Войти'}
				</button>
			</form>
		</div>

		<p class="text-center text-sm text-gray-400 mt-6">
			{#if isRegister}
				Уже есть аккаунт?
				<button
					on:click={() => { isRegister = false; error = ''; }}
					class="text-violet-400 hover:text-violet-300 font-medium"
				>Войти</button>
			{:else}
				Нет аккаунта?
				<button
					on:click={() => { isRegister = true; error = ''; }}
					class="text-violet-400 hover:text-violet-300 font-medium"
				>Зарегистрируйтесь</button>
			{/if}
		</p>
	</div>
</div>
