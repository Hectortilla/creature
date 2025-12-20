<script lang="ts">
	import { onMount, onDestroy } from 'svelte';

	let messages: string[] = $state([]);
	let messageText = $state('');
	let ws: WebSocket | null = $state(null);
	let connected = $state(false);

	onMount(() => {
		ws = new WebSocket('ws://localhost:8000/game');

		ws.onopen = () => {
			connected = true;
		};

		ws.onmessage = (event) => {
			messages = [...messages, event.data];
		};

		ws.onclose = () => {
			connected = false;
		};

		ws.onerror = () => {
			connected = false;
		};
	});

	onDestroy(() => {
		if (ws) {
			ws.close();
		}
	});

	function sendMessage(event: SubmitEvent) {
		event.preventDefault();
		if (ws && messageText.trim()) {
			ws.send(messageText);
			messageText = '';
		}
	}
</script>

<div class="chat-container">
	<header>
		<h1>WebSocket Chat</h1>
		<span class="status" class:connected>
			{connected ? '● Connected' : '○ Disconnected'}
		</span>
	</header>

	<ul class="messages">
		{#each messages as message, i}
			<li class="message" style="animation-delay: {i * 0.05}s">
				{message}
			</li>
		{/each}
	</ul>

	<form onsubmit={sendMessage}>
		<input
			type="text"
			bind:value={messageText}
			placeholder="Type a message..."
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

	.status {
		font-size: 0.75rem;
		color: #f85149;
		transition: color 0.3s ease;
	}

	.status.connected {
		color: #3fb950;
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

