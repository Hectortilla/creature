/**
 * Game networking module
 *
 * Provides WebSocket-based game communication that can be used
 * from both Svelte components and Babylon scene scripts.
 */

export { GameConnection } from './GameConnection';
export { CardDefinitionCache } from './CardDefinitionCache';
export type { CardDefinition } from './CardDefinitionCache';
export type {
	ValidAction,
	GameMessage,
	GameConnectionCallbacks,
	GameConnectionOptions,
	ActionData
} from './types';
