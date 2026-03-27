<script lang="ts">
	import { onMount } from 'svelte';
	import { apiFetch } from '$lib/api';
	import { t } from '$lib/i18n';

	type Account = { id: string; name: string; platform: string; created_at: string };

	let accounts: Account[] = [];
	let loading = true;
	let error = '';
	let success = '';

	// Form states
	let tgName = ''; let tgToken = ''; let tgChatId = '';
	let liName = ''; let liToken = ''; let liProfileId = '';
	let vkName = ''; let vkToken = ''; let vkGroupId = '';

	let submitting = false;

	async function loadAccounts() {
		loading = true;
		error = '';
		try {
			const res = await apiFetch('/api/accounts/');
			if (res.ok) accounts = await res.json();
			else { const d = await res.json(); error = d.detail || 'Error'; }
		} catch (e: any) { error = e.message; }
		finally { loading = false; }
	}

	onMount(loadAccounts);

	async function addTelegram() {
		if (!tgName || !tgToken || !tgChatId) { error = 'Fill all Telegram fields'; return; }
		submitting = true; error = ''; success = '';
		try {
			const res = await apiFetch('/api/accounts/telegram', {
				method: 'POST',
				body: JSON.stringify({ name: tgName, bot_token: tgToken, channel_id: tgChatId })
			});
			const d = await res.json();
			if (!res.ok) { error = d.detail || 'Error'; return; }
			success = 'Telegram ' + $t('set.connect') + '!';
			tgName = ''; tgToken = ''; tgChatId = '';
			await loadAccounts();
		} catch (e: any) { error = e.message; }
		finally { submitting = false; }
	}

	async function addLinkedIn() {
		if (!liName || !liToken || !liProfileId) { error = 'Fill all LinkedIn fields'; return; }
		submitting = true; error = ''; success = '';
		try {
			const res = await apiFetch('/api/accounts/linkedin', {
				method: 'POST',
				body: JSON.stringify({ name: liName, access_token: liToken, profile_id: liProfileId })
			});
			const d = await res.json();
			if (!res.ok) { error = d.detail || 'Error'; return; }
			success = 'LinkedIn ' + $t('set.connect') + '!';
			liName = ''; liToken = ''; liProfileId = '';
			await loadAccounts();
		} catch (e: any) { error = e.message; }
		finally { submitting = false; }
	}

	async function addVK() {
		if (!vkName || !vkToken) { error = 'Fill VK fields'; return; }
		submitting = true; error = ''; success = '';
		try {
			const res = await apiFetch('/api/accounts/vk', {
				method: 'POST',
				body: JSON.stringify({ name: vkName, access_token: vkToken, group_id: vkGroupId || null })
			});
			const d = await res.json();
			if (!res.ok) { error = d.detail || 'Error'; return; }
			success = 'VK ' + $t('set.connect') + '!';
			vkName = ''; vkToken = ''; vkGroupId = '';
			await loadAccounts();
		} catch (e: any) { error = e.message; }
		finally { submitting = false; }
	}

	const PLATFORM_COLORS: Record<string, string> = {
		telegram: 'bg-blue-500', linkedin: 'bg-blue-700', vk: 'bg-blue-400'
	};

	let activeTab = 'accounts';
</script>

<svelte:head>
	<title>{$t('set.title')} — VYUD Publisher</title>
</svelte:head>

