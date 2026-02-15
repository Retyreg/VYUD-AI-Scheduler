<script>
    import { onMount } from 'svelte';
    
    let posts = [];
    let analytics = [];
    let loading = true;
    let refreshing = {};
    let error = null;
    let summary = null;
    
    const API_URL = '/api';
    
    function getToken() {
        const token = localStorage.getItem('access_token');
        if (token) {
            return token;
            
        }
        return null;
    }
    
    async function fetchPosts() {
        const token = getToken();
        if (!token) {
            error = 'Необходима авторизация';
            loading = false;
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/posts/?status=published`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
                posts = await response.json();
            } else {
                error = 'Ошибка загрузки постов';
            }
        } catch (e) {
            error = e.message;
        }
    }
    
    async function fetchAnalytics() {
        const token = getToken();
        if (!token) return;
        
        try {
            const response = await fetch(`${API_URL}/analytics/all`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) analytics = await response.json();
        } catch (e) {
            console.error('Failed to fetch analytics:', e);
        }
    }
    
    async function fetchSummary() {
        const token = getToken();
        if (!token) return;
        
        try {
            const response = await fetch(`${API_URL}/analytics/summary`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) summary = await response.json();
        } catch (e) {
            console.error('Failed to fetch summary:', e);
        }
    }
    
    async function refreshPostAnalytics(postId, platform) {
        const token = getToken();
        if (!token) return;
        
        const key = `${postId}-${platform}`;
        refreshing[key] = true;
        refreshing = refreshing;
        
        try {
            const response = await fetch(`${API_URL}/analytics/refresh`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ post_id: postId, platform })
            });
            
            if (response.ok) {
                const result = await response.json();
                const idx = analytics.findIndex(a => a.post_id === postId && a.platform === platform);
                if (idx >= 0) {
                    analytics[idx] = { ...analytics[idx], views: result.views, clicks: result.clicks, collected_at: new Date().toISOString() };
                } else {
                    analytics = [result, ...analytics];
                }
                analytics = analytics;
                await fetchSummary();
                if (result.error) alert(`Предупреждение: ${result.error}`);
            } else {
                const err = await response.json();
                alert(`Ошибка: ${err.detail || 'Unknown error'}`);
            }
        } catch (e) {
            alert(`Ошибка: ${e.message}`);
        } finally {
            refreshing[key] = false;
            refreshing = refreshing;
        }
    }
    
    function getAnalyticsForPost(postId, platform) {
        return analytics.find(a => a.post_id === postId && a.platform === platform);
    }
    
    function formatDate(dateStr) {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString('ru-RU', {
            day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
        });
    }
    
    function formatNumber(num) {
        if (num === null || num === undefined) return '-';
        return num.toLocaleString('ru-RU');
    }
    
    function getPlatformIcon(platform) {
        return { telegram: '📱', linkedin: '💼', vk: '🔵' }[platform] || '📝';
    }
    
    function getPlatformName(platform) {
        return { telegram: 'Telegram', linkedin: 'LinkedIn', vk: 'VK' }[platform] || platform;
    }
    
    onMount(async () => {
        await fetchPosts();
        await fetchAnalytics();
        await fetchSummary();
        loading = false;
    });
</script>

<svelte:head>
    <title>Аналитика | VYUD Publisher</title>
</svelte:head>

<div class="min-h-screen bg-gray-900 text-white p-6">
    <div class="max-w-7xl mx-auto">
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-purple-400">📊 Аналитика постов</h1>
            <p class="text-gray-400 mt-2">Отслеживайте эффективность публикаций</p>
        </div>
        
        {#if error}
            <div class="bg-red-900/50 border border-red-500 text-red-300 px-4 py-3 rounded mb-6">{error}</div>
        {/if}
        
        {#if loading}
            <div class="flex items-center justify-center h-64">
                <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
            </div>
        {:else}
            {#if summary}
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                        <div class="text-gray-400 text-sm">Всего постов</div>
                        <div class="text-2xl font-bold text-white">{summary.total_posts}</div>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                        <div class="text-gray-400 text-sm">Общий охват</div>
                        <div class="text-2xl font-bold text-purple-400">{formatNumber(summary.total_views)}</div>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                        <div class="text-gray-400 text-sm">Всего кликов</div>
                        <div class="text-2xl font-bold text-green-400">{formatNumber(summary.total_clicks)}</div>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                        <div class="text-gray-400 text-sm">CTR</div>
                        <div class="text-2xl font-bold text-blue-400">
                            {summary.total_views > 0 ? ((summary.total_clicks / summary.total_views) * 100).toFixed(2) + '%' : '-'}
                        </div>
                    </div>
                </div>
            {/if}
            
            <div class="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                <div class="p-4 border-b border-gray-700">
                    <h2 class="text-xl font-semibold">Опубликованные посты</h2>
                </div>
                
                {#if posts.length === 0}
                    <div class="p-8 text-center text-gray-400">
                        <p>Нет опубликованных постов</p>
                        <a href="/create" class="text-purple-400 hover:text-purple-300 mt-2 inline-block">Создать первый пост →</a>
                    </div>
                {:else}
                    <div class="overflow-x-auto">
                        <table class="w-full">
                            <thead class="bg-gray-900">
                                <tr>
                                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-400">Пост</th>
                                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-400">Платформа</th>
                                    <th class="px-4 py-3 text-right text-sm font-medium text-gray-400">Охват</th>
                                    <th class="px-4 py-3 text-right text-sm font-medium text-gray-400">Клики</th>
                                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-400">Обновлено</th>
                                    <th class="px-4 py-3 text-center text-sm font-medium text-gray-400">Действия</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-700">
                                {#each posts as post}
                                    {@const postAnalytics = getAnalyticsForPost(post.id, post.platform)}
                                    {@const refreshKey = `${post.id}-${post.platform}`}
                                    <tr class="hover:bg-gray-700/50 transition-colors">
                                        <td class="px-4 py-3">
                                            <div class="max-w-xs">
                                                <div class="font-medium truncate">{post.title || post.content?.substring(0, 50) + '...' || 'Без заголовка'}</div>
                                                <div class="text-sm text-gray-400">{formatDate(post.scheduled_time)}</div>
                                            </div>
                                        </td>
                                        <td class="px-4 py-3">
                                            <span class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-sm bg-gray-700">
                                                {getPlatformIcon(post.platform)} {getPlatformName(post.platform)}
                                            </span>
                                        </td>
                                        <td class="px-4 py-3 text-right">
                                            <span class="text-purple-400 font-semibold">{formatNumber(postAnalytics?.views)}</span>
                                        </td>
                                        <td class="px-4 py-3 text-right">
                                            <span class="text-green-400 font-semibold">{formatNumber(postAnalytics?.clicks)}</span>
                                        </td>
                                        <td class="px-4 py-3 text-sm text-gray-400">
                                            {postAnalytics ? formatDate(postAnalytics.collected_at) : 'Нет данных'}
                                        </td>
                                        <td class="px-4 py-3 text-center">
                                            <button
                                                on:click={() => refreshPostAnalytics(post.id, post.platform)}
                                                disabled={refreshing[refreshKey]}
                                                class="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-sm transition-colors inline-flex items-center gap-1"
                                            >
                                                {#if refreshing[refreshKey]}
                                                    <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
                                                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                                                    </svg>
                                                {:else}
                                                    🔄
                                                {/if}
                                                Обновить
                                            </button>
                                        </td>
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
                    </div>
                {/if}
            </div>
            
            <div class="mt-6 p-4 bg-gray-800/50 border border-gray-700 rounded-lg">
                <h3 class="font-medium text-yellow-400 mb-2">💡 Для Telegram аналитики</h3>
                <p class="text-sm text-gray-400">
                    Telegram Bot API не предоставляет статистику просмотров. Добавьте <code class="bg-gray-700 px-1 rounded">TGSTAT_TOKEN</code> в .env.
                </p>
            </div>
        {/if}
    </div>
</div>
