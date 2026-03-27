<script lang="ts">
	import { onMount } from 'svelte';
	import { apiFetch } from '$lib/api';
	import { t } from '$lib/i18n';

	type Model = { id: string; name: string; provider: string };
	type Account = { id: string; name: string; platform: string };
	type PlanItem = { day?: number; title?: string; content: string; suggested_time?: string; platform?: string };

	let models: Model[] = [];
	let accounts: Account[] = [];
	let selectedModel = '';
	let topic = '';
	let platform = 'telegram';
	let tone = 'professional';
	let language = 'ru';
	let planDays = 7;

	// Publish controls
	let publishAccountId = '';
	let scheduledAt = '';

	let generatedPost = '';
	let contentPlan: PlanItem[] = [];
	let loadingPost = false;
	let loadingPlan = false;
	let savingPlan = false;
	let publishing = false;
	let error = '';
	let successMsg = '';

	const PLATFORMS = ['telegram', 'linkedin', 'vk'];
	$: TONES = [
		{ value: 'professional', label: $t('tone.professional') },
		{ value: 'casual',       label: $t('tone.casual') },
		{ value: 'funny',        label: $t('tone.funny') },
		{ value: 'motivational', label: $t('tone.motivational') },
		{ value: 'educational',  label: $t('tone.educational') },
	];

	onMount(async () => {
		try {
			const [mRes, aRes] = await Promise.all([
				apiFetch('/api/ai/models'),
				apiFetch('/api/accounts/'),
			]);
			if (mRes.ok) {
				models = await mRes.json();
				if (models.length > 0) selectedModel = models[0].id;
			}
			if (aRes.ok) accounts = await aRes.json();
		} catch {}
	});

	$: filteredAccounts = accounts.filter((a) => a.platform === platform);

	async function generatePost() {
		error = ''; successMsg = '';
		if (!topic.trim()) { error = $t('gen.enterTopic'); return; }
		loadingPost = true;
		try {
			const res = await apiFetch('/api/ai/generate-post', {
				method: 'POST',
				body: JSON.stringify({ topic, platform, tone, language, model: selectedModel })
			});
			const data = await res.json();
			if (!res.ok) { error = data.detail || 'Error'; return; }
			generatedPost = data.content || data.post || JSON.stringify(data);
		} catch (e: any) { error = e.message || 'Network error'; }
		finally { loadingPost = false; }
	}

	async function generatePlan() {
		error = ''; successMsg = '';
		if (!topic.trim()) { error = $t('gen.enterTopicPlan'); return; }
		loadingPlan = true;
		try {
			const res = await apiFetch('/api/ai/content-plan', {
				method: 'POST',
				body: JSON.stringify({ topic, platform, tone, language, model: selectedModel, days: planDays })
			});
			const data = await res.json();
			if (!res.ok) { error = data.detail || 'Error'; return; }
			contentPlan = Array.isArray(data.plan) ? data.plan : Array.isArray(data) ? data : [];
		} catch (e: any) { error = e.message || 'Network error'; }
		finally { loadingPlan = false; }
	}

	async function savePostAsDraft() {
		if (!generatedPost) return;
		try {
			const res = await apiFetch('/api/posts/', {
				method: 'POST',
				body: JSON.stringify({ content: generatedPost, platform, status: 'draft' })
			});
			if (res.ok) successMsg = $t('create.saved');
			else { const d = await res.json(); error = d.detail || 'Error'; }
		} catch (e: any) { error = e.message; }
	}

	async function schedulePost() {
		if (!generatedPost || !scheduledAt) return;
		try {
			publishing = true;
			const body: Record<string, any> = {
				content: generatedPost,
				platform,
				status: 'scheduled',
				scheduled_at: new Date(scheduledAt).toISOString(),
			};
			if (publishAccountId) body.account_id = publishAccountId;
			const res = await apiFetch('/api/posts/', { method: 'POST', body: JSON.stringify(body) });
			if (res.ok) { successMsg = $t('create.scheduled'); scheduledAt = ''; }
			else { const d = await res.json(); error = d.detail || 'Error'; }
		} catch (e: any) { error = e.message; }
		finally { publishing = false; }
	}

	async function publishNow() {
		if (!generatedPost) return;
		try {
			publishing = true;
			const body: Record<string, any> = { content: generatedPost, platform, status: 'published' };
			if (publishAccountId) body.account_id = publishAccountId;
			const res = await apiFetch('/api/posts/', { method: 'POST', body: JSON.stringify(body) });
			if (res.ok) { successMsg = $t('create.published'); }
			else { const d = await res.json(); error = d.detail || 'Error'; }
		} catch (e: any) { error = e.message; }
		finally { publishing = false; }
	}

	async function savePlanAsDrafts() {
		if (contentPlan.length === 0) return;
		savingPlan = true; error = ''; successMsg = '';
		let saved = 0;
		const today = new Date();
		for (const item of contentPlan) {
			try {
				const dayOffset = (item.day || 1) - 1;
				const postDate = new Date(today);
				postDate.setDate(today.getDate() + dayOffset);
				if (item.suggested_time) {
					const [h, m] = item.suggested_time.split(':').map(Number);
					if (!isNaN(h)) { postDate.setHours(h, m || 0, 0, 0); }
				} else {
					postDate.setHours(10, 0, 0, 0);
				}
				const content = item.title
					? `${item.title}\n\n${item.content}`
					: item.content;
				const body = {
					content,
					platform: item.platform || platform,
					status: 'scheduled',
					scheduled_at: postDate.toISOString(),
				};
				const res = await apiFetch('/api/posts/', { method: 'POST', body: JSON.stringify(body) });
				if (res.ok) saved++;
			} catch {}
		}
		savingPlan = false;
		successMsg = `${$t('gen.planSaved')} (${saved}/${contentPlan.length})`;
	}

	function usePlanItemAsTopic(item: PlanItem) {
		topic = item.title || item.content.slice(0, 80);
		generatedPost = '';
	}
