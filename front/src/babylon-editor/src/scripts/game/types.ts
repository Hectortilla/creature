/**
 * Game networking types
 *
 * Types specific to the game networking module.
 */

/**
 * Action data sent to the game server.
 * Flexible interface allowing any action-specific fields.
 */
export interface ActionData {
	action_type: string;
	[key: string]: unknown;
}

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

