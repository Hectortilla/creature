<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { goto } from '$app/navigation';
    import { PUBLIC_API_URL } from '$env/static/public';
    import { authStore } from '$lib/stores/auth.svelte';
    import ActionCards from '$lib/components/ActionCards.svelte';
    import { GameConnection, type ValidAction, type GameMessage, type ActionData } from '$lib/game';
    import type { PageData } from './$types';
    import type { DeckReadSummary, RoomSummary } from '$lib/types';

    let { data }: { data: PageData } = $props();
    
    // Lobby state (stays in this component)
    let decks = $state<DeckReadSummary[]>(data.decks ?? []);
    let rooms = $state<RoomSummary[]>(data.rooms ?? []);
    let selectedDeckId = $state<number | null>(null);
    let selectedRoomId = $state<string | null>(null);
    let createNewRoom = $state(false);
    let loadingRooms = $state(false);
    let connectionError = $state<string | null>(null);

    // Game state (bridged from GameConnection)
    let ws: WebSocket | null = $state(null);
    let gameConnection: GameConnection | null = $state(null);
    let connected = $state(false);
    let messages = $state<GameMessage[]>([]);
    let validActions = $state<ValidAction[]>([]);
    let actionCardsCollapsed = $state(false);

    // Debug input
    let promptText = $state('');
    
    // Debug mode toggle - when false, redirects to /game instead of inline WS
    let debugMode = $state(true);

    // Convert http(s):// to ws(s):// for WebSocket connection
    const wsUrl = PUBLIC_API_URL.replace(/^http/, 'ws').replace(/\/$/, '');

    async function fetchRooms() {
        loadingRooms = true;
        try {
            const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
            if (!token) return;

            const response = await fetch(`${PUBLIC_API_URL}/game/rooms`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
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

        const selectedDeck = decks.find(d => d.id === selectedDeckId);
        if (!selectedDeck || !selectedDeck.is_valid_for_playing) {
            connectionError = 'Selected deck is not valid for playing.';
            return;
        }

        // Validate room selection if not creating new room
        if (!createNewRoom && !selectedRoomId) {
            connectionError = 'Please select a room or choose to create a new one.';
            return;
        }

        // If joining existing room, validate it can be joined
        if (!createNewRoom && selectedRoomId) {
            const selectedRoom = rooms.find(r => r.room_id === selectedRoomId);
            if (!selectedRoom || !selectedRoom.can_join) {
                connectionError = 'Selected room cannot be joined.';
                return;
            }
        }

        connectionError = null;
        
        // If debug mode is off, redirect to /game with params
        if (!debugMode) {
            const params = new URLSearchParams();
            params.set('deck_id', String(selectedDeckId));
            if (createNewRoom) {
                params.set('create_room', 'true');
            } else if (selectedRoomId) {
                params.set('room_id', selectedRoomId);
            }
            goto(`/game?${params.toString()}`);
            return;
        }

        // Debug mode: inline WebSocket connection
        let wsPath = `${wsUrl}/game/ws?token=${encodeURIComponent(token)}&deck_id=${selectedDeckId}`;
        if (!createNewRoom && selectedRoomId) {
            wsPath += `&room_id=${encodeURIComponent(selectedRoomId)}`;
        }
        
        // Create WebSocket and hand off to GameConnection
        ws = new WebSocket(wsPath);
        
        ws.onopen = () => {
            // Initialize GameConnection once WebSocket is open
            gameConnection = new GameConnection({
                ws: ws!,
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
                    },
                    onError: (error) => {
                        connectionError = error;
                    }
                }
            });
            connected = true;
            connectionError = null;
        };

        ws.onclose = (event) => {
            connected = false;
            gameConnection?.dispose();
            gameConnection = null;
            if (event.code === 1008) {
                connectionError = event.reason || 'Connection refused. Please check your deck and try again.';
            }
        };

        ws.onerror = () => {
            connected = false;
            connectionError = 'Connection error. Please try again.';
        };
    }

    onMount(() => {
        // Refresh rooms periodically when not connected
        const interval = setInterval(() => {
            if (!connected) {
                fetchRooms();
            }
        }, 5000);
        return () => clearInterval(interval);
    });

    onDestroy(() => {
        gameConnection?.dispose();
        ws?.close();
    });

    function sendMessage(event: SubmitEvent) {
        event.preventDefault();
        if (gameConnection && promptText.trim()) {
            try {
                const parsed = JSON.parse(promptText);
                gameConnection.sendRawMessage(parsed);
            } catch {
                gameConnection.sendRawMessage({ type: 'raw', data: promptText });
            }
            promptText = '';
        }
    }

    function reconnect() {
        gameConnection?.dispose();
        ws?.close();
        gameConnection = null;
        ws = null;
        connected = false;
        selectedDeckId = null;
        selectedRoomId = null;
        createNewRoom = false;
        messages = [];
        validActions = [];
        window.location.reload();
    }

    function handleSendAction(actionData: ActionData) {
        gameConnection?.sendAction(actionData);
    }
