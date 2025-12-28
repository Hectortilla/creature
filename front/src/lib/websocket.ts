/**
 * Type-safe WebSocket wrapper for game communication
 * 
 * This wrapper provides type safety for WebSocket messages using
 * the types generated from the OpenAPI schema.
 */

// Import types once they're generated (will be available after running generate-client)
// For now, we'll use a generic approach that will work once types are generated

type ClientMessageType =
	| 'create_game'
	| 'join_game'
	| 'list_rooms'
	| 'start_game'
	| 'action'
	| 'get_state'
	| 'get_valid_actions'
	| 'leave_game'
	| 'ping';

type ServerMessageType =
	| 'connected'
	| 'game_created'
	| 'game_joined'
	| 'player_joined'
	| 'player_left'
	| 'game_started'
	| 'game_state'
	| 'action_result'
	| 'valid_actions'
	| 'rooms_list'
	| 'game_left'
	| 'error'
	| 'pong';

type ClientMessage = {
	type: ClientMessageType;
	data?: Record<string, unknown>;
};

type ServerMessage = {
	type: ServerMessageType;
	data?: Record<string, unknown>;
};

type MessageHandler<T extends ServerMessageType> = (message: Extract<ServerMessage, { type: T }>) => void;

export class GameWebSocket {
	private ws: WebSocket | null = null;
	private messageHandlers: Map<ServerMessageType, MessageHandler<ServerMessageType>[]> = new Map();
	private connectionHandlers: {
		onOpen?: () => void;
		onClose?: (event: CloseEvent) => void;
		onError?: (error: Event) => void;
	} = {};

	/**
	 * Connect to the game WebSocket server
	 */
	connect(url: string): void {
		if (this.ws && this.ws.readyState === WebSocket.OPEN) {
			console.warn('WebSocket already connected');
			return;
		}

		this.ws = new WebSocket(url);

		this.ws.onopen = () => {
			console.log('WebSocket connected');
			this.connectionHandlers.onOpen?.();
		};

		this.ws.onmessage = (event) => {
			try {
				const message: ServerMessage = JSON.parse(event.data);
				const handlers = this.messageHandlers.get(message.type);
				if (handlers) {
					handlers.forEach((handler) => handler(message as any));
				}
				// Also call generic handler if registered
				const genericHandlers = this.messageHandlers.get('*' as ServerMessageType);
				if (genericHandlers) {
					genericHandlers.forEach((handler) => handler(message as any));
				}
			} catch (error) {
				console.error('Failed to parse WebSocket message:', error);
			}
		};

		this.ws.onclose = (event) => {
			console.log('WebSocket closed', event.code, event.reason);
			this.connectionHandlers.onClose?.(event);
			this.ws = null;
		};

		this.ws.onerror = (error) => {
			console.error('WebSocket error:', error);
			this.connectionHandlers.onError?.(error);
		};
	}

	/**
	 * Send a message to the server
	 */
	send(message: ClientMessage): void {
		if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
			console.warn('WebSocket is not connected');
			return;
		}
		this.ws.send(JSON.stringify(message));
	}

	/**
	 * Register a handler for a specific message type
	 */
	on<T extends ServerMessageType>(type: T, handler: MessageHandler<T>): void {
		if (!this.messageHandlers.has(type)) {
			this.messageHandlers.set(type, []);
		}
		this.messageHandlers.get(type)!.push(handler as MessageHandler<ServerMessageType>);
	}

	/**
	 * Unregister a handler for a specific message type
	 */
	off<T extends ServerMessageType>(type: T, handler: MessageHandler<T>): void {
		const handlers = this.messageHandlers.get(type);
		if (handlers) {
			const index = handlers.indexOf(handler as MessageHandler<ServerMessageType>);
			if (index > -1) {
				handlers.splice(index, 1);
			}
		}
	}

	/**
	 * Register connection event handlers
	 */
	onOpen(handler: () => void): void {
		this.connectionHandlers.onOpen = handler;
	}

	onClose(handler: (event: CloseEvent) => void): void {
		this.connectionHandlers.onClose = handler;
	}

	onError(handler: (error: Event) => void): void {
		this.connectionHandlers.onError = handler;
	}

	/**
	 * Close the WebSocket connection
	 */
	close(): void {
		if (this.ws) {
			this.ws.close();
			this.ws = null;
		}
	}

	/**
	 * Check if the WebSocket is connected
	 */
	isConnected(): boolean {
		return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
	}

	/**
	 * Get the current ready state
	 */
	getReadyState(): number | null {
		return this.ws?.readyState ?? null;
	}
}

/**
 * Helper functions to create typed messages
 */
export const createGameMessages = {
	createGame: (): ClientMessage => ({ type: 'create_game', data: {} }),
	joinGame: (roomId: string): ClientMessage => ({ type: 'join_game', data: { room_id: roomId } }),
	listRooms: (): ClientMessage => ({ type: 'list_rooms', data: {} }),
	startGame: (): ClientMessage => ({ type: 'start_game', data: {} }),
	action: (actionData: Record<string, unknown>): ClientMessage => ({ type: 'action', data: actionData }),
	getState: (): ClientMessage => ({ type: 'get_state', data: {} }),
	getValidActions: (): ClientMessage => ({ type: 'get_valid_actions', data: {} }),
	leaveGame: (): ClientMessage => ({ type: 'leave_game', data: {} }),
	ping: (): ClientMessage => ({ type: 'ping', data: {} }),
};

