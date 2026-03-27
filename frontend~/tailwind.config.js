/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				vyud: {
					blue:        '#0D7EFF',
					'blue-dark': '#0066D6',
					dark:        '#070E18',
					darker:      '#0D1926',
				}
			},
			fontFamily: {
				display: ['Syne', 'sans-serif'],
				sans:    ['DM Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
				mono:    ['JetBrains Mono', 'ui-monospace', 'monospace'],
			}
		}
	},
	plugins: []
};
