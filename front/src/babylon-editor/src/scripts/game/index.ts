/**
 * Game networking module
 *
 * Provides WebSocket-based game communication that can be used
 * from both Svelte components and Babylon scene scripts.
 */

export { GameConnection } from './GameConnection';
export type {
	ValidAction,
	GameMessage,
	GameConnectionCallbacks,
	GameConnectionOptions,
	ActionData
} from './types';