</script>

<svelte:head><title>{$t('gen.title')} — VYUD Publisher</title></svelte:head>

<div class="max-w-screen-xl mx-auto px-4 py-8">
	<div class="mb-6">
		<h1 class="text-2xl font-bold text-gray-100">{$t('gen.title')}</h1>
		<p class="text-sm text-gray-400 mt-1">{$t('gen.subtitle')}</p>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<!-- Settings panel -->
		<div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-4 h-fit">

			<!-- Model -->
			<div>
				<label class="block text-sm text-gray-400 mb-1">{$t('gen.model')}</label>
				<select bind:value={selectedModel}
					class="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500">
					{#each models as m}
						<option value={m.id}>{m.name} ({m.provider})</option>
					{/each}
					{#if models.length === 0}<option value="">{$t('loading')}</option>{/if}
				</select>
			</div>

			<!-- Topic — textarea 5 rows (Issue 5) -->
			<div>
				<label class="block text-sm text-gray-400 mb-1">{$t('gen.topic')}</label>
				<textarea
					bind:value={topic}
					rows="5"
					placeholder={$t('gen.topicPlaceholder')}
					class="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500 resize-y"
				></textarea>
			</div>

			<!-- Platform -->
			<div>
				<label class="block text-sm text-gray-400 mb-1">{$t('gen.platform')}</label>
				<div class="flex gap-2">
					{#each PLATFORMS as p}
						<button on:click={() => platform = p}
							class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
								{platform === p ? 'bg-violet-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}"
						>{p}</button>
					{/each}
				</div>
			</div>

			<!-- Tone (Issue 6 — added educational) -->
			<div>
				<label class="block text-sm text-gray-400 mb-1">{$t('gen.tone')}</label>
				<select bind:value={tone}
					class="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500">
					{#each TONES as t_}
						<option value={t_.value}>{t_.label}</option>
					{/each}
				</select>
			</div>

			<!-- Language -->
			<div>
				<label class="block text-sm text-gray-400 mb-1">{$t('gen.contentLang')}</label>
				<select bind:value={language}
					class="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500">
					<option value="ru">Русский</option>
					<option value="en">English</option>
				</select>
			</div>

			{#if error}
				<div class="bg-red-900/40 border border-red-700 rounded-xl px-4 py-3 text-sm text-red-300">{error}</div>
			{/if}

			<div class="flex flex-col gap-2">
				<button on:click={generatePost} disabled={loadingPost}
					class="w-full bg-violet-600 hover:bg-violet-500 disabled:opacity-60 text-white font-semibold rounded-xl py-3 text-sm transition-colors">
					{loadingPost ? $t('gen.generating') : $t('gen.generatePost')}
				</button>
				<div class="flex items-center gap-2">
					<input type="number" bind:value={planDays} min="1" max="30"
						class="w-16 bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500"/>
					<button on:click={generatePlan} disabled={loadingPlan}
						class="flex-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-60 text-gray-100 font-semibold rounded-xl py-3 text-sm transition-colors">
						{loadingPlan ? $t('gen.planGenerating') : `${$t('gen.planBtn')} ${planDays} ${$t('gen.days')}`}
					</button>
				</div>
			</div>
		</div>

		<!-- Output panel -->
		<div class="flex flex-col gap-4">
			{#if successMsg}
				<div class="bg-green-900/40 border border-green-700 rounded-xl px-4 py-3 text-sm text-green-300">{successMsg}</div>
			{/if}

			<!-- Generated post + publish controls (Issue 3) -->
			{#if generatedPost}
				<div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-4">
					<h2 class="font-semibold text-gray-100">{$t('gen.result')}</h2>
					<textarea bind:value={generatedPost} rows="10"
						class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500 resize-y"
					></textarea>
					<p class="text-right text-xs text-gray-500 -mt-2">{generatedPost.length} {$t('chars')}</p>

					<!-- Account selector -->
					{#if filteredAccounts.length > 0}
						<div>
							<label class="block text-sm text-gray-400 mb-1">{$t('gen.account')}</label>
							<select bind:value={publishAccountId}
								class="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500">
								<option value="">{$t('selectAccount')}</option>
								{#each filteredAccounts as acc}
									<option value={acc.id}>{acc.name}</option>
								{/each}
							</select>
						</div>
					{/if}

					<!-- Schedule datetime -->
					<div>
						<label class="block text-sm text-gray-400 mb-1">{$t('gen.scheduledAt')}</label>
						<input type="datetime-local" bind:value={scheduledAt}
							class="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500"/>
					</div>

					<!-- Action buttons -->
					<div class="flex gap-2 flex-wrap">
						<button on:click={savePostAsDraft} disabled={publishing}
							class="flex-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-60 text-gray-100 font-semibold rounded-xl py-2.5 text-sm transition-colors">
							{$t('gen.draft')}
						</button>
						<button on:click={schedulePost} disabled={publishing || !scheduledAt}
							class="flex-1 bg-blue-700 hover:bg-blue-600 disabled:opacity-60 text-white font-semibold rounded-xl py-2.5 text-sm transition-colors">
							{$t('gen.schedule')}
						</button>
						<button on:click={publishNow} disabled={publishing || !publishAccountId}
							class="flex-1 bg-green-700 hover:bg-green-600 disabled:opacity-60 text-white font-semibold rounded-xl py-2.5 text-sm transition-colors">
							{publishing ? '...' : $t('gen.publishNow')}
						</button>
					</div>
				</div>
			{/if}

			<!-- Content plan + save (Issue 4) -->
			{#if contentPlan.length > 0}
				<div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
					<div class="flex items-center justify-between mb-4">
						<h2 class="font-semibold text-gray-100">{$t('gen.planTitle')} ({contentPlan.length})</h2>
						<button on:click={savePlanAsDrafts} disabled={savingPlan}
							class="text-xs bg-violet-600/20 text-violet-300 hover:bg-violet-600/40 disabled:opacity-60 px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap">
							{savingPlan ? '...' : $t('gen.savePlan')}
						</button>
					</div>
					<div class="flex flex-col gap-3 max-h-[500px] overflow-y-auto pr-1">
						{#each contentPlan as item, i}
							<div class="bg-gray-800 rounded-xl p-4">
								<div class="flex items-start justify-between gap-2 mb-2">
									<div class="flex items-center gap-2">
										<span class="text-xs font-medium text-violet-300">
											{item.day ? `День ${item.day}` : `#${i+1}`}
											{item.suggested_time ? `· ${item.suggested_time}` : ''}
										</span>
										{#if item.platform}
											<span class="text-xs text-gray-400">{item.platform}</span>
										{/if}
									</div>
									<button on:click={() => usePlanItemAsTopic(item)}
										class="text-xs text-blue-400 hover:text-blue-300 shrink-0 transition-colors">
										{$t('gen.useTopic')}
									</button>
								</div>
								{#if item.title}
									<p class="text-xs font-semibold text-gray-300 mb-1">{item.title}</p>
								{/if}
								<p class="text-sm text-gray-200 whitespace-pre-wrap">{item.content}</p>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			{#if !generatedPost && contentPlan.length === 0}
				<div class="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center">
					<p class="text-4xl mb-3">🤖</p>
					<p class="text-gray-400 text-sm">{$t('gen.empty')}</p>
				</div>
			{/if}
		</div>
	</div>
</div>
