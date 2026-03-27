<script lang="ts">
	import { onMount } from 'svelte';
	import { apiFetch } from '$lib/api';

	type AnalyticsItem = {
		id: string;
		post_id: string;
		platform: string;
		views: number;
		likes: number;
		shares: number;
		comments: number;
		subscribers: number;
		fetched_at: string;
		updated_at: string;
		post_content?: string;
	};

	type Summary = {
		total_posts: number;
		total_views: number;
		total_likes: number;
		total_comments: number;
		total_shares: number;
		total_subscribers: number;
		by_platform: Record<string, { posts: number; likes: number; comments: number; shares: number; subscribers: number }>;
	};

	let analytics: AnalyticsItem[] = [];
	let summary: Summary | null = null;
	let loading = true;
	let refreshing = false;
	let error = '';
	let refreshMsg = '';

	async function loadData() {
		loading = true;
		error = '';
		try {
			const [aRes, sRes] = await Promise.all([
				apiFetch('/api/analytics/'),
				apiFetch('/api/analytics/summary'),
			]);
			if (aRes.ok) analytics = await aRes.json();
			else { const d = await aRes.json(); error = d.detail || 'Ошибка загрузки'; }
			if (sRes.ok) summary = await sRes.json();
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	async function triggerRefresh() {
		refreshing = true;
		refreshMsg = '';
		try {
			const res = await apiFetch('/api/analytics/refresh', { method: 'POST' });
			if (res.ok) {
				refreshMsg = 'Обновление запущено. Данные появятся через ~30 секунд.';
				setTimeout(loadData, 30000);
			}
		} catch (e: any) {
			error = e.message;
		} finally {
			refreshing = false;
		}
	}

	onMount(loadData);

	function fmt(n: number | null | undefined) {
		if (n == null || n === 0) return '—';
		if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
		if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
		return String(n);
	}

	function fmtDate(dt: string) {
		if (!dt) return '—';
		return new Date(dt).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
	}

	const PLATFORM_COLORS: Record<string, string> = {
		telegram: 'bg-blue-500', linkedin: 'bg-blue-700', vk: 'bg-blue-400'
	};
</script>

<svelte:head>
	<title>Аналитика — VYUD Publisher</title>
</svelte:head>

<div class="max-w-screen-xl mx-auto px-4 py-8">
	<!-- Header -->
	<div class="flex items-center justify-between mb-6 flex-wrap gap-3">
		<div>
			<h1 class="text-2xl font-bold text-gray-100">Аналитика</h1>
			<p class="text-sm text-gray-400 mt-1">
				Метрики по опубликованным постам · обновляется автоматически каждые 30 мин
			</p>
		</div>
		<button
			on:click={triggerRefresh}
			disabled={refreshing}
			class="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-60 text-white text-sm font-medium rounded-xl transition-colors"
		>
			{#if refreshing}
				<span class="animate-spin">↻</span> Обновление...
			{:else}
				↻ Обновить сейчас
			{/if}
		</button>
	</div>

	{#if error}
		<div class="bg-red-900/40 border border-red-700 rounded-xl px-4 py-3 text-sm text-red-300 mb-6">{error}</div>
	{/if}
	{#if refreshMsg}
		<div class="bg-violet-900/40 border border-violet-700 rounded-xl px-4 py-3 text-sm text-violet-300 mb-6">{refreshMsg}</div>
	{/if}

	<!-- Summary cards -->
	{#if summary}
		<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
			{#each [
				['Постов', fmt(summary.total_posts), '📄'],
				['Подписчики', fmt(summary.total_subscribers), '👥'],
				['Лайки', fmt(summary.total_likes), '❤️'],
				['Комменты', fmt(summary.total_comments), '💬'],
				['Репосты', fmt(summary.total_shares), '🔁'],
			] as [label, val, icon]}
				<div class="bg-gray-900 border border-gray-800 rounded-2xl p-4 text-center">
					<p class="text-2xl mb-1">{icon}</p>
					<p class="text-2xl font-bold text-gray-100">{val}</p>
					<p class="text-xs text-gray-400 mt-1">{label}</p>
				</div>
			{/each}
		</div>

		<!-- Per-platform breakdown -->
		{#if Object.keys(summary.by_platform).length > 1}
			<div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
				{#each Object.entries(summary.by_platform) as [platform, stats]}
					<div class="bg-gray-900 border border-gray-800 rounded-2xl p-4">
						<div class="flex items-center gap-2 mb-3">
							<span class="text-xs font-bold text-white px-2 py-0.5 rounded {PLATFORM_COLORS[platform] || 'bg-gray-600'}">
								{platform}
							</span>
							<span class="text-xs text-gray-400">{stats.posts} постов</span>
						</div>
						<div class="grid grid-cols-2 gap-2 text-xs text-gray-300">
							{#if stats.subscribers}
								<span class="text-gray-400">Подписчики</span>
								<span class="text-right font-medium">{fmt(stats.subscribers)}</span>
							{/if}
							<span class="text-gray-400">Лайки</span>
							<span class="text-right font-medium">{fmt(stats.likes)}</span>
							<span class="text-gray-400">Комменты</span>
							<span class="text-right font-medium">{fmt(stats.comments)}</span>
							<span class="text-gray-400">Репосты</span>
							<span class="text-right font-medium">{fmt(stats.shares)}</span>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/if}

	<!-- Table -->
	{#if loading}
		<div class="text-center py-16 text-gray-400">Загрузка...</div>
	{:else if analytics.length === 0}
		<div class="text-center py-16">
			<p class="text-4xl mb-3">📊</p>
			<p class="text-gray-400 mb-2">Нет данных аналитики</p>
			<p class="text-sm text-gray-500">
				Данные появятся после первой публикации поста.<br>
				Telegram: показывает подписчиков канала.<br>
				LinkedIn: лайки, комменты и репосты поста.
			</p>
		</div>
	{:else}
		<div class="bg-gray-900 border border-gray-800 rounded-2xl overflow-x-auto">
			<table class="w-full text-sm">
				<thead>
					<tr class="border-b border-gray-800 text-gray-400 text-xs">
						<th class="text-left px-5 py-3 font-medium">Пост</th>
						<th class="text-left px-5 py-3 font-medium">Платформа</th>
						<th class="text-right px-5 py-3 font-medium">Подписчики</th>
						<th class="text-right px-5 py-3 font-medium">Лайки</th>
						<th class="text-right px-5 py-3 font-medium">Репосты</th>
						<th class="text-right px-5 py-3 font-medium">Комменты</th>
						<th class="text-right px-5 py-3 font-medium">Обновлено</th>
					</tr>
				</thead>
				<tbody>
					{#each analytics as row}
						<tr class="border-b border-gray-800/50 hover:bg-gray-800/40 transition-colors">
							<td class="px-5 py-3 text-gray-200 max-w-xs">
								<p class="truncate">{row.post_content || row.post_id}</p>
							</td>
							<td class="px-5 py-3">
								<span class="inline-block text-xs text-white px-2 py-0.5 rounded {PLATFORM_COLORS[row.platform] || 'bg-gray-600'}">
									{row.platform}
								</span>
							</td>
							<td class="px-5 py-3 text-right text-gray-200">{fmt(row.subscribers)}</td>
							<td class="px-5 py-3 text-right text-gray-200">{fmt(row.likes)}</td>
							<td class="px-5 py-3 text-right text-gray-200">{fmt(row.shares)}</td>
							<td class="px-5 py-3 text-right text-gray-200">{fmt(row.comments)}</td>
							<td class="px-5 py-3 text-right text-gray-400 text-xs">{fmtDate(row.updated_at)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
