<script lang="ts">
	import { onMount } from 'svelte';

	type Model = { id: string; name: string; provider: string };
	type ContentPlanItem = { topic: string; platform: string; content: string };

	let models: Model[] = [];
	let selectedModel = '';
	let topic = '';
	let platform = 'telegram';
	let tone = 'professional';
	let language = 'ru';
	let planDays = 7;

	let generatedPost = '';
	let contentPlan: ContentPlanItem[] = [];
	let loadingPost = false;
	let loadingPlan = false;
	let error = '';
	let successMsg = '';

	const PLATFORMS = ['telegram', 'linkedin', 'vk'];
	const TONES = [
		{ value: 'professional', label: 'Профессиональный' },
		{ value: 'casual', label: 'Разговорный' },
		{ value: 'funny', label: 'Юмористический' },
		{ value: 'motivational', label: 'Мотивационный' }
	];

	function authHeaders(): Record<string, string> {
		const token = localStorage.getItem('access_token');
		const h: Record<string, string> = { 'Content-Type': 'application/json' };
		if (token) h['Authorization'] = `Bearer ${token}`;
		return h;
	}

	onMount(async () => {
		try {
			const res = await fetch('/api/ai/models', { headers: authHeaders() });
			if (res.ok) {
				models = await res.json();
				if (models.length > 0) selectedModel = models[0].id;
			}
		} catch {}
	});

	async function generatePost() {
		error = '';
		successMsg = '';
		if (!topic.trim()) { error = 'Введите тему поста'; return; }
		loadingPost = true;
		try {
			const res = await fetch('/api/ai/generate-post', {
				method: 'POST',
				headers: authHeaders(),
				body: JSON.stringify({ topic, platform, tone, language, model: selectedModel })
			});
			const data = await res.json();
			if (!res.ok) { error = data.detail || 'Ошибка генерации'; return; }
			generatedPost = data.content || data.post || JSON.stringify(data);
		} catch (e: any) {
			error = e.message || 'Ошибка сети';
		} finally {
			loadingPost = false;
		}
	}

	async function generatePlan() {
		error = '';
		successMsg = '';
		if (!topic.trim()) { error = 'Введите тему для контент-плана'; return; }
		loadingPlan = true;
		try {
			const res = await fetch('/api/ai/content-plan', {
				method: 'POST',
				headers: authHeaders(),
				body: JSON.stringify({ topic, platform, tone, language, model: selectedModel, days: planDays })
			});
			const data = await res.json();
			if (!res.ok) { error = data.detail || 'Ошибка генерации плана'; return; }
			contentPlan = data.plan || data.items || data;
		} catch (e: any) {
			error = e.message || 'Ошибка сети';
		} finally {
			loadingPlan = false;
		}
	}

	async function savePostAsDraft() {
		if (!generatedPost) return;
		try {
			const token = localStorage.getItem('access_token');
			const res = await fetch('/api/posts/', {
				method: 'POST',
				headers: { Authorization: `Bearer ${token || ''}`, 'Content-Type': 'application/json' },
				body: JSON.stringify({ content: generatedPost, platform, status: 'draft' })
			});
			if (res.ok) { successMsg = 'Пост сохранён как черновик!'; }
			else { const d = await res.json(); error = d.detail || 'Ошибка сохранения'; }
		} catch (e: any) { error = e.message; }
	}
</script>

<svelte:head>
	<title>AI Генерация — VYUD Publisher</title>
</svelte:head>

