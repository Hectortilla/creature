import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';

export default defineConfig({
	cacheDir: 'node_modules/.vite-babylon',
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
	ssr: {
		noExternal: ['babylonjs-editor-tools']
	},
	optimizeDeps: {
		exclude: ['@babylonjs/havok'],
		include: [
			'@babylonjs/core',
			'@babylonjs/core/Animations/animation',
			'@babylonjs/core/Animations/animationEvent',
			'@babylonjs/core/Animations/animationGroup',
			'@babylonjs/core/Debug/debugLayer',
			'@babylonjs/core/Engines/constants',
			'@babylonjs/core/Engines/engine',
			'@babylonjs/core/Loading/Plugins/babylonFileParser.function',
			'@babylonjs/core/Loading/sceneLoader',
			'@babylonjs/core/Loading/sceneLoaderFlags',
			'@babylonjs/core/Materials/material',
			'@babylonjs/core/Materials/Textures/colorGradingTexture',
			'@babylonjs/core/Materials/Textures/renderTargetTexture',
			'@babylonjs/core/Materials/Textures/texture',
			'@babylonjs/core/Maths/math.axis',
			'@babylonjs/core/Maths/math.color',
			'@babylonjs/core/Maths/math.vector',
			'@babylonjs/core/Meshes/mesh',
			'@babylonjs/core/Misc/decorators.serialization',
			'@babylonjs/core/Misc/observable',
			'@babylonjs/core/Misc/tools',
			'@babylonjs/core/Misc/webRequest',
			'@babylonjs/core/Particles/Node/nodeParticleSystemSet',
			'@babylonjs/core/Physics/v2/Plugins/havokPlugin',
			'@babylonjs/core/Physics/v2/physicsAggregate',
			'@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/defaultRenderingPipeline',
			'@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/ssao2RenderingPipeline',
			'@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/ssrRenderingPipeline',
			'@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/taaRenderingPipeline',
			'@babylonjs/core/PostProcesses/motionBlurPostProcess',
			'@babylonjs/core/PostProcesses/volumetricLightScatteringPostProcess',
			'@babylonjs/core/scene',
			'@babylonjs/core/sceneComponent',
			'@babylonjs/core/Sprites/sprite',
			'@babylonjs/core/Sprites/spriteManager',
			'@babylonjs/core/Sprites/spriteMap',
			'@babylonjs/gui/2D/advancedDynamicTexture',
			'@babylonjs/inspector',
			'@babylonjs/materials',
			'babylonjs-editor-tools'
		]
	}
});
