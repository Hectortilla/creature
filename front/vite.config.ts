import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';

export default defineConfig({
	plugins: [
		sveltekit(),
		viteStaticCopy({
			targets: [
				{
					src: 'src/babylon-editor/public/scene/*',
					dest: 'scene'
				}
			]
		})
	],
	esbuild: {
		// Enable TypeScript decorators support
		tsconfigRaw: {
			compilerOptions: {
				experimentalDecorators: true
			}
		}
	},
	optimizeDeps: {
		exclude: ['@babylonjs/havok']
	}
});
