<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import '@babylonjs/core/Debug/debugLayer';
	import '@babylonjs/inspector';
	import {
		Engine,
		Scene,
		ArcRotateCamera,
		Vector3,
		HemisphericLight,
		MeshBuilder
	} from '@babylonjs/core';

	let canvas: HTMLCanvasElement;
	let engine: Engine | null = $state(null);
	let scene: Scene | null = $state(null);
	let loading = $state(true);

	function initScene() {
		if (!canvas) return;

		engine = new Engine(canvas, true);
		scene = new Scene(engine);

		const camera = new ArcRotateCamera(
			'Camera',
			Math.PI / 2,
			Math.PI / 2,
			2,
			Vector3.Zero(),
			scene
		);
		camera.attachControl(canvas, true);

		new HemisphericLight('light1', new Vector3(1, 1, 0), scene);
		MeshBuilder.CreateSphere('sphere', { diameter: 1 }, scene);

		engine.runRenderLoop(() => scene?.render());
		loading = false;
	}

	function handleResize() {
		engine?.resize();
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.shiftKey && event.ctrlKey && event.altKey && event.key.toLowerCase() === 'i') {
			if (scene?.debugLayer.isVisible()) {
				scene.debugLayer.hide();
			} else {
				scene?.debugLayer.show();
			}
		}
	}

	onMount(() => {
		initScene();
		window.addEventListener('resize', handleResize);
		window.addEventListener('keydown', handleKeydown);
	});

	onDestroy(() => {
		window.removeEventListener('resize', handleResize);
		window.removeEventListener('keydown', handleKeydown);
		scene?.dispose();
		engine?.dispose();
	});
</script>

<div class="scene-container">
	{#if loading}
		<div class="loading">Loading scene...</div>
	{/if}
	<canvas bind:this={canvas}></canvas>
</div>

<style lang="scss">
	.scene-container {
		position: relative;
		width: 100%;
		height: 100%;
		min-height: 500px;
	}

	canvas {
		width: 100%;
		height: 100%;
		display: block;
		outline: none;
	}

	.loading {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 1.25rem;
		color: var(--color-text, #c9d1d9);
		z-index: 1;
	}
</style>
