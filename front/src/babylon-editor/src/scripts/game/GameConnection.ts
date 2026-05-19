/**
 * GameConnection — IScript singleton that owns the WebSocket, GameStateStore,
 * and CardDefinitionCache. Emits raw GameMessage to a registered handler
 * without any interpretation or routing.
 */

import type { Scene } from '@babylonjs/core/scene';
import { visibleAsNumber, visibleAsString, visibleAsBoolean } from 'babylonjs-editor-tools';
import type { IScript } from 'babylonjs-editor-tools';

import { CardDefinitionCache } from './CardDefinitionCache';
import { GameStateStore } from '../state/GameStateStore';
import type { GameMessage, ActionData } from './types';

function buildWebSocketUrl(wsUrl: string, token: string, deckId: number, roomId?: string): string {
	let url = `${wsUrl}/game/ws?token=${encodeURIComponent(token)}&deck_id=${deckId}`;
	if (roomId) url += `&room_id=${encodeURIComponent(roomId)}`;
	return url;
}

export default class GameConnection implements IScript {
	static instance: GameConnection | null = null;

	@visibleAsString('WebSocket URL')
	public wsUrl = '';

	@visibleAsString('Token')
	public token = '';

	@visibleAsString('Player ID')
	public playerId = '';

	@visibleAsNumber('Deck ID')
	public deckId = 0;

	@visibleAsString('Room ID')
	public roomId = '';

	@visibleAsBoolean('Create Room')
	public createRoom = false;

	private _ws: WebSocket | null = null;
	private _connected = false;
	private _cardCache: CardDefinitionCache | null = null;
	private _stateStore: GameStateStore | null = null;

	/** Registered by BoardController to receive every raw message. */
	public onMessage: ((message: GameMessage) => void) | null = null;

	public constructor(_scene: Scene) {}

	// ── IScript lifecycle ───────────────────────────────────────────

	public onStart(): void {
		GameConnection.instance = this;

		if (!this.wsUrl || !this.token || !this.playerId || !this.deckId) {
			console.log('GameConnection: missing params — skipping connection');
			return;
		}

		this._cardCache = CardDefinitionCache.getOrCreate();
		this._cardCache.initialize(this.wsUrl, this.token);
		this._stateStore = GameStateStore.getOrCreate(this.playerId);

		const url = buildWebSocketUrl(this.wsUrl, this.token, this.deckId, this.roomId || undefined);
		this._ws = new WebSocket(url);

		this._ws.addEventListener('open', this._handleOpen);
		this._ws.addEventListener('message', this._handleMessage);
		this._ws.addEventListener('close', this._handleClose);
		this._ws.addEventListener('error', this._handleError);
	}

	public onUpdate(): void {}

	public onStop(): void {
		if (this._ws) {
			this._ws.removeEventListener('open', this._handleOpen);
			this._ws.removeEventListener('message', this._handleMessage);
			this._ws.removeEventListener('close', this._handleClose);
			this._ws.removeEventListener('error', this._handleError);
			this._ws.close();
			this._ws = null;
		}

		this._cardCache?.dispose();
		this._cardCache = null;
		this._stateStore?.dispose();
		this._stateStore = null;
		this._connected = false;
		this.onMessage = null;
		GameConnection.instance = null;
	}

	// ── Public API ──────────────────────────────────────────────────

	get connected(): boolean {
		return this._connected;
	}

	getStateStore(): GameStateStore | null {
		return this._stateStore;
	}

	getCardCache(): CardDefinitionCache | null {
		return this._cardCache;
	}

	sendAction(actionData: ActionData): void {
		if (!this._connected || !this._ws || this._ws.readyState !== WebSocket.OPEN) {
			console.warn('GameConnection: cannot send action — not connected');
			return;
		}
		this._ws.send(JSON.stringify({ type: 'action', data: actionData }));
	}

	sendRawMessage(message: Record<string, unknown>): void {
		if (!this._connected || !this._ws || this._ws.readyState !== WebSocket.OPEN) {
			console.warn('GameConnection: cannot send message — not connected');
			return;
		}
		this._ws.send(JSON.stringify(message));
	}

	// ── WebSocket handlers (no interpretation, just forward) ────────

	private _handleOpen = (): void => {
		this._connected = true;
	};

	private _handleMessage = (event: MessageEvent): void => {
		const message: GameMessage = JSON.parse(event.data);
		this.onMessage?.(message);
	};

	private _handleClose = (event: CloseEvent): void => {
		this._connected = false;
		if (event.code === 1008) {
			console.error('GameConnection: refused —', event.reason || 'unknown reason');
		}
	};

	private _handleError = (): void => {
		this._connected = false;
		console.error('GameConnection: WebSocket error');
	};
}
