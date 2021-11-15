/** @type {import('@sveltejs/kit').Config} */
import adapter from '@sveltejs/adapter-static';
const dev = process.env.NODE_ENV === 'development';
const config = {
	kit: {
		paths: {
			base: dev ? '' : '/dsite'
		},
		appDir: 'internal',
		adapter: adapter({
			// default options are shown
			pages: 'build',
			assets: 'build',
			fallback: null
		}),
		// hydrate the <div id="svelte"> element in src/app.html
		target: '#svelte'
	}
};

export default config;
