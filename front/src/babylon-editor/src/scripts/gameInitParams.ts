import { visibleAsNumber, visibleAsString, visibleAsBoolean } from "babylonjs-editor-tools";

export default class GameInitParamsComponent {
    @visibleAsNumber("Deck ID")
    public deckId: number | null = null;

    @visibleAsString("Room ID")
    public roomId: string | null = null;

    @visibleAsBoolean("Create Room")
    public createRoom: boolean = false;

    public constructor() {}

    public onStart(): void {
        console.log("Deck ID:", this.deckId);
        console.log("Room ID:", this.roomId);
        console.log("Create Room:", this.createRoom);
    }
}
