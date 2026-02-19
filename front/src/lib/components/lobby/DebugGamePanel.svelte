<script lang="ts">
	import ActionCards from '$lib/components/ActionCards.svelte';
	import type { GameMessage, ValidAction, ActionData } from '../../../babylon-editor/src/scripts/game';

	interface Props {
		messages: GameMessage[];
		validActions: ValidAction[];
		connected: boolean;
		onSendAction: (action: ActionData) => void;
		onSendRawMessage: (text: string) => void;
		onReconnect: () => void;
		userName?: string;
	}

	let {
		messages,
		validActions,
		connected,
		onSendAction,
		onSendRawMessage,
		onReconnect,
		userName
	}: Props = $props();

	let actionCardsCollapsed = $state(false);
	let promptText = $state('');

	function sendMessage(event: SubmitEvent) {
		event.preventDefault();
		if (promptText.trim()) {
			onSendRawMessage(promptText);
			promptText = '';
		}
	}
</script>

<div class="debug-layout">
	<aside class="action-cards-sidebar" class:collapsed={actionCardsCollapsed}>
		<div class="sidebar-header">
			<h2>Actions</h2>
			<button class="collapse-btn" onclick={() => (actionCardsCollapsed = !actionCardsCollapsed)}>
				{actionCardsCollapsed ? '▶' : '◀'}
			</button>
		</div>
		{#if !actionCardsCollapsed}
			<div class="action-cards-content">
				<ActionCards {validActions} onSendAction={onSendAction} />
			</div>
		{/if}
	</aside>

	<div class="chat-container">
		<header>
			<div class="header-left">
				<h1>Debug WebSocket</h1>
				{#if userName}
					<span class="user-info">Playing as: {userName}</span>
				{/if}
			</div>
			<div class="header-right">
				<span class="status" class:connected>
					{connected ? '● Connected' : '○ Disconnected'}
				</span>
				<button class="reconnect-btn" onclick={onReconnect}>Back to Lobby</button>
			</div>
		</header>

		<ul class="messages">
			{#each messages as message, i}
				<li
					class="message"
					style="animation-delay: {i * 0.05}s"
					class:failed={message.data.success !== undefined && !message.data.success}
				>
					<h3>{message.type}</h3>
					<pre>{JSON.stringify(message, null, 2)}</pre>
				</li>
			{/each}
		</ul>

		<form onsubmit={sendMessage}>
			<input
				type="text"
				bind:value={promptText}
				placeholder={'Send JSON: {"type": "ping"} or {"type": "list_rooms"}'}
				autocomplete="off"
				disabled={!connected}
			/>
			<button type="submit" disabled={!connected || !promptText.trim()}>Send</button>
		</form>
	</div>
</div>

<style>
	.debug-layout {
		display: flex;
		height: 100%;
		gap: 1rem;
		font-family: 'JetBrains Mono', 'Fira Code', monospace;
		color: #c9d1d9;
		overflow: hidden;
	}

	.action-cards-sidebar {
		flex: 0 0 400px;
		display: flex;
		flex-direction: column;
		background: #161b22;
		border-radius: 8px;
		border: 1px solid #30363d;
		overflow: hidden;
		transition: flex-basis 0.3s ease;
	}

	.action-cards-sidebar.collapsed {
		flex: 0 0 60px;
	}

	.sidebar-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		border-bottom: 1px solid #30363d;
		background: #0d1117;
	}

	.sidebar-header h2 {
		margin: 0;
		font-size: 1.25rem;
		color: #c9d1d9;
	}

	.collapse-btn {
		padding: 0.5rem;
		background: #30363d;
		border: 1px solid #484f58;
		border-radius: 4px;
		color: #c9d1d9;
		cursor: pointer;
		font-size: 0.875rem;
		transition: all 0.2s ease;
		min-width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.collapse-btn:hover {
		background: #484f58;
	}

	.action-cards-sidebar.collapsed .sidebar-header h2 {
		display: none;
	}

	.action-cards-content {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
	}

	.action-cards-sidebar.collapsed .action-cards-content {
		display: none;
	}

	.chat-container {
		flex: 1;
		display: flex;
		flex-direction: column;
		max-width: 800px;
		margin: 0 auto;
		padding: 1.5rem;
		background: #161b22;
		border-radius: 8px;
		border: 1px solid #30363d;
		overflow: hidden;
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
		border-radius: 6px;
		color: #c9d1d9;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.reconnect-btn:hover:not(:disabled) {
		background: #484f58;
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

	.message h3 {
		margin: 0;
		font-size: 0.8rem;
		color: #8b949e;
		font-weight: 600;
	}

	.message.failed {
		border-left-color: #f85149;
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

	button[type='submit'] {
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

	button[type='submit']:hover:not(:disabled) {
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
	}

	button[type='submit']:active:not(:disabled) {
		transform: translateY(0);
	}

	button[type='submit']:disabled {
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
