<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { PUBLIC_API_URL } from '$env/static/public';
	import { auth } from '$lib/stores/auth.svelte';
	import type { PageData } from './$types';

	interface DeckSummary {
		id: number;
		name: string;
		description: string | null;
		card_count: number;
		is_valid_for_playing: boolean;
	}

	let { data }: { data: PageData } = $props();

	let messages: string[] = $state([]);
	let messageText = $state('');
	let ws: WebSocket | null = $state(null);
	let connected = $state(false);
	let connectionError = $state<string | null>(null);
	let decks = $state<DeckSummary[]>(data.decks ?? []);
	let selectedDeckId = $state<number | null>(null);

	// Convert http(s):// to ws(s):// for WebSocket connection
	const wsUrl = PUBLIC_API_URL.replace(/^http/, 'ws').replace(/\/$/, '');

	function connect() {
		if (!auth.isAuthenticated) {
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

		const selectedDeck = decks.find(d => d.id === selectedDeckId);
		if (!selectedDeck || !selectedDeck.is_valid_for_playing) {
			connectionError = 'Selected deck is not valid for playing.';
			return;
		}

		connectionError = null;
		const wsPath = `${wsUrl}/game/ws?token=${encodeURIComponent(token)}&deck_id=${selectedDeckId}`;
		ws = new WebSocket(wsPath);

		ws.onopen = () => {
			connected = true;
			connectionError = null;
		};

		ws.onmessage = (event) => {
			// Parse JSON messages from server
			try {
				const data = JSON.parse(event.data);
				messages = [...messages, JSON.stringify(data, null, 2)];
			} catch {
				messages = [...messages, event.data];
			}
		};

		ws.onclose = (event) => {
			connected = false;
			if (event.code === 1008) {
				// Policy violation - could be auth or deck validation
				const reason = event.reason || 'Connection refused';
				connectionError = reason || 'Connection refused. Please check your deck and try again.';
			}
		};

		ws.onerror = () => {
			connected = false;
			connectionError = 'Connection error. Please try again.';
		};
	}

	onMount(() => {
		// Decks are already loaded server-side via +page.server.ts
	});

	onDestroy(() => {
		if (ws) {
			ws.close();
		}
	});

	function sendMessage(event: SubmitEvent) {
		event.preventDefault();
		if (ws && messageText.trim()) {
			// Send as JSON message
			try {
				const parsed = JSON.parse(messageText);
				ws.send(JSON.stringify(parsed));
			} catch {
				// If not valid JSON, wrap it
				ws.send(JSON.stringify({ type: 'raw', data: messageText }));
			}
			messageText = '';
		}
	}

	function reconnect() {
		if (ws) {
			ws.close();
		}
		connected = false;
		selectedDeckId = null;
		messages = [];
		// Reload page to get fresh deck data
		window.location.reload();
	}
</script>

<div class="chat-container">
	<header>
		<div class="header-left">
			<h1>Game WebSocket</h1>
			{#if auth.user}
				<span class="user-info">Playing as: {auth.user.full_name || auth.user.username}</span>
			{/if}
		</div>
		<div class="header-right">
			<span class="status" class:connected>
				{connected ? '● Connected' : '○ Disconnected'}
			</span>
			{#if !connected}
				<button class="reconnect-btn" onclick={reconnect}>Reconnect</button>
			{/if}
		</div>
	</header>

	{#if connectionError}
		<div class="error-banner">
			{connectionError}
		</div>
	{/if}

	{#if !connected}
		<div class="deck-selection">
			<h2>Select a Deck</h2>
			{#if decks.length === 0}
				<div class="no-decks">
					<p>No decks found. <a href="/decks">Create a deck</a> first.</p>
				</div>
			{:else}
				<div class="deck-list">
					{#each decks as deck}
						<button
							class="deck-item"
							class:selected={selectedDeckId === deck.id}
							class:invalid={!deck.is_valid_for_playing}
							onclick={() => {
								if (deck.is_valid_for_playing) {
									selectedDeckId = deck.id;
									connectionError = null;
								}
							}}
							disabled={!deck.is_valid_for_playing}
						>
							<div class="deck-info">
								<span class="deck-name">{deck.name}</span>
								<span class="deck-meta">
									{deck.card_count} cards
									{#if deck.is_valid_for_playing}
										<span class="valid-badge">✓ Valid</span>
									{:else}
										<span class="invalid-badge">✗ Invalid</span>
									{/if}
								</span>
							</div>
							{#if deck.description}
								<p class="deck-description">{deck.description}</p>
							{/if}
						</button>
					{/each}
				</div>
				<button
					class="connect-btn"
					onclick={connect}
					disabled={!selectedDeckId || connected}
				>
					Connect to Game
				</button>
			{/if}
		</div>
	{/if}

	<ul class="messages">
		{#each messages as message, i}
			<li class="message" style="animation-delay: {i * 0.05}s">
				<pre>{message}</pre>
			</li>
		{/each}
	</ul>

	<form onsubmit={sendMessage}>
		<input
			type="text"
			bind:value={messageText}
			placeholder={'Send JSON: {"type": "ping"} or {"type": "list_rooms"}'}
			autocomplete="off"
			disabled={!connected}
		/>
		<button type="submit" disabled={!connected || !messageText.trim()}>
			Send
		</button>
	</form>
</div>

<style>
	.chat-container {
		display: flex;
		flex-direction: column;
		height: 100vh;
		max-width: 720px;
		margin: 0 auto;
		padding: 1.5rem;
		font-family: 'JetBrains Mono', 'Fira Code', monospace;
		background: linear-gradient(145deg, #0d1117 0%, #161b22 100%);
		color: #c9d1d9;
	}

	header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding-bottom: 1rem;
		border-bottom: 1px solid #30363d;
		margin-bottom: 1rem;
		gap: 1rem;
	}

	.header-left {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.header-right {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	h1 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 600;
		background: linear-gradient(135deg, #58a6ff 0%, #a371f7 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.user-info {
		font-size: 0.75rem;
		color: #8b949e;
	}

	.status {
		font-size: 0.75rem;
		color: #f85149;
		transition: color 0.3s ease;
	}

	.status.connected {
		color: #3fb950;
	}

	.reconnect-btn {
		padding: 0.4rem 0.75rem;
		font-size: 0.75rem;
		background: #30363d;
		border: 1px solid #484f58;
	}

	.reconnect-btn:hover:not(:disabled) {
		background: #484f58;
		box-shadow: none;
		transform: none;
	}

	.error-banner {
		padding: 0.75rem 1rem;
		background: rgba(248, 81, 73, 0.15);
		border: 1px solid #f85149;
		border-radius: 8px;
		color: #f85149;
		font-size: 0.85rem;
		margin-bottom: 1rem;
	}

	.deck-selection {
		padding: 1.5rem;
		margin-bottom: 1rem;
	}

	.deck-selection h2 {
		margin: 0 0 1rem 0;
		font-size: 1.25rem;
		color: #c9d1d9;
	}

	.no-decks {
		padding: 1rem;
		text-align: center;
		color: #8b949e;
	}

	.no-decks a {
		color: #58a6ff;
		text-decoration: none;
	}

	.no-decks a:hover {
		text-decoration: underline;
	}

	.deck-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		margin-bottom: 1rem;
	}

	.deck-item {
		padding: 1rem;
		background: #0d1117;
		border: 2px solid #30363d;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s ease;
		text-align: left;
		width: 100%;
	}

	.deck-item:hover:not(:disabled) {
		border-color: #58a6ff;
		background: #161b22;
	}

	.deck-item.selected {
		border-color: #3fb950;
		background: rgba(63, 185, 80, 0.1);
	}

	.deck-item.invalid {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.deck-item:disabled {
		cursor: not-allowed;
		opacity: 0.6;
	}

	.deck-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.deck-name {
		font-weight: 600;
		color: #c9d1d9;
		font-size: 1rem;
	}

	.deck-meta {
		font-size: 0.85rem;
		color: #8b949e;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.valid-badge {
		color: #3fb950;
		font-weight: 600;
	}

	.invalid-badge {
		color: #f85149;
		font-weight: 600;
	}

	.deck-description {
		margin: 0;
		font-size: 0.85rem;
		color: #8b949e;
		font-style: italic;
	}

	.connect-btn {
		width: 100%;
		padding: 0.875rem 1.5rem;
		background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
		border: none;
		border-radius: 8px;
		color: #fff;
		font-family: inherit;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
	}

	.connect-btn:hover:not(:disabled) {
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
	}

	.connect-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.messages {
		flex: 1;
		overflow-y: auto;
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.message {
		padding: 0.75rem 1rem;
		background: #21262d;
		border-radius: 8px;
		border-left: 3px solid #58a6ff;
		animation: slideIn 0.3s ease forwards;
		opacity: 0;
		transform: translateX(-10px);
	}

	.message pre {
		margin: 0;
		white-space: pre-wrap;
		word-break: break-word;
		font-size: 0.8rem;
		line-height: 1.4;
	}

	@keyframes slideIn {
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}

	form {
		display: flex;
		gap: 0.75rem;
		padding-top: 1rem;
		border-top: 1px solid #30363d;
		margin-top: 1rem;
	}

	input {
		flex: 1;
		padding: 0.75rem 1rem;
		background: #0d1117;
		border: 1px solid #30363d;
		border-radius: 8px;
		color: #c9d1d9;
		font-family: inherit;
		font-size: 0.9rem;
		outline: none;
		transition: border-color 0.2s ease, box-shadow 0.2s ease;
	}

	input:focus {
		border-color: #58a6ff;
		box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.15);
	}

	input::placeholder {
		color: #484f58;
	}

	input:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	button {
		padding: 0.75rem 1.5rem;
		background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
		border: none;
		border-radius: 8px;
		color: #fff;
		font-family: inherit;
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
	}

	button:hover:not(:disabled) {
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
	}

	button:active:not(:disabled) {
		transform: translateY(0);
	}

	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* Scrollbar styling */
	.messages::-webkit-scrollbar {
		width: 6px;
	}

	.messages::-webkit-scrollbar-track {
		background: #0d1117;
		border-radius: 3px;
	}

	.messages::-webkit-scrollbar-thumb {
		background: #30363d;
		border-radius: 3px;
	}

	.messages::-webkit-scrollbar-thumb:hover {
		background: #484f58;
	}
</style>
