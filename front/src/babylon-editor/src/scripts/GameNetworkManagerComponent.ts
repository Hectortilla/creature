import { Scene } from "@babylonjs/core/scene";
import { visibleAsNumber, visibleAsString, visibleAsBoolean, IScript } from "babylonjs-editor-tools";
import { GameConnection } from "./game";

export default class GameInitParamsComponent implements IScript {
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

    public constructor(_scene: Scene) {}

    public onStart(): void {
        if (!this.wsUrl || !this.token || !this.playerId || !this.deckId) {
            console.log("Missing connection params - skipping connection setup");
            return;
        }

        this.initializeConnection();
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
            }
        });
    }

    /** Get the current game connection (if established) */
    public getConnection(): GameConnection | null {
        return this._gameConnection;
    }

    public onStop(): void {
        this._gameConnection?.dispose();
        this._gameConnection = null;
    }
}