</script>

<div class="game-layout">
    {#if connected}
        <aside class="action-cards-sidebar" class:collapsed={actionCardsCollapsed}>
            <div class="sidebar-header">
                <h2>Actions</h2>
                <button class="collapse-btn" onclick={() => actionCardsCollapsed = !actionCardsCollapsed}>
                    {actionCardsCollapsed ? '▶' : '◀'}
                </button>
            </div>
            {#if !actionCardsCollapsed}
                <div class="action-cards-content">
                    <ActionCards {validActions} onSendAction={handleSendAction} />
                </div>
            {/if}
        </aside>
    {/if}

    <div class="chat-container">
        <header>
            <div class="header-left">
                <h1>Game WebSocket</h1>
                {#if authStore.user}
                    <span class="user-info">Playing as: {authStore.user.full_name || authStore.user.username}</span>
                {/if}
            </div>
            <div class="header-right">
                <label class="debug-toggle">
                    <span class="toggle-label">Debug Mode</span>
                    <input type="checkbox" bind:checked={debugMode} disabled={connected} />
                    <span class="toggle-slider"></span>
                </label>
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
            {/if}
        </div>

        {#if selectedDeckId}
            <div class="room-selection">
                <h2>Select or Create a Room</h2>
                <div class="room-options">
                    <button
                        class="room-option"
                        class:selected={createNewRoom}
                        onclick={() => {
                            createNewRoom = true;
                            selectedRoomId = null;
                            connectionError = null;
                        }}
                    >
                        <span class="room-option-icon">➕</span>
                        <span class="room-option-text">Create New Room</span>
                    </button>
                    <button
                        class="room-option"
                        class:selected={!createNewRoom}
                        onclick={() => {
                            createNewRoom = false;
                            connectionError = null;
                        }}
                    >
                        <span class="room-option-icon">🔍</span>
                        <span class="room-option-text">Join Existing Room</span>
                    </button>
                </div>

                {#if !createNewRoom}
                    <div class="rooms-section">
                        <div class="rooms-header">
                            <h3>Available Rooms</h3>
                            <button class="refresh-btn" onclick={fetchRooms} disabled={loadingRooms}>
                                {loadingRooms ? '⏳' : '🔄'} Refresh
                            </button>
                        </div>
                        {#if rooms.length === 0}
                            <div class="no-rooms">
                                <p>No available rooms. Create a new room to start playing.</p>
                            </div>
                        {:else}
                            <div class="room-list">
                                {#each rooms as room}
                                    <button
                                        class="room-item"
                                        class:selected={selectedRoomId === room.room_id}
                                        class:can-join={room.can_join}
                                        class:cannot-join={!room.can_join}
                                        onclick={() => {
                                            if (room.can_join) {
                                                selectedRoomId = room.room_id;
                                                connectionError = null;
                                            }
                                        }}
                                        disabled={!room.can_join}
                                    >
                                        <div class="room-info">
                                            <span class="room-id">Room: {room.room_id.slice(0, 8)}...</span>
                                            <span class="room-status">
                                                {#if room.can_join}
                                                    <span class="status-badge can-join">✓ Can Join</span>
                                                {:else if room.is_full}
                                                    <span class="status-badge full">Full</span>
                                                {:else if room.is_started}
                                                    <span class="status-badge started">Started</span>
                                                {:else}
                                                    <span class="status-badge waiting">Waiting</span>
                                                {/if}
                                            </span>
                                        </div>
                                        <div class="room-players">
                                            Players: {Object.keys(room.players).length}/2
                                            {#if room.player1_name}
                                                <span class="player-name">• {room.player1_name}</span>
                                            {/if}
                                            {#if room.player2_name}
                                                <span class="player-name">• {room.player2_name}</span>
                                            {/if}
                                        </div>
                                    </button>
                                {/each}
                            </div>
                        {/if}
                    </div>
                {/if}

                <button
                    class="connect-btn"
                    onclick={connect}
                    disabled={!selectedDeckId || connected || (!createNewRoom && !selectedRoomId)}
                >
                    {createNewRoom ? 'Create Room & Connect' : 'Join Room & Connect'}
                </button>
            </div>
        {/if}
    {/if}

    <ul class="messages">
        {#each messages as message, i}
            <li class="message" style="animation-delay: {i * 0.05}s" class:failed={message.data.success !== undefined && !message.data.success}>
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
        <button type="submit" disabled={!connected || !promptText.trim()}>
            Send
        </button>
    </form>
    </div>
</div>

<style>
    .game-layout {
        display: flex;
        height: 100vh;
        gap: 1rem;
        padding: 1rem;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        background: linear-gradient(145deg, #0d1117 0%, #161b22 100%);
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
        background: #161b22;
        border-radius: 8px;
        border: 1px solid #30363d;
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

    .room-selection {
        padding: 1.5rem;
        background: #161b22;
        border-radius: 8px;
        border: 1px solid #30363d;
        margin-bottom: 1rem;
    }

    .room-selection h2 {
        margin: 0 0 1rem 0;
        font-size: 1.25rem;
        color: #c9d1d9;
    }

    .room-options {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }

    .room-option {
        flex: 1;
        padding: 0.875rem 1rem;
        background: #0d1117;
        border: 2px solid #30363d;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        color: #c9d1d9;
        font-family: inherit;
        font-size: 0.9rem;
    }

    .room-option:hover:not(:disabled) {
        border-color: #58a6ff;
        background: #161b22;
    }

    .room-option.selected {
        border-color: #3fb950;
        background: rgba(63, 185, 80, 0.1);
    }

    .room-option-icon {
        font-size: 1.1rem;
    }

    .rooms-section {
        margin-top: 1rem;
    }

    .rooms-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }

    .rooms-header h3 {
        margin: 0;
        font-size: 1rem;
        color: #c9d1d9;
    }

    .refresh-btn {
        padding: 0.4rem 0.75rem;
        font-size: 0.75rem;
        background: #30363d;
        border: 1px solid #484f58;
        border-radius: 6px;
        color: #c9d1d9;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .refresh-btn:hover:not(:disabled) {
        background: #484f58;
    }

    .refresh-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .no-rooms {
        padding: 1rem;
        text-align: center;
        color: #8b949e;
        font-size: 0.9rem;
    }

    .room-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }

    .room-item {
        padding: 1rem;
        background: #0d1117;
        border: 2px solid #30363d;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: left;
        width: 100%;
    }

    .room-item:hover:not(:disabled) {
        border-color: #58a6ff;
        background: #161b22;
    }

    .room-item.selected {
        border-color: #3fb950;
        background: rgba(63, 185, 80, 0.1);
    }

    .room-item.cannot-join {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .room-item:disabled {
        cursor: not-allowed;
        opacity: 0.6;
    }

    .room-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .room-id {
        font-weight: 600;
        color: #c9d1d9;
        font-size: 0.9rem;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
    }

    .room-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .status-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
    }

    .status-badge.can-join {
        color: #3fb950;
        background: rgba(63, 185, 80, 0.15);
    }

    .status-badge.full {
        color: #f85149;
        background: rgba(248, 81, 73, 0.15);
    }

    .status-badge.started {
        color: #f85149;
        background: rgba(248, 81, 73, 0.15);
    }

    .status-badge.waiting {
        color: #8b949e;
        background: rgba(139, 148, 158, 0.15);
    }

    .room-players {
        font-size: 0.85rem;
        color: #8b949e;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .player-name {
        color: #c9d1d9;
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

    /* Debug mode toggle */
    .debug-toggle {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        user-select: none;
    }

    .debug-toggle input {
        position: absolute;
        opacity: 0;
        width: 0;
        height: 0;
    }

    .toggle-label {
        font-size: 0.75rem;
        color: #8b949e;
    }

    .toggle-slider {
        position: relative;
        width: 40px;
        height: 20px;
        background: #30363d;
        border-radius: 10px;
        transition: background 0.2s ease;
    }

    .toggle-slider::after {
        content: '';
        position: absolute;
        top: 2px;
        left: 2px;
        width: 16px;
        height: 16px;
        background: #c9d1d9;
        border-radius: 50%;
        transition: transform 0.2s ease;
    }

    .debug-toggle input:checked + .toggle-slider {
        background: #a371f7;
    }

    .debug-toggle input:checked + .toggle-slider::after {
        transform: translateX(20px);
    }

    .debug-toggle input:disabled + .toggle-slider {
        opacity: 0.5;
        cursor: not-allowed;
    }
</style>
