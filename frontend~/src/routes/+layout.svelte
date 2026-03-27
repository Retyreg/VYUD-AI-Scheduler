<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { onMount } from 'svelte';
	import { isTokenExpired } from '$lib/api';
	import { lang, t } from '$lib/i18n';

	const PUBLIC_ROUTES = ['/login', '/register'];

	onMount(() => {
		if (browser) {
			const token = localStorage.getItem('access_token');
			const isPublic = PUBLIC_ROUTES.some((r) => $page.url.pathname.startsWith(r));
			if (!token || isTokenExpired(token)) {
				localStorage.removeItem('access_token');
				if (!isPublic) goto('/login');
			}
		}
	});

	function logout() {
		localStorage.removeItem('access_token');
		goto('/login');
	}

	function toggleLang() {
		lang.update((l) => (l === 'ru' ? 'en' : 'ru'));
	}

	$: isPublicPage = PUBLIC_ROUTES.some((r) => $page.url.pathname.startsWith(r));

	$: navItems = [
		{ href: '/', label: $t('nav.calendar'), icon: '📅' },
		{ href: '/create', label: $t('nav.create'), icon: '✏️' },
		{ href: '/generate', label: $t('nav.generate'), icon: '🤖' },
		{ href: '/settings', label: $t('nav.settings'), icon: '⚙️' },
		{ href: '/analytics', label: $t('nav.analytics'), icon: '📊' }
	];
</script>

{#if isPublicPage}
	<slot />
{:else}
	<div class="flex flex-col min-h-screen">
		<header class="border-b border-gray-800 bg-gray-900 sticky top-0 z-50">
			<div class="max-w-screen-2xl mx-auto px-4 h-14 flex items-center justify-between">
				<div class="flex items-center gap-6">
					<a href="/" class="flex items-center gap-2.5 shrink-0">
						<img src="/logo-mark.svg" alt="VYUD" class="w-8 h-8" />
						<span class="font-display font-bold text-lg tracking-tight leading-none">
							<span class="text-white">VYUD</span><span class="text-vyud-blue"> Publisher</span>
						</span>
					</a>
					<nav class="hidden md:flex items-center gap-1">
						{#each navItems as item}
							<a
								href={item.href}
								class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors
									{$page.url.pathname === item.href
									? 'bg-violet-600/20 text-violet-300'
									: 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'}"
							>
								<span>{item.icon}</span>
								<span>{item.label}</span>
							</a>
						{/each}
					</nav>
				</div>
				<div class="flex items-center gap-2">
					<button
						on:click={toggleLang}
						class="text-xs font-semibold px-2.5 py-1 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-gray-100 transition-colors border border-gray-700"
						title="Switch language"
					>
						{$lang === 'ru' ? 'EN' : 'RU'}
					</button>
					<button
						on:click={logout}
						class="text-sm text-gray-400 hover:text-gray-100 transition-colors px-3 py-1.5 rounded-md hover:bg-gray-800"
					>
						{$t('nav.logout')}
					</button>
				</div>
			</div>
			<!-- Mobile nav -->
			<div class="md:hidden flex items-center gap-1 px-4 pb-2 overflow-x-auto">
				{#each navItems as item}
					<a
						href={item.href}
						class="flex items-center gap-1 px-3 py-1.5 rounded-md text-xs whitespace-nowrap transition-colors
							{$page.url.pathname === item.href
							? 'bg-violet-600/20 text-violet-300'
							: 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'}"
					>
						<span>{item.icon}</span>
						<span>{item.label}</span>
					</a>
				{/each}
			</div>
		</header>

		<main class="flex-1">
			<slot />
		</main>
	</div>
{/if}
