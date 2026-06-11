<script lang="ts">
	import type { DeckReadSummary, RoomSummary } from '$lib/types';

	interface Props {
		decks: DeckReadSummary[];
		rooms: RoomSummary[];
		selectedDeckId: number | null;
		selectedRoomId: string | null;
		createNewRoom: boolean;
		loadingRooms: boolean;
		connectionError: string | null;
		onDeckSelect: (deckId: number | null) => void;
		onRoomSelect: (roomId: string | null) => void;
		onCreateNewRoomChange: (value: boolean) => void;
		onRefreshRooms: () => void;
		onConnect: () => void;
	}

	let {
		decks,
		rooms,
		selectedDeckId,
		selectedRoomId,
		createNewRoom,
		loadingRooms,
		connectionError,
		onDeckSelect,
		onRoomSelect,
		onCreateNewRoomChange,
		onRefreshRooms,
		onConnect
	}: Props = $props();

	// Deck buttons are server-rendered; until hydration attaches onclick, a
	// click is a silent no-op — keep them disabled so it can't happen.
	let hydrated = $state(false);
	$effect(() => {
		hydrated = true;
	});
</script>

<div class="lobby-selector">
	{#if connectionError}
		<div class="error-banner">{connectionError}</div>
	{/if}

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
								onDeckSelect(deck.id);
							}
						}}
						disabled={!hydrated || !deck.is_valid_for_playing}
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
						onCreateNewRoomChange(true);
						onRoomSelect(null);
					}}
				>
					<span class="room-option-icon">➕</span>
					<span class="room-option-text">Create New Room</span>
				</button>
				<button
					class="room-option"
					class:selected={!createNewRoom}
					onclick={() => onCreateNewRoomChange(false)}
				>
					<span class="room-option-icon">🔍</span>
					<span class="room-option-text">Join Existing Room</span>
				</button>
			</div>

			{#if !createNewRoom}
				<div class="rooms-section">
					<div class="rooms-header">
						<h3>Available Rooms</h3>
						<button class="refresh-btn" onclick={onRefreshRooms} disabled={loadingRooms}>
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
											onRoomSelect(room.room_id);
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
				onclick={onConnect}
				disabled={!selectedDeckId || (!createNewRoom && !selectedRoomId)}
			>
				{createNewRoom ? 'Create Room & Play' : 'Join Room & Play'}
			</button>
		</div>
	{/if}
</div>

<style>
	.lobby-selector {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.error-banner {
		padding: 0.75rem 1rem;
		background: rgba(248, 81, 73, 0.15);
		border: 1px solid #f85149;
		border-radius: 8px;
		color: #f85149;
		font-size: 0.85rem;
	}

	.deck-selection,
	.room-selection {
		padding: 1.5rem;
		background: #161b22;
		border-radius: 8px;
		border: 1px solid #30363d;
	}

	.deck-selection h2,
	.room-selection h2 {
		margin: 0 0 1rem 0;
		font-size: 1.25rem;
		color: #c9d1d9;
	}

	.no-decks,
	.no-rooms {
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

	.deck-list,
	.room-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		margin-bottom: 1rem;
	}

	.deck-item,
	.room-item {
		padding: 1rem;
		background: #0d1117;
		border: 2px solid #30363d;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s ease;
		text-align: left;
		width: 100%;
		font-family: inherit;
		color: #c9d1d9;
	}

	.deck-item:hover:not(:disabled),
	.room-item:hover:not(:disabled) {
		border-color: #58a6ff;
		background: #161b22;
	}

	.deck-item.selected,
	.room-item.selected {
		border-color: #3fb950;
		background: rgba(63, 185, 80, 0.1);
	}

	.deck-item.invalid,
	.room-item.cannot-join {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.deck-item:disabled,
	.room-item:disabled {
		cursor: not-allowed;
		opacity: 0.6;
	}

	.deck-info,
	.room-info {
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

	.status-badge.full,
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
</style>
