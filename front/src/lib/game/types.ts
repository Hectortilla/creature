/**
 * Game networking types
 *
 * Types specific to the game networking module.
 * Reuses generated types from the API client where possible.
 */

import type { ActionData } from '$lib/api/types.gen';

/**
 * A valid action that a player can perform.
 * Includes the action type and player_id for filtering.
 */
export interface ValidAction {
	action: string;
	player_id: string;
	[key: string]: unknown;
}

/**
 * Generic game message received from WebSocket.
 * The `type` field determines the message kind, `data` contains the payload.
 */
export interface GameMessage {
	type: string;
	data: Record<string, unknown>;
}

/**
 * Callbacks for GameConnection events.
 * All callbacks are optional - implement only what you need.
 */
export interface GameConnectionCallbacks {
	/** Called when a message is received */
	onMessage?: (message: GameMessage) => void;

	/** Called when valid actions are updated */
	onValidActionsChange?: (actions: ValidAction[]) => void;

	/** Called when game state changes */
	onGameStateChange?: (state: Record<string, unknown> | null) => void;

	/** Called when connection status changes */
	onConnectionChange?: (connected: boolean) => void;

	/** Called on connection error */
	onError?: (error: string) => void;

	/** Called when game starts */
	onGameStarted?: (data: Record<string, unknown>) => void;

	/** Called when game ends */
	onGameOver?: (winnerId: string | null) => void;
}

/**
 * Options for creating a GameConnection instance.
 */
export interface GameConnectionOptions {
	/** WebSocket instance to use for communication */
	ws: WebSocket;

	/** Current player's user ID for filtering valid actions */
	playerId: string;

	/** Event callbacks */
	callbacks?: GameConnectionCallbacks;
}

// Re-export ActionData for convenience
export type { ActionData };
