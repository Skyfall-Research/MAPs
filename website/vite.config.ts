import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		port: 3001
	},
	ssr: {
		// Exclude browser-only libraries and Node.js built-ins from SSR builds
		external: ['phaser', 'fs', 'path', 'url']
	},
	build: {
		// Disable source maps in production to prevent 404 errors for source files
		sourcemap: false
	}
	// optimizeDeps: {
	// 	exclude: ['phaser']
	// }
});
