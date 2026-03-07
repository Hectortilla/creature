import { Scene } from "@babylonjs/core/scene";
import { visibleAsNumber, visibleAsString, visibleAsBoolean } from "babylonjs-editor-tools";
import type { IScript } from "babylonjs-editor-tools";
import { GameConnection, CardDefinitionCache } from "./game";
import type { GameMessage, ValidAction } from "./game";
import { GameStateStore } from "./state/GameStateStore";

export interface GameEventMap {
    message: GameMessage;
    gameStarted: Record<string, unknown>;
    gameOver: string | null;
    gameStateChange: Record<string, unknown> | null;
    validActionsChange: ValidAction[];
    connectionChange: boolean;
    error: string;
}

type GameEventCallback<K extends keyof GameEventMap> = (data: GameEventMap[K]) => void;
type GameEventListenerCallback = (data: Record<string, unknown>) => void;

export default class GameNetworkManagerComponent implements IScript {
    static instance: GameNetworkManagerComponent | null = null;

    @visibleAsString("WebSocket URL")
    public wsUrl: string = "";

    @visibleAsString("Token")
    public token: string = "";

    @visibleAsString("Player ID")
    public playerId: string = "";

    @visibleAsNumber("Deck ID")
    public deckId: number = 0;

    @visibleAsString("Room ID")
    public roomId: string = "";

    @visibleAsBoolean("Create Room")
    public createRoom: boolean = false;

    private _gameConnection: GameConnection | null = null;
    private _cardCache: CardDefinitionCache | null = null;
    private _stateStore: GameStateStore | null = null;
    private _listeners = new Map<keyof GameEventMap, Set<GameEventCallback<any>>>();
    private _gameEventListeners = new Map<string, Set<GameEventListenerCallback>>();

    public constructor(_scene: Scene) {}

    public onStart(): void {
        GameNetworkManagerComponent.instance = this;

        if (!this.wsUrl || !this.token || !this.playerId || !this.deckId) {
            console.log("Missing connection params - skipping connection setup");
            return;
        }

        this._cardCache = CardDefinitionCache.getOrCreate();
        this._cardCache.initialize(this.wsUrl, this.token);
        this._stateStore = GameStateStore.getOrCreate(this.playerId);

        this.initializeConnection();
    }

    private emit<K extends keyof GameEventMap>(event: K, data: GameEventMap[K]): void {
        const listeners = this._listeners.get(event);
        if (!listeners) return;
        for (const cb of listeners) cb(data);
    }

    private emitGameEvent(eventType: string, data: Record<string, unknown>): void {
        const listeners = this._gameEventListeners.get(eventType);
        if (!listeners) return;
        for (const cb of listeners) cb(data);
    }

    private initializeConnection(): void {
        console.log("Connecting to game server...");

        this._gameConnection = new GameConnection({
            wsUrl: this.wsUrl,
            token: this.token,
            deckId: this.deckId,
            roomId: this.roomId || undefined,
            playerId: this.playerId,
            callbacks: {
                onMessage: (msg) => this.emit("message", msg),
                onConnectionChange: (connected) => this.emit("connectionChange", connected),
                onError: (error) => this.emit("error", error),
                onGameOver: (winnerId) => this.emit("gameOver", winnerId),
                onGameStarted: (data) => {
                    this._stateStore?.processGameStarted(data);
                    this.emit("gameStarted", data);
                },
                onGameEvents: (events) => {
                    this._stateStore?.processGameEvents(events);
                    for (const event of events) {
                        this.registerCardFromEvent(event);
                        const eventType = event.event_type as string;
                        if (eventType) this.emitGameEvent(eventType, event);
                    }
                },
                onGameStateChange: (state) => {
                    if (state) this._stateStore?.processGameState(state);
                    this.emit("gameStateChange", state);
                },
                onValidActionsChange: (actions) => {
                    this._stateStore?.updateValidActions(actions);
                    this.emit("validActionsChange", actions);
                },
            }
        });
    }

    public on<K extends keyof GameEventMap>(event: K, callback: GameEventCallback<K>): void {
        if (!this._listeners.has(event)) {
            this._listeners.set(event, new Set());
        }
        this._listeners.get(event)!.add(callback);
    }

    public off<K extends keyof GameEventMap>(event: K, callback: GameEventCallback<K>): void {
        this._listeners.get(event)?.delete(callback);
    }

    public onGameEvent(eventType: string, callback: GameEventListenerCallback): void {
        if (!this._gameEventListeners.has(eventType)) {
            this._gameEventListeners.set(eventType, new Set());
        }
        this._gameEventListeners.get(eventType)!.add(callback);
    }

    public offGameEvent(eventType: string, callback: GameEventListenerCallback): void {
        this._gameEventListeners.get(eventType)?.delete(callback);
    }

    private registerCardFromEvent(event: Record<string, unknown>): void {
        const instanceId = event.instance_id as string | undefined;
        const cardId = event.card_id as number | undefined;
        if (instanceId && cardId && cardId > 0) {
            this._cardCache?.registerInstance(instanceId, cardId);
        }
    }

    public getConnection(): GameConnection | null {
        return this._gameConnection;
    }

    public getCardCache(): CardDefinitionCache | null {
        return this._cardCache;
    }

    public getStateStore(): GameStateStore | null {
        return this._stateStore;
    }

    public onStop(): void {
        this._gameConnection?.dispose();
        this._gameConnection = null;
        this._cardCache?.dispose();
        this._cardCache = null;
        this._stateStore?.dispose();
        this._stateStore = null;
        this._listeners.clear();
        this._gameEventListeners.clear();
        GameNetworkManagerComponent.instance = null;
    }
}