<div class="max-w-screen-xl mx-auto px-4 py-8">
	<div class="mb-6">
		<h1 class="text-2xl font-bold text-gray-100">{$t('set.title')}</h1>
		<p class="text-sm text-gray-400 mt-1">{$t('set.subtitle')}</p>
	</div>

	<!-- Tabs -->
	<div class="flex gap-2 mb-6 border-b border-gray-800">
		{#each [['accounts', $t('set.accounts')], ['add', $t('set.addAccount')]] as [tab, label]}
			<button
				on:click={() => activeTab = tab}
				class="pb-3 px-4 text-sm font-medium border-b-2 transition-colors
					{activeTab === tab ? 'border-violet-500 text-violet-300' : 'border-transparent text-gray-400 hover:text-gray-100'}"
			>{label}</button>
		{/each}
	</div>

	{#if error}
		<div class="bg-red-900/40 border border-red-700 rounded-xl px-4 py-3 text-sm text-red-300 mb-4">{error}</div>
	{/if}
	{#if success}
		<div class="bg-green-900/40 border border-green-700 rounded-xl px-4 py-3 text-sm text-green-300 mb-4">{success}</div>
	{/if}

	{#if activeTab === 'accounts'}
		{#if loading}
			<p class="text-gray-400">{$t('loading')}</p>
		{:else if accounts.length === 0}
			<div class="text-center py-16">
				<p class="text-4xl mb-3">📭</p>
				<p class="text-gray-400 mb-4">{$t('set.noAccounts')}</p>
				<button on:click={() => activeTab = 'add'} class="text-violet-400 hover:text-violet-300 text-sm">{$t('set.addFirst')}</button>
			</div>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each accounts as acc}
					<div class="bg-gray-900 border border-gray-800 rounded-2xl p-5">
						<div class="flex items-center gap-3 mb-2">
							<span class="w-8 h-8 rounded-full {PLATFORM_COLORS[acc.platform] || 'bg-gray-600'} flex items-center justify-center text-xs text-white font-bold">
								{acc.platform[0].toUpperCase()}
							</span>
							<div>
								<p class="font-medium text-gray-100 text-sm">{acc.name}</p>
								<p class="text-xs text-gray-400 capitalize">{acc.platform}</p>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{:else}
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
			<!-- Telegram -->
			<div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
				<h3 class="font-semibold text-blue-400 mb-4">📱 Telegram</h3>
				<div class="flex flex-col gap-3">
					<input bind:value={tgName} placeholder="{$t('set.name')} (e.g. My channel)" class="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-blue-500 w-full" />
					<input bind:value={tgToken} placeholder="Bot Token (@BotFather)" class="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-blue-500 w-full font-mono text-xs" />
					<input bind:value={tgChatId} placeholder="Channel ID (e.g. -100123456)" class="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-blue-500 w-full" />
					<button on:click={addTelegram} disabled={submitting} class="bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-semibold rounded-xl py-2.5 text-sm transition-colors">
						{$t('set.connect')} Telegram
					</button>
				</div>
			</div>

			<!-- LinkedIn -->
			<div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
				<h3 class="font-semibold text-blue-300 mb-4">💼 LinkedIn</h3>
				<div class="flex flex-col gap-3">
					<input bind:value={liName} placeholder={$t('set.name')} class="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-blue-500 w-full" />
					<input bind:value={liToken} placeholder="Access Token" class="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-blue-500 w-full font-mono text-xs" />
					<input bind:value={liProfileId} placeholder="Profile / Org ID" class="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-blue-500 w-full" />
					<button on:click={addLinkedIn} disabled={submitting} class="bg-blue-700 hover:bg-blue-600 disabled:opacity-60 text-white font-semibold rounded-xl py-2.5 text-sm transition-colors">
						{$t('set.connect')} LinkedIn
					</button>
				</div>
			</div>

			<!-- VK -->
			<div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
				<h3 class="font-semibold text-blue-200 mb-4">🔵 VK</h3>
				<div class="flex flex-col gap-3">
					<input bind:value={vkName} placeholder={$t('set.name')} class="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-blue-500 w-full" />
					<input bind:value={vkToken} placeholder="Access Token" class="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-blue-500 w-full font-mono text-xs" />
					<input bind:value={vkGroupId} placeholder="Group ID (optional)" class="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-blue-500 w-full" />
					<button on:click={addVK} disabled={submitting} class="bg-blue-500 hover:bg-blue-400 disabled:opacity-60 text-white font-semibold rounded-xl py-2.5 text-sm transition-colors">
						{$t('set.connect')} VK
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>
