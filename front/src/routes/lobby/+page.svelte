<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { PUBLIC_API_URL } from '$env/static/public';
	import { authStore } from '$lib/stores/auth.svelte';
	import LobbySelector from '$lib/components/lobby/LobbySelector.svelte';
	import DebugGamePanel from '$lib/components/lobby/DebugGamePanel.svelte';
	import BabylonEditorScene from '$lib/components/BabylonEditorScene.svelte';
	import {
		GameConnection,
		type ValidAction,
		type GameMessage,
		type ActionData
	} from '../../babylon-editor/src/scripts/game';
	import type { PageData } from './$types';
	import type { DeckReadSummary, RoomSummary } from '$lib/types';

	let { data }: { data: PageData } = $props();

	// Lobby state
	let decks = $state<DeckReadSummary[]>(data.decks ?? []);
	let rooms = $state<RoomSummary[]>(data.rooms ?? []);
	let selectedDeckId = $state<number | null>(null);
	let selectedRoomId = $state<string | null>(null);
	let createNewRoom = $state(false);
	let loadingRooms = $state(false);
	let connectionError = $state<string | null>(null);

	// Game mode: 'debug' shows WebSocket panel, 'babylon' shows 3D scene
	type GameMode = 'debug' | 'babylon';
	let gameMode = $state<GameMode>('babylon');

	// Game state (bridged from GameConnection)
	let gameConnection: GameConnection | null = $state(null);
	let connected = $state(false);
	let messages = $state<GameMessage[]>([]);
	let validActions = $state<ValidAction[]>([]);

	// WebSocket URL
	const wsUrl = PUBLIC_API_URL.replace(/^http/, 'ws').replace(/\/$/, '');

	async function fetchRooms() {
		loadingRooms = true;
		try {
			const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
			if (!token) return;

			const response = await fetch(`${PUBLIC_API_URL}/game/rooms`, {
				headers: {
					Authorization: `Bearer ${token}`,
					'Content-Type': 'application/json'
				}
			});

			if (response.ok) {
				const fetchedData = await response.json();
				rooms = fetchedData.rooms || [];
			}
		} catch (error) {
			console.error('Error fetching rooms:', error);
		} finally {
			loadingRooms = false;
		}
	}

	function connect() {
		if (!authStore.isAuthenticated || !authStore.user) {
			connectionError = 'No authentication token. Please log in.';
			goto('/login');
			return;
		}

		const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
		if (!token) {
			connectionError = 'No authentication token. Please log in.';
			goto('/login');
			return;
		}

		if (!selectedDeckId) {
			connectionError = 'Please select a valid deck to connect.';
			return;
		}

		const selectedDeck = decks.find((d) => d.id === selectedDeckId);
		if (!selectedDeck || !selectedDeck.is_valid_for_playing) {
			connectionError = 'Selected deck is not valid for playing.';
			return;
		}

		if (!createNewRoom && !selectedRoomId) {
			connectionError = 'Please select a room or choose to create a new one.';
			return;
		}

		if (!createNewRoom && selectedRoomId) {
			const selectedRoom = rooms.find((r) => r.room_id === selectedRoomId);
			if (!selectedRoom || !selectedRoom.can_join) {
				connectionError = 'Selected room cannot be joined.';
				return;
			}
		}

		connectionError = null;

		// For babylon mode, we don't create GameConnection here - it's handled by the component
		if (gameMode === 'babylon') {
			connected = true;
			return;
		}

		// Debug mode: create inline WebSocket connection
		gameConnection = new GameConnection({
			wsUrl,
			token,
			deckId: selectedDeckId,
			roomId: !createNewRoom ? (selectedRoomId ?? undefined) : undefined,
			playerId: String(authStore.user!.id),
			callbacks: {
				onMessage: (msg) => {
					messages = [...messages, msg];
				},
				onValidActionsChange: (actions) => {
					validActions = actions;
				},
				onConnectionChange: (isConnected) => {
					connected = isConnected;
					if (isConnected) {
						connectionError = null;
					}
				},
				onError: (error) => {
					connectionError = error;
				}
			}
		});
	}

	function handleReconnect() {
		gameConnection?.dispose();
		gameConnection = null;
		connected = false;
		selectedDeckId = null;
		selectedRoomId = null;
		createNewRoom = false;
		messages = [];
		validActions = [];
	}

	function handleSendAction(actionData: ActionData) {
		gameConnection?.sendAction(actionData);
	}

	function handleSendRawMessage(text: string) {
		if (!gameConnection) return;
		try {
			const parsed = JSON.parse(text);
			gameConnection.sendRawMessage(parsed);
		} catch {
			gameConnection.sendRawMessage({ type: 'raw', data: text });
		}
	}

	onMount(() => {
		const interval = setInterval(() => {
			if (!connected) {
				fetchRooms();
			}
		}, 5000);
		return () => clearInterval(interval);
	});

	onDestroy(() => {
		gameConnection?.dispose();
	});
</script>

