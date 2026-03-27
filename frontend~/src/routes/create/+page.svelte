<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { apiFetch } from '$lib/api';

	type Account = { id: string; name: string; platform: string };

	let content = '';
	let platform = 'telegram';
	let accountId = '';
	let scheduledAt = '';
	let accounts: Account[] = [];
	let loading = false;
	let error = '';
	let success = '';

	const PLATFORMS = [
		{ value: 'telegram', label: 'Telegram' },
		{ value: 'linkedin', label: 'LinkedIn' },
		{ value: 'vk', label: 'VK' }
	];

	onMount(async () => {
		try {
			const res = await apiFetch('/api/accounts/');
			if (res.ok) accounts = await res.json();
		} catch {}
	});

	$: filteredAccounts = accounts.filter((a) => a.platform === platform);

	async function submitPost() {
		error = '';
		success = '';
		if (!content.trim()) { error = 'Введите текст поста'; return; }
		loading = true;
		try {
			const body: Record<string, any> = {
				content,
				platform,
				status: scheduledAt ? 'scheduled' : 'draft'
			};
			if (accountId) body.account_id = accountId;
			if (scheduledAt) body.scheduled_at = new Date(scheduledAt).toISOString();

			const res = await apiFetch('/api/posts/', {
				method: 'POST',
				body: JSON.stringify(body)
			});
			const data = await res.json();
			if (!res.ok) { error = data.detail || 'Ошибка создания поста'; return; }
			success = scheduledAt ? 'Пост запланирован!' : 'Черновик сохранён!';
			content = '';
			scheduledAt = '';
			accountId = '';
		} catch (e: any) {
			error = e.message || 'Ошибка сети';
		} finally {
			loading = false;
		}
	}

	async function publishNow() {
		error = '';
		success = '';
		if (!content.trim()) { error = 'Введите текст поста'; return; }
		if (!accountId) { error = 'Выберите аккаунт для публикации'; return; }
		loading = true;
		try {
			const body = { content, platform, account_id: accountId, status: 'published' };
			const res = await apiFetch('/api/posts/', {
				method: 'POST',
				body: JSON.stringify(body)
			});
			const data = await res.json();
			if (!res.ok) { error = data.detail || 'Ошибка публикации'; return; }
			success = 'Пост опубликован!';
			content = '';
			accountId = '';
		} catch (e: any) {
			error = e.message || 'Ошибка сети';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Создать пост — VYUD Publisher</title>
</svelte:head>

<div class="max-w-3xl mx-auto px-4 py-8">
	<div class="mb-6">
		<h1 class="text-2xl font-bold text-gray-100">Создать пост</h1>
		<p class="text-sm text-gray-400 mt-1">Напишите текст, выберите платформу и опубликуйте или запланируйте</p>
	</div>

	<div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-5">
		<!-- Platform selector -->
		<div>
			<label class="block text-sm text-gray-400 mb-2">Платформа</label>
			<div class="flex gap-2">
				{#each PLATFORMS as p}
					<button
						on:click={() => { platform = p.value; accountId = ''; }}
						class="px-4 py-2 rounded-xl text-sm font-medium transition-colors
							{platform === p.value
							? 'bg-violet-600 text-white'
							: 'bg-gray-800 text-gray-300 hover:bg-gray-700'}"
					>
						{p.label}
					</button>
				{/each}
			</div>
		</div>

		<!-- Account -->
		{#if filteredAccounts.length > 0}
			<div>
				<label class="block text-sm text-gray-400 mb-2">Аккаунт</label>
				<select
					bind:value={accountId}
					class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500"
				>
					<option value="">— Выберите аккаунт —</option>
					{#each filteredAccounts as acc}
						<option value={acc.id}>{acc.name}</option>
					{/each}
				</select>
			</div>
		{:else}
			<p class="text-xs text-yellow-400 bg-yellow-900/20 border border-yellow-800 rounded-xl px-4 py-2">
				Нет аккаунтов для {platform}.
				<a href="/settings" class="underline hover:text-yellow-300">Добавить в настройках →</a>
			</p>
		{/if}

		<!-- Content -->
		<div>
			<label class="block text-sm text-gray-400 mb-2">Текст поста</label>
			<textarea
				bind:value={content}
				rows="8"
				placeholder="Введите текст поста..."
				class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500 resize-y"
			></textarea>
			<p class="text-right text-xs text-gray-500 mt-1">{content.length} символов</p>
		</div>

		<!-- Schedule -->
		<div>
			<label class="block text-sm text-gray-400 mb-2">Запланировать (опционально)</label>
			<input
				type="datetime-local"
				bind:value={scheduledAt}
				class="bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500"
			/>
		</div>

		{#if error}
			<div class="bg-red-900/40 border border-red-700 rounded-xl px-4 py-3 text-sm text-red-300">{error}</div>
		{/if}
		{#if success}
			<div class="bg-green-900/40 border border-green-700 rounded-xl px-4 py-3 text-sm text-green-300">{success}</div>
		{/if}

		<!-- Actions -->
		<div class="flex gap-3 flex-wrap">
			<button
				on:click={submitPost}
				disabled={loading}
				class="flex-1 bg-violet-600 hover:bg-violet-500 disabled:opacity-60 text-white font-semibold rounded-xl py-3 transition-colors text-sm"
			>
				{scheduledAt ? 'Запланировать' : 'Сохранить черновик'}
			</button>
			<button
				on:click={publishNow}
				disabled={loading || !accountId}
				class="flex-1 bg-green-700 hover:bg-green-600 disabled:opacity-60 text-white font-semibold rounded-xl py-3 transition-colors text-sm"
			>
				Опубликовать сейчас
			</button>
		</div>
	</div>
</div>
