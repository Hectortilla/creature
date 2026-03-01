import { Scene } from "@babylonjs/core/scene";
import { visibleAsNumber, visibleAsString, visibleAsBoolean } from "babylonjs-editor-tools";
import type { IScript } from "babylonjs-editor-tools";
import { GameConnection } from "./game";
import type { GameMessage, ValidAction } from "./game";

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
    private _listeners = new Map<keyof GameEventMap, Set<GameEventCallback<any>>>();

    public constructor(_scene: Scene) {}

    public onStart(): void {
        GameNetworkManagerComponent.instance = this;

        if (!this.wsUrl || !this.token || !this.playerId || !this.deckId) {
            console.log("Missing connection params - skipping connection setup");
            return;
        }

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
                onValidActionsChange: (actions) => this.emit("validActionsChange", actions),
                onGameStateChange: (state) => this.emit("gameStateChange", state),
                onConnectionChange: (connected) => this.emit("connectionChange", connected),
                onError: (error) => this.emit("error", error),
                onGameStarted: (data) => this.emit("gameStarted", data),
                onGameOver: (winnerId) => this.emit("gameOver", winnerId),
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

    public getConnection(): GameConnection | null {
        return this._gameConnection;
    }

    public onStop(): void {
        this._gameConnection?.dispose();
        this._gameConnection = null;
        this._listeners.clear();
        GameNetworkManagerComponent.instance = null;
    }
}
