<script lang="ts">
	import { onMount } from 'svelte';
	import { apiFetch } from '$lib/api';
	import { lang, t } from '$lib/i18n';

	type Post = {
		id: string;
		content: string;
		platform: string;
		status: string;
		scheduled_at: string | null;
		created_at: string;
	};

	let posts: Post[] = [];
	let loading = true;
	let error = '';

	let currentDate = new Date();
	let currentYear = currentDate.getFullYear();
	let currentMonth = currentDate.getMonth();

	const MONTHS_RU = [
		'Январь','Февраль','Март','Апрель','Май','Июнь',
		'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'
	];
	const MONTHS_EN = [
		'January','February','March','April','May','June',
		'July','August','September','October','November','December'
	];
	const MONTHS_RU_GENITIVE = [
		'января','февраля','марта','апреля','мая','июня',
		'июля','августа','сентября','октября','ноября','декабря'
	];
	const MONTHS_EN_SHORT = [
		'Jan','Feb','Mar','Apr','May','Jun',
		'Jul','Aug','Sep','Oct','Nov','Dec'
	];
	const DAYS_SHORT_RU = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
	const DAYS_SHORT_EN = ['Mo','Tu','We','Th','Fr','Sa','Su'];

	$: MONTHS = $lang === 'ru' ? MONTHS_RU : MONTHS_EN;
	$: DAYS_SHORT = $lang === 'ru' ? DAYS_SHORT_RU : DAYS_SHORT_EN;

	const PLATFORM_COLORS: Record<string, string> = {
		telegram: 'bg-blue-500',
		linkedin: 'bg-blue-700',
		vk: 'bg-blue-400',
	};
	const PLATFORM_LABELS: Record<string, string> = {
		telegram: 'TG',
		linkedin: 'in',
		vk: 'VK',
	};

	async function loadPosts() {
		loading = true;
		error = '';
		try {
			const res = await apiFetch('/api/posts/');
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			posts = await res.json();
		} catch (e: any) {
			error = e.message || $t('cal.errorLoad');
		} finally {
			loading = false;
		}
	}

	onMount(loadPosts);

	function getDaysInMonth(year: number, month: number) {
		return new Date(year, month + 1, 0).getDate();
	}

	function getFirstDayOfWeek(year: number, month: number) {
		// 0=Mon...6=Sun
		const d = new Date(year, month, 1).getDay();
		return d === 0 ? 6 : d - 1;
	}

	function getPostsForDay(day: number) {
		return posts.filter((p) => {
			const dt = p.scheduled_at || p.created_at;
			if (!dt) return false;
			const d = new Date(dt);
			return d.getFullYear() === currentYear && d.getMonth() === currentMonth && d.getDate() === day;
		});
	}

	$: calendarDays = (() => {
		const daysInMonth = getDaysInMonth(currentYear, currentMonth);
		const firstDay = getFirstDayOfWeek(currentYear, currentMonth);
		const days: (number | null)[] = Array(firstDay).fill(null);
		for (let i = 1; i <= daysInMonth; i++) days.push(i);
		while (days.length % 7 !== 0) days.push(null);
		return days;
	})();

	$: scheduledPosts = posts
		.filter((p) => {
			if (!p.scheduled_at) return false;
			return new Date(p.scheduled_at) >= new Date();
		})
		.sort((a, b) => new Date(a.scheduled_at!).getTime() - new Date(b.scheduled_at!).getTime())
		.slice(0, 10);

	$: totalPosts = posts.length;
	$: scheduledCount = scheduledPosts.length;

	function prevMonth() {
		if (currentMonth === 0) { currentYear--; currentMonth = 11; }
		else currentMonth--;
	}
	function nextMonth() {
		if (currentMonth === 11) { currentYear++; currentMonth = 0; }
		else currentMonth++;
	}

	function isToday(day: number) {
		const now = new Date();
		return now.getFullYear() === currentYear && now.getMonth() === currentMonth && now.getDate() === day;
	}

	function formatTime(dt: string) {
		const d = new Date(dt);
		return d.toLocaleTimeString($lang === 'ru' ? 'ru-RU' : 'en-US', { hour: '2-digit', minute: '2-digit' });
	}
	function formatDay(dt: string) {
		const d = new Date(dt);
		if ($lang === 'ru') {
			return `${d.getDate()} ${MONTHS_RU_GENITIVE[d.getMonth()]}, ${formatTime(dt)}`;
		}
		return `${MONTHS_EN_SHORT[d.getMonth()]} ${d.getDate()}, ${formatTime(dt)}`;
	}
