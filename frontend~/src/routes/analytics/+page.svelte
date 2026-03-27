<script lang="ts">
	import { onMount } from 'svelte';

	type AnalyticsItem = {
		id: string;
		post_id: string;
		platform: string;
		views: number;
		likes: number;
		shares: number;
		comments: number;
		fetched_at: string;
		post_content?: string;
	};

	let analytics: AnalyticsItem[] = [];
	let loading = true;
	let error = '';

	function authHeaders() {
		const token = localStorage.getItem('access_token');
		return { Authorization: `Bearer ${token || ''}` };
	}

	onMount(async () => {
		loading = true;
		try {
			const res = await fetch('/api/analytics/', { headers: authHeaders() });
			if (res.ok) analytics = await res.json();
			else { const d = await res.json(); error = d.detail || 'Ошибка загрузки'; }
		} catch (e: any) { error = e.message; }
		finally { loading = false; }
	});

	function fmt(n: number | null | undefined) {
		if (n == null) return '—';
		if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
		return String(n);
	}

	const PLATFORM_COLORS: Record<string, string> = {
		telegram: 'bg-blue-500', linkedin: 'bg-blue-700', vk: 'bg-blue-400'
	};

	$: totalViews = analytics.reduce((s, a) => s + (a.views || 0), 0);
	$: totalLikes = analytics.reduce((s, a) => s + (a.likes || 0), 0);
	$: totalShares = analytics.reduce((s, a) => s + (a.shares || 0), 0);
</script>

<svelte:head>
	<title>Аналитика — VYUD Publisher</title>
</svelte:head>

<div class="max-w-screen-xl mx-auto px-4 py-8">
	<div class="mb-6">
		<h1 class="text-2xl font-bold text-gray-100">Аналитика</h1>
		<p class="text-sm text-gray-400 mt-1">Статистика по опубликованным постам</p>
	</div>

	{#if error}
		<div class="bg-red-900/40 border border-red-700 rounded-xl px-4 py-3 text-sm text-red-300 mb-6">{error}</div>
	{/if}

	<!-- Summary cards -->
	<div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
		{#each [['👁 Просмотры', fmt(totalViews)], ['❤️ Лайки', fmt(totalLikes)], ['🔁 Репосты', fmt(totalShares)]] as [label, val]}
			<div class="bg-gray-900 border border-gray-800 rounded-2xl p-5 text-center">
				<p class="text-3xl font-bold text-gray-100">{val}</p>
				<p class="text-sm text-gray-400 mt-1">{label}</p>
			</div>
		{/each}
	</div>

	{#if loading}
		<div class="text-center py-16 text-gray-400">Загрузка...</div>
	{:else if analytics.length === 0}
		<div class="text-center py-16">
			<p class="text-4xl mb-3">📊</p>
			<p class="text-gray-400">Нет данных аналитики. Опубликуйте посты для отображения статистики.</p>
		</div>
	{:else}
		<div class="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
			<table class="w-full text-sm">
				<thead>
					<tr class="border-b border-gray-800 text-gray-400 text-xs">
						<th class="text-left px-5 py-3 font-medium">Пост</th>
						<th class="text-left px-5 py-3 font-medium">Платформа</th>
						<th class="text-right px-5 py-3 font-medium">Просмотры</th>
						<th class="text-right px-5 py-3 font-medium">Лайки</th>
						<th class="text-right px-5 py-3 font-medium">Репосты</th>
						<th class="text-right px-5 py-3 font-medium">Комменты</th>
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
							<td class="px-5 py-3 text-right text-gray-200">{fmt(row.views)}</td>
							<td class="px-5 py-3 text-right text-gray-200">{fmt(row.likes)}</td>
							<td class="px-5 py-3 text-right text-gray-200">{fmt(row.shares)}</td>
							<td class="px-5 py-3 text-right text-gray-200">{fmt(row.comments)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
