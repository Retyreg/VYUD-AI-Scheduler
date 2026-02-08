<script>
  import '../app.css';
  import { page } from '$app/stores';
</script>

<div class="min-h-screen bg-gray-900 text-white">
  <!-- Header -->
  <header class="border-b border-gray-800 px-6 py-4">
    <div class="max-w-6xl mx-auto flex justify-between items-center">
      <a href="/" class="text-xl font-bold text-purple-400">VYUD Publisher</a>
      <nav class="flex gap-2">
        <a 
          href="/" 
          class="px-4 py-2 rounded-lg transition {$page.url.pathname === '/' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'}"
        >
          Календарь
        </a>
        <a 
          href="/create" 
          class="px-4 py-2 rounded-lg transition {$page.url.pathname === '/create' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'}"
        >
          Создать пост
        </a>
        <a 
          href="/generate" 
          class="px-4 py-2 rounded-lg transition {$page.url.pathname === '/generate' ? 'bg-purple-600 text-white' : 'text-purple-400 hover:text-purple-300'}"
        >
          ✨ AI
        </a>
        <a 
          href="/settings" 
          class="px-4 py-2 rounded-lg transition {$page.url.pathname === '/settings' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'}"
        >
          Настройки
        </a>
      </nav>
    </div>
  </header>
  
  <!-- Main -->
  <main class="p-6">
    <slot />
  </main>
</div>