</script>

<svelte:head>
	<title>{$t('nav.calendar')} — VYUD Publisher</title>
</svelte:head>

<div class="max-w-screen-2xl mx-auto px-4 py-6 flex gap-6 flex-col xl:flex-row">
	<!-- Calendar -->
	<div class="flex-1 bg-gray-900 border border-gray-800 rounded-2xl p-6">
		<!-- Header -->
		<div class="flex items-center justify-between mb-6">
			<h2 class="text-xl font-semibold capitalize">
				{MONTHS[currentMonth]} {currentYear}
			</h2>
			<div class="flex items-center gap-2">
				<button
					on:click={prevMonth}
					class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-800 transition-colors text-gray-400 hover:text-gray-100"
				>←</button>
				<button
					on:click={nextMonth}
					class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-800 transition-colors text-gray-400 hover:text-gray-100"
				>→</button>
			</div>
		</div>

		{#if loading}
			<div class="text-center py-16 text-gray-400">{$t('loading')}</div>
		{:else if error}
			<div class="text-center py-16 text-red-400">{error}</div>
		{:else}
			<!-- Day headers -->
			<div class="grid grid-cols-7 mb-2">
				{#each DAYS_SHORT as d}
					<div class="text-center text-xs text-gray-500 font-medium py-1">{d}</div>
				{/each}
			</div>

			<!-- Calendar grid -->
			<div class="grid grid-cols-7 gap-1">
				{#each calendarDays as day}
					<div
						class="min-h-[80px] rounded-xl p-1.5 transition-colors
							{day ? 'hover:bg-gray-800 cursor-pointer' : ''}
							{day && isToday(day) ? 'ring-2 ring-violet-500' : ''}"
					>
						{#if day}
							<div class="text-xs font-medium mb-1 {isToday(day) ? 'text-violet-300' : 'text-gray-400'}">
								{day}
							</div>
							{@const dayPosts = getPostsForDay(day)}
							<div class="flex flex-wrap gap-0.5">
								{#each dayPosts.slice(0, 4) as post}
									<span
										class="inline-flex items-center justify-center w-6 h-6 rounded text-xs font-bold text-white
											{PLATFORM_COLORS[post.platform] || 'bg-gray-600'}"
										title={post.content?.slice(0, 60)}
									>
										{PLATFORM_LABELS[post.platform] || '?'}
									</span>
								{/each}
								{#if dayPosts.length > 4}
									<span class="text-xs text-gray-400 self-center">+{dayPosts.length - 4}</span>
								{/if}
							</div>
						{/if}
					</div>
				{/each}
			</div>

			<div class="mt-4 text-xs text-gray-500">
				{$t('cal.total')}: {totalPosts} | {$t('cal.scheduledCount')}: {scheduledCount}
			</div>
		{/if}
	</div>

	<!-- Scheduled panel -->
	<div class="w-full xl:w-80 flex flex-col gap-4">
		<div class="bg-gray-900 border border-gray-800 rounded-2xl p-5">
			<div class="flex items-center justify-between mb-4">
				<h3 class="font-semibold text-gray-100">{$t('cal.scheduled')}</h3>
				<a
					href="/create"
					class="text-xs text-violet-400 hover:text-violet-300 font-medium transition-colors"
				>{$t('cal.add')}</a>
			</div>

			{#if loading}
				<p class="text-sm text-gray-400">{$t('loading')}</p>
			{:else if scheduledPosts.length === 0}
				<p class="text-sm text-gray-400">{$t('cal.noScheduled')}</p>
			{:else}
				<div class="flex flex-col gap-3">
					{#each scheduledPosts as post}
						<div class="flex flex-col gap-1">
							<div class="flex items-center gap-2">
								<span
									class="text-xs font-bold text-white px-1.5 py-0.5 rounded {PLATFORM_COLORS[post.platform] || 'bg-gray-600'}"
								>
									{post.platform}
								</span>
								<span class="text-xs text-gray-400">
									{post.scheduled_at ? formatDay(post.scheduled_at) : '—'}
								</span>
							</div>
							<p class="text-sm text-gray-200 line-clamp-2">{post.content}</p>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</div>
