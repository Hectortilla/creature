import { Scene } from "@babylonjs/core/scene";
import { visibleAsNumber, visibleAsString, visibleAsBoolean } from "babylonjs-editor-tools";
import type { IScript } from "babylonjs-editor-tools";
import { GameConnection } from "./GameConnection";
import { CardDefinitionCache } from "./CardDefinitionCache";
import type { GameMessage } from "./types";
import { GameStateStore } from "../state/GameStateStore";

export interface GameEventMap {
    message: GameMessage;
    gameOver: string | null;
    connectionChange: boolean;
    error: string;
}

type GameEventCallback<K extends keyof GameEventMap> = (data: GameEventMap[K]) => void;

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
                },
                onGameEvents: (events) => {
                    this._stateStore?.processGameEvents(events);
                    for (const event of events) this.registerCardFromEvent(event);
                },
                onGameStateChange: (state) => {
                    if (state) this._stateStore?.processGameState(state);
                },
                onValidActionsChange: (actions) => {
                    this._stateStore?.updateValidActions(actions);
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
        GameNetworkManagerComponent.instance = null;
    }
}
