<script lang="ts">
	import { onMount } from 'svelte';
	import BabylonEditorScene from '$lib/components/BabylonEditorScene.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	onMount(() => {
		if (data.gameParams) {
			console.log('Game params from URL:', data.gameParams);
		}
	});
</script>

<div class="game-page">
	<header>
		<h1>Jugar</h1>
		<p class="hint">Press <kbd>Ctrl</kbd> + <kbd>I</kbd> to toggle inspector</p>
	</header>
	<div class="scene-wrapper">
		<BabylonEditorScene 
			scenePath="/scene/" 
			sceneFile="example.babylon"
			deckId={data.gameParams?.deckId}
			roomId={data.gameParams?.roomId}
			createRoom={data.gameParams?.createRoom ?? false}
		/>
	</div>
</div>

<style lang="scss">
	@use "$lib/styles/abstracts/variables" as variables;
	@use "$lib/styles/abstracts/functions" as functions;
	@use "$lib/styles/abstracts/mixins" as mixins;

	.game-page {
		display: flex;
		flex-direction: column;
		height: calc(100vh - 120px);
		padding: functions.rem(20);
		gap: functions.rem(16);
	}

	header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: functions.rem(12);

		h1 {
			margin: 0;
			font-family: variables.$font-title;
			font-size: functions.rem(32);
		}

		.hint {
			margin: 0;
			font-size: functions.rem(14);
			opacity: 0.6;

			kbd {
				padding: functions.rem(2) functions.rem(6);
				background: var(--color-input-background, #21262d);
				border: 1px solid var(--color-input-border, #30363d);
				border-radius: functions.rem(4);
				font-family: inherit;
				font-size: functions.rem(12);
			}
		}
	}

	.scene-wrapper {
		flex: 1;
		border-radius: functions.rem(12);
		overflow: hidden;
		border: 1px solid var(--color-input-border, #30363d);
		background: #0d1117;
	}
</style>
