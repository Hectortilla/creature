/**
 * GameConnection - Framework-agnostic WebSocket game networking
 *
 * Handles in-game WebSocket communication for the card game.
 * Can be used from both Svelte components and Babylon scene scripts.
 */

import type {
	GameConnectionOptions,
	GameConnectionCallbacks,
	GameMessage,
	ValidAction,
	ActionData
} from './types';

export class GameConnection {
	private ws: WebSocket;
	private playerId: string;
	private callbacks: GameConnectionCallbacks;
	private _validActions: ValidAction[] = [];
	private _messages: GameMessage[] = [];
	private _gameState: Record<string, unknown> | null = null;
	private _connected = false;

	constructor(options: GameConnectionOptions) {
		this.ws = options.ws;
		this.playerId = options.playerId;
		this.callbacks = options.callbacks ?? {};

		this.setupWebSocketHandlers();
	}

	/** Current valid actions for this player */
	get validActions(): ValidAction[] {
		return this._validActions;
	}

	/** All received messages */
	get messages(): GameMessage[] {
		return this._messages;
	}

	/** Current game state */
	get gameState(): Record<string, unknown> | null {
		return this._gameState;
	}

	/** Connection status */
	get connected(): boolean {
		return this._connected;
	}

	private setupWebSocketHandlers(): void {
		// Track initial connection state
		this._connected = this.ws.readyState === WebSocket.OPEN;
		this.callbacks.onConnectionChange?.(this._connected);

		this.ws.addEventListener('open', this.handleOpen);
		this.ws.addEventListener('message', this.handleMessage);
		this.ws.addEventListener('close', this.handleClose);
		this.ws.addEventListener('error', this.handleError);
	}

	private handleOpen = (): void => {
		this._connected = true;
		this.callbacks.onConnectionChange?.(true);
	};

	private handleMessage = (event: MessageEvent): void => {
		const message: GameMessage = JSON.parse(event.data);
		this._messages = [...this._messages, message];
		this.callbacks.onMessage?.(message);

		// Skip failed action results for valid action updates
		if (message.type === 'action_result' && message.data?.success === false) {
			return;
		}

		// Process message types that affect valid actions
		this.processValidActions(message);
		this.processGameState(message);
		this.processGameEvents(message);
	};

	private handleClose = (event: CloseEvent): void => {
		this._connected = false;
		this.callbacks.onConnectionChange?.(false);

		if (event.code === 1008) {
			const reason = event.reason || 'Connection refused';
			this.callbacks.onError?.(reason);
		}
	};

	private handleError = (): void => {
		this._connected = false;
		this.callbacks.onConnectionChange?.(false);
		this.callbacks.onError?.('Connection error');
	};

	private processValidActions(message: GameMessage): void {
		let newActions: ValidAction[] = [];

		// Extract valid actions from different message types
		if (message.type === 'action_result' && message.data?.valid_actions) {
			newActions = message.data.valid_actions as ValidAction[];
		} else if (message.type === 'game_started' && message.data?.valid_actions) {
			newActions = message.data.valid_actions as ValidAction[];
		} else if (message.type === 'valid_actions' && message.data?.actions) {
			newActions = message.data.actions as ValidAction[];
		} else {
			return; // No valid actions in this message
		}

		// Filter to only this player's actions and update
		this._validActions = newActions.filter(
			(action) => action.player_id === this.playerId
		);
		this.callbacks.onValidActionsChange?.(this._validActions);
	}

	private processGameState(message: GameMessage): void {
		if (message.type === 'game_state' && message.data?.state) {
			this._gameState = message.data.state as Record<string, unknown>;
			this.callbacks.onGameStateChange?.(this._gameState);
		} else if (message.type === 'game_started' && message.data?.game_state) {
			this._gameState = message.data.game_state as Record<string, unknown>;
			this.callbacks.onGameStateChange?.(this._gameState);
		} else if (message.type === 'action_result' && message.data?.game_state) {
			this._gameState = message.data.game_state as Record<string, unknown>;
			this.callbacks.onGameStateChange?.(this._gameState);
		}
	}

	private processGameEvents(message: GameMessage): void {
		if (message.type === 'game_started') {
			this.callbacks.onGameStarted?.(message.data);
		}

		if (message.type === 'action_result' && message.data?.game_over) {
			this.callbacks.onGameOver?.(message.data.winner_id as string | null);
		}
	}

	/** Send a game action */
	sendAction(actionData: ActionData): void {
		if (!this._connected || this.ws.readyState !== WebSocket.OPEN) {
			this.callbacks.onError?.('Cannot send action: not connected');
			return;
		}

		this.ws.send(JSON.stringify({ type: 'action', data: actionData }));
	}

	/** Send a raw message (for debugging or custom messages) */
	sendRawMessage(message: Record<string, unknown>): void {
		if (!this._connected || this.ws.readyState !== WebSocket.OPEN) {
			this.callbacks.onError?.('Cannot send message: not connected');
			return;
		}

		this.ws.send(JSON.stringify(message));
	}

	/** Clear all messages */
	clearMessages(): void {
		this._messages = [];
	}

	/** Dispose of the connection and clean up event listeners */
	dispose(): void {
		this.ws.removeEventListener('open', this.handleOpen);
		this.ws.removeEventListener('message', this.handleMessage);
		this.ws.removeEventListener('close', this.handleClose);
		this.ws.removeEventListener('error', this.handleError);

		this._validActions = [];
		this._messages = [];
		this._gameState = null;
		this._connected = false;
	}
}
