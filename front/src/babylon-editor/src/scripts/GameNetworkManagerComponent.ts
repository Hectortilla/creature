import { Scene } from "@babylonjs/core/scene";
import { visibleAsNumber, visibleAsString, visibleAsBoolean, IScript } from "babylonjs-editor-tools";
import { GameConnection, type GameConnectionCallbacks } from "./game";
import type { GameConnectionParams } from "../App";

export default class GameInitParamsComponent implements IScript {
    @visibleAsNumber("Deck ID")
    public deckId: number | null = null;

    @visibleAsString("Room ID")
    public roomId: string | null = null;

    @visibleAsBoolean("Create Room")
    public createRoom: boolean = false;

    private _scene: Scene;
    private _gameConnection: GameConnection | null = null;
    private _ws: WebSocket | null = null;

    public constructor(scene: Scene) {
        this._scene = scene;
    }

    public onStart(): void {
        console.log("Deck ID:", this.deckId);
        console.log("Room ID:", this.roomId);
        console.log("Create Room:", this.createRoom);

        // Read connection params from scene metadata (set by App.init())
        const params = this._scene.metadata?.gameConnection as GameConnectionParams | undefined;
        if (!params) {
            console.log("No game connection params provided - skipping connection setup");
            return;
        }

        this.initializeConnection(params);
    }

    private initializeConnection(params: GameConnectionParams): void {
        // Build WebSocket URL
        let wsPath = `${params.wsUrl}/game/ws?token=${encodeURIComponent(params.token)}&deck_id=${params.deckId}`;
        if (params.roomId) {
            wsPath += `&room_id=${encodeURIComponent(params.roomId)}`;
        }

        console.log("Connecting to game server...");
        this._ws = new WebSocket(wsPath);

        this._ws.onopen = () => {
            const callbacks: GameConnectionCallbacks = {
                onMessage: (msg) => {
                    console.log("Game message:", msg.type, msg.data);
                },
                onValidActionsChange: (actions) => {
                    console.log("Valid actions updated:", actions.length, "actions available");
                },
                onGameStateChange: (state) => {
                    console.log("Game state updated:", state);
                },
                onConnectionChange: (connected) => {
                    console.log("Connection status:", connected ? "connected" : "disconnected");
                },
                onError: (error) => {
                    console.error("Game connection error:", error);
                },
                onGameStarted: (data) => {
                    console.log("Game started:", data);
                },
                onGameOver: (winnerId) => {
                    console.log("Game over! Winner:", winnerId);
                }
            };

            this._gameConnection = new GameConnection({
                ws: this._ws!,
                playerId: params.playerId,
                callbacks
            });

            console.log("Game connection established");
        };

        this._ws.onerror = () => {
            console.error("WebSocket connection error");
        };

        this._ws.onclose = (event) => {
            console.log("WebSocket closed:", event.code, event.reason);
            this._gameConnection?.dispose();
            this._gameConnection = null;
        };
    }

    /** Get the current game connection (if established) */
    public getConnection(): GameConnection | null {
        return this._gameConnection;
    }

    public onStop(): void {
        this._gameConnection?.dispose();
        this._ws?.close();
        this._gameConnection = null;
        this._ws = null;
    }
}