<div class="lobby-page">
	{#if !connected}
		<header class="lobby-header">
			<h1>Game Lobby</h1>
			<div class="mode-selector">
				<span class="mode-label">Game Mode:</span>
				<div class="mode-toggle">
					<button
						class="mode-btn"
						class:active={gameMode === 'babylon'}
						onclick={() => (gameMode = 'babylon')}
					>
						3D Game
					</button>
					<button
						class="mode-btn"
						class:active={gameMode === 'debug'}
						onclick={() => (gameMode = 'debug')}
					>
						Debug
					</button>
				</div>
			</div>
		</header>

		<div class="lobby-content">
			<LobbySelector
				{decks}
				{rooms}
				{selectedDeckId}
				{selectedRoomId}
				{createNewRoom}
				{loadingRooms}
				{connectionError}
				onDeckSelect={(id) => {
					selectedDeckId = id;
					connectionError = null;
				}}
				onRoomSelect={(id) => {
					selectedRoomId = id;
					connectionError = null;
				}}
				onCreateNewRoomChange={(value) => {
					createNewRoom = value;
					connectionError = null;
				}}
				onRefreshRooms={fetchRooms}
				onConnect={connect}
			/>
		</div>
	{:else if gameMode === 'debug'}
		<DebugGamePanel
			{messages}
			{validActions}
			{connected}
			onSendAction={handleSendAction}
			onSendRawMessage={handleSendRawMessage}
			onReconnect={handleReconnect}
			userName={authStore.user?.full_name || authStore.user?.username}
		/>
	{:else}
		<div class="game-view">
			<header class="game-header">
				<h1>Playing</h1>
				<p class="hint">Press <kbd>Ctrl</kbd> + <kbd>I</kbd> to toggle inspector</p>
				<button class="back-btn" onclick={handleReconnect}>Back to Lobby</button>
			</header>
			<div class="scene-wrapper">
				<BabylonEditorScene
					scenePath="/scene/"
					sceneFile="Battle.babylon"
					{wsUrl}
					token={localStorage.getItem('auth_token') ?? ''}
					playerId={String(authStore.user?.id ?? '')}
					deckId={selectedDeckId}
					roomId={createNewRoom ? null : selectedRoomId}
					createRoom={createNewRoom}
				/>
			</div>
		</div>
	{/if}
</div>

<style lang="scss">
	@use '$lib/styles/abstracts/variables' as variables;
	@use '$lib/styles/abstracts/functions' as functions;

	.lobby-page {
		display: flex;
		flex-direction: column;
		height: calc(100vh - 120px);
		padding: functions.rem(20);
		gap: functions.rem(16);
		background: linear-gradient(145deg, #0d1117 0%, #161b22 100%);
	}

	.lobby-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: functions.rem(16);

		h1 {
			margin: 0;
			font-family: variables.$font-title;
			font-size: functions.rem(32);
			background: linear-gradient(135deg, #58a6ff 0%, #a371f7 100%);
			-webkit-background-clip: text;
			-webkit-text-fill-color: transparent;
			background-clip: text;
		}
	}

	.mode-selector {
		display: flex;
		align-items: center;
		gap: functions.rem(12);
	}

	.mode-label {
		font-size: functions.rem(14);
		color: #8b949e;
	}

	.mode-toggle {
		display: flex;
		background: #21262d;
		border-radius: functions.rem(8);
		padding: functions.rem(4);
		border: 1px solid #30363d;
	}

	.mode-btn {
		padding: functions.rem(8) functions.rem(16);
		background: transparent;
		border: none;
		border-radius: functions.rem(6);
		color: #8b949e;
		font-family: inherit;
		font-size: functions.rem(14);
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;

		&:hover:not(.active) {
			color: #c9d1d9;
		}

		&.active {
			background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
			color: #fff;
		}
	}

	.lobby-content {
		flex: 1;
		overflow-y: auto;
		max-width: 700px;
		margin: 0 auto;
		width: 100%;
	}

	.game-view {
		display: flex;
		flex-direction: column;
		flex: 1;
		gap: functions.rem(16);
	}

	.game-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: functions.rem(12);

		h1 {
			margin: 0;
			font-family: variables.$font-title;
			font-size: functions.rem(28);
			background: linear-gradient(135deg, #58a6ff 0%, #a371f7 100%);
			-webkit-background-clip: text;
			-webkit-text-fill-color: transparent;
			background-clip: text;
		}

		.hint {
			margin: 0;
			font-size: functions.rem(14);
			opacity: 0.6;

			kbd {
				padding: functions.rem(2) functions.rem(6);
				background: #21262d;
				border: 1px solid #30363d;
				border-radius: functions.rem(4);
				font-family: inherit;
				font-size: functions.rem(12);
			}
		}
	}

	.back-btn {
		padding: functions.rem(8) functions.rem(16);
		background: #30363d;
		border: 1px solid #484f58;
		border-radius: functions.rem(6);
		color: #c9d1d9;
		font-family: inherit;
		font-size: functions.rem(14);
		cursor: pointer;
		transition: all 0.2s ease;

		&:hover {
			background: #484f58;
		}
	}

	.scene-wrapper {
		flex: 1;
		border-radius: functions.rem(12);
		overflow: hidden;
		border: 1px solid #30363d;
		background: #0d1117;
		display: flex;
		align-items: center;
		justify-content: center;
	}
</style>
