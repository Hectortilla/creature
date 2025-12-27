<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { PUBLIC_API_URL } from '$env/static/public';
	import { auth } from '$lib/stores/auth.svelte';

	let messages: string[] = $state([]);
	let messageText = $state('');
	let ws: WebSocket | null = $state(null);
	let connected = $state(false);
	let connectionError = $state<string | null>(null);

	// Convert http(s):// to ws(s):// for WebSocket connection
	const wsUrl = PUBLIC_API_URL.replace(/^http/, 'ws');

	function connect() {
		const token = auth.getToken();
		
		if (!token) {
			connectionError = 'No authentication token. Please log in.';
			goto('/login');
			return;
		}

		connectionError = null;
		ws = new WebSocket(`${wsUrl}/game/ws?token=${encodeURIComponent(token)}`);

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
				// Policy violation - authentication failed
				connectionError = 'Authentication failed. Please log in again.';
				auth.clearAuth();
				goto('/login');
			}
		};

		ws.onerror = () => {
			connected = false;
			connectionError = 'Connection error. Please try again.';
		};
	}

	onMount(() => {
		connect();
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
		connect();
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
			placeholder='Send JSON: {"type": "ping"} or {"type": "list_rooms"}'
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