<div class="max-w-screen-xl mx-auto px-4 py-8">
	<div class="mb-6">
		<h1 class="text-2xl font-bold text-gray-100">AI Генерация</h1>
		<p class="text-sm text-gray-400 mt-1">Генерируйте посты и контент-планы с помощью 11 языковых моделей</p>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<!-- Settings panel -->
		<div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-4 h-fit">
			<h2 class="font-semibold text-gray-100">Параметры</h2>

			<!-- Model -->
			<div>
				<label class="block text-sm text-gray-400 mb-1">Модель AI</label>
				<select
					bind:value={selectedModel}
					class="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500"
				>
					{#each models as m}
						<option value={m.id}>{m.name} ({m.provider})</option>
					{/each}
					{#if models.length === 0}
						<option value="">Загрузка моделей...</option>
					{/if}
				</select>
			</div>

			<!-- Topic -->
			<div>
				<label class="block text-sm text-gray-400 mb-1">Тема / идея</label>
				<input
					type="text"
					bind:value={topic}
					placeholder="Например: пятница 13-е, AI в маркетинге..."
					class="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500"
				/>
			</div>

			<!-- Platform -->
			<div>
				<label class="block text-sm text-gray-400 mb-1">Платформа</label>
				<div class="flex gap-2">
					{#each PLATFORMS as p}
						<button
							on:click={() => platform = p}
							class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
								{platform === p ? 'bg-violet-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}"
						>{p}</button>
					{/each}
				</div>
			</div>

			<!-- Tone -->
			<div>
				<label class="block text-sm text-gray-400 mb-1">Тон</label>
				<select
					bind:value={tone}
					class="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500"
				>
					{#each TONES as t}
						<option value={t.value}>{t.label}</option>
					{/each}
				</select>
			</div>

			<!-- Language -->
			<div>
				<label class="block text-sm text-gray-400 mb-1">Язык</label>
				<select
					bind:value={language}
					class="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500"
				>
					<option value="ru">Русский</option>
					<option value="en">English</option>
				</select>
			</div>

			{#if error}
				<div class="bg-red-900/40 border border-red-700 rounded-xl px-4 py-3 text-sm text-red-300">{error}</div>
			{/if}

			<div class="flex flex-col gap-2">
				<button
					on:click={generatePost}
					disabled={loadingPost}
					class="w-full bg-violet-600 hover:bg-violet-500 disabled:opacity-60 text-white font-semibold rounded-xl py-3 text-sm transition-colors"
				>
					{loadingPost ? '⏳ Генерация поста...' : '✨ Сгенерировать пост'}
				</button>

				<div class="flex items-center gap-2">
					<input
						type="number"
						bind:value={planDays}
						min="1" max="30"
						class="w-16 bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500"
					/>
					<button
						on:click={generatePlan}
						disabled={loadingPlan}
						class="flex-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-60 text-gray-100 font-semibold rounded-xl py-3 text-sm transition-colors"
					>
						{loadingPlan ? '⏳ Генерация плана...' : `📋 Контент-план на ${planDays} дн.`}
					</button>
				</div>
			</div>
		</div>

		<!-- Output panel -->
		<div class="flex flex-col gap-4">
			{#if successMsg}
				<div class="bg-green-900/40 border border-green-700 rounded-xl px-4 py-3 text-sm text-green-300">{successMsg}</div>
			{/if}

			{#if generatedPost}
				<div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
					<div class="flex items-center justify-between mb-3">
						<h2 class="font-semibold text-gray-100">Сгенерированный пост</h2>
						<button
							on:click={savePostAsDraft}
							class="text-xs bg-violet-600/20 text-violet-300 hover:bg-violet-600/40 px-3 py-1.5 rounded-lg transition-colors"
						>Сохранить черновик</button>
					</div>
					<textarea
						bind:value={generatedPost}
						rows="12"
						class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-100 outline-none focus:ring-2 focus:ring-violet-500 resize-y"
					></textarea>
					<p class="text-right text-xs text-gray-500 mt-1">{generatedPost.length} символов</p>
				</div>
			{/if}

			{#if contentPlan.length > 0}
				<div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
					<h2 class="font-semibold text-gray-100 mb-4">Контент-план ({contentPlan.length} постов)</h2>
					<div class="flex flex-col gap-3 max-h-96 overflow-y-auto pr-1">
						{#each contentPlan as item, i}
							<div class="bg-gray-800 rounded-xl p-4">
								<div class="flex items-center justify-between mb-2">
									<span class="text-xs font-medium text-violet-300">День {i + 1} · {item.platform}</span>
									{#if item.topic}
										<span class="text-xs text-gray-400">{item.topic}</span>
									{/if}
								</div>
								<p class="text-sm text-gray-200 whitespace-pre-wrap line-clamp-3">{item.content}</p>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			{#if !generatedPost && contentPlan.length === 0}
				<div class="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center">
					<p class="text-4xl mb-3">🤖</p>
					<p class="text-gray-400 text-sm">Введите тему и нажмите кнопку генерации</p>
				</div>
			{/if}
		</div>
	</div>
</div>
