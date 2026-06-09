<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import type { Engine } from '@babylonjs/core/Engines/engine';
	import type { Scene } from '@babylonjs/core/scene';
	import { getScriptByClassForObject } from 'babylonjs-editor-tools';
	import GameConnection from '../../babylon-editor/src/scripts/game/GameConnection';
	import HudController from '../../babylon-editor/src/scripts/hud/HudController';
	import { DevToolPanel } from '../../babylon-editor/src/scripts/devtools/DevToolPanel';
	// Static import; guarded by `__CREATURE_E2E_HOOKS__` below so it's tree-shaken from prod builds.
	import { attachE2EHarness } from '../../babylon-editor/src/scripts/devtools/E2EHarness';
	import { setHoveredCard } from '$lib/stores/babylon/hoveredCard';
	import { setElementPools } from '$lib/stores/babylon/elementPools';
	import HoveredCardOverlay from '$lib/components/babylon/HoveredCardOverlay.svelte';
	import ElementPoolsOverlay from '$lib/components/babylon/ElementPoolsOverlay.svelte';
	import type { Creature, Element } from '$lib/types';

	interface Props {
		scenePath?: string;
		sceneFile?: string;
		enablePhysics?: boolean;
		gravity?: { x: number; y: number; z: number };
		wsUrl?: string;
		token?: string;
		playerId?: string;
		deckId?: number | null;
		roomId?: string | null;
		createRoom?: boolean;
		cards?: Creature[];
		elements?: Element[];
	}

	let {
		scenePath = '/scene/',
		sceneFile = 'example.babylon',
		enablePhysics = true,
		gravity = { x: 0, y: -981, z: 0 },
		wsUrl = '',
		token = '',
		playerId = '',
		deckId = null,
		roomId = null,
		createRoom = false,
		cards = [],
		elements = []
	}: Props = $props();

	let canvas: HTMLCanvasElement;
	let engine: Engine | null = $state(null);
	let scene: Scene | null = $state(null);
	let loading = $state(true);
	let error = $state<string | null>(null);
	// Deterministic "board-ready" signal for E2E / autonomous probes: true only once
	// the scene has initialised successfully and the render loop is running.
	const sceneReady = $derived(!loading && error === null);
	let devToolPanel: DevToolPanel | null = null;
	// `__CREATURE_E2E_HOOKS__`: vite `define` literal, true only in the e2e preview build.
	const e2eHooks = __CREATURE_E2E_HOOKS__;

	async function initScene() {
		if (!canvas) return;

		try {
			// Import full Babylon.js core to ensure all serializers are registered
			// Import scripts directly from babylon-editor (single source of truth)
			const [BABYLON, HavokPhysicsModule, { loadScene }, { scriptsMap }] = await Promise.all([
				import('@babylonjs/core'),
				import('@babylonjs/havok'),
				import('babylonjs-editor-tools'),
				import('../../babylon-editor/src/scripts')
			]);

			// Additional imports for materials and inspector
			await Promise.all([
				import('@babylonjs/materials'),
				import('@babylonjs/core/Debug/debugLayer'),
				import('@babylonjs/inspector')
			]);

			const { Engine, Scene, Vector3, HavokPlugin, SceneLoaderFlags } = BABYLON;

			engine = new Engine(canvas, true, {
				stencil: true,
				antialias: true,
				audioEngine: true,
				adaptToDeviceRatio: true,
				powerPreference: 'high-performance'
			});

			scene = new Scene(engine);

			if (enablePhysics) {
				const havok = await HavokPhysicsModule.default();
				scene.enablePhysics(new Vector3(gravity.x, gravity.y, gravity.z), new HavokPlugin(true, havok));
			}

			SceneLoaderFlags.ForceFullSceneLoadingForIncremental = true;
			await loadScene(scenePath, sceneFile, scene, scriptsMap, { quality: 'high' });
			
			const scriptInstance = getScriptByClassForObject(scene, GameConnection);
			if (!scriptInstance) {
				throw new Error('GameConnection must be attached to the root scene');
			}
			scriptInstance.wsUrl = wsUrl;
			scriptInstance.token = token;
			scriptInstance.playerId = playerId;
			scriptInstance.deckId = deckId ?? 0;
			scriptInstance.roomId = roomId ?? '';
			scriptInstance.createRoom = createRoom;

			const hud = getScriptByClassForObject(scene, HudController);
			hud?.setHoveredCardSetter(setHoveredCard);
			hud?.setElementPoolsSetter(setElementPools);

			if (scene.activeCamera) {
				scene.activeCamera.attachControl();
			}

			// E2E drive API — attached only in the e2e preview build, after loadScene sets BoardController.instance.
			if (e2eHooks) {
				attachE2EHarness();
			}

			engine.runRenderLoop(() => scene?.render());
			loading = false;
		} catch (e) {
			console.error('Failed to load scene:', e);
			error = e instanceof Error ? e.message : 'Failed to load scene';
			loading = false;
		}
	}

	function handleResize() {
		engine?.resize();
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.ctrlKey && event.key.toLowerCase() === 'i') {
			if (scene?.debugLayer.isVisible()) {
				scene.debugLayer.hide();
			} else {
				scene?.debugLayer.show();
			}
		}

		if (event.ctrlKey && event.key.toLowerCase() === 'd') {
			if (!devToolPanel && scene) devToolPanel = new DevToolPanel(scene);
			devToolPanel?.toggle();
		}
	}

	onMount(() => {
		initScene();
		window.addEventListener('resize', handleResize);
		window.addEventListener('keydown', handleKeydown);
	});

	onDestroy(() => {
		if (!browser) return;
		window.removeEventListener('resize', handleResize);
		window.removeEventListener('keydown', handleKeydown);
		devToolPanel?.dispose();
		devToolPanel = null;
		scene?.dispose();
		engine?.dispose();
		setHoveredCard(null);
		setElementPools(null);
	});
</script>

<div class="scene-container" data-testid="game-board" data-scene-ready={sceneReady ? 'true' : 'false'}>
	{#if loading}
		<div class="loading">Loading scene...</div>
	{:else if error}
		<div class="error">{error}</div>
	{/if}
	<canvas bind:this={canvas} data-testid="game-board-canvas"></canvas>
	<HoveredCardOverlay {cards} {elements} />
	<ElementPoolsOverlay {elements} />
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

	.loading,
	.error {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 1.25rem;
		z-index: 1;
	}

	.loading {
		color: var(--color-text, #c9d1d9);
	}

	.error {
		color: #f85149;
	}
</style>
