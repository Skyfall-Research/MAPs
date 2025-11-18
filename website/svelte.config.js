import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors

	preprocess: vitePreprocess(),
	extensions: ['.svelte'],

	kit: {
		// Using adapter-node for Docker deployment
		// This creates a standalone Node.js server in ./build
		adapter: adapter({
			// Externalize Phaser - it's browser-only and shouldn't be in server bundle
			external: ['phaser']
		})
	}
};

export default config;
