import { Scene } from "@babylonjs/core/scene";
import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import type { IScript } from "babylonjs-editor-tools";
import GameNetworkManagerComponent from "./GameNetworkManagerComponent";

const BLUEPRINT_NAME = "UpsideDownCard_BP";
const CARD_STACK_Y_OFFSET = 1.5;
const MAX_RANDOM_ROTATION = 0.08; // ~4.5 degrees in radians

interface CardSnapshot {
    instance_id: string;
    owner_id: string;
    zone: string;
}

export default class CardsInitializer implements IScript {
    private _deckMeshes: Mesh[] = [];

    public constructor(private _scene: Scene) {}

    public onStart(): void {
        const manager = GameNetworkManagerComponent.instance;
        if (!manager) {
            console.warn("CardsInitializer: GameNetworkManagerComponent not available");
            return;
        }
        manager.on("gameStarted", this.handleGameStarted);
    }

    private handleGameStarted = (data: Record<string, unknown>): void => {
        const gameState = data.game_state as Record<string, unknown>;
        const total_cards = gameState.total_cards as number;
        const blueprint = this._scene.getMeshByName(BLUEPRINT_NAME) as Mesh;
        if (!blueprint) {
            throw new Error(`CardsInitializer: blueprint mesh "${BLUEPRINT_NAME}" not found`);
        }
        for (let i = 0; i < total_cards; i++) {
            const clone = blueprint.clone(`deck_card_${total_cards}`);
            if (!clone) continue;
            clone.position = blueprint.position.clone();
            clone.position.y += i * CARD_STACK_Y_OFFSET;
            clone.rotation = blueprint.rotation.clone();
            clone.rotation.y += (Math.random() * 2 - 1) * MAX_RANDOM_ROTATION;
            this._deckMeshes.push(clone);
        }
        // Keep blueprint hidden but available as a template for future cloning
        blueprint.setEnabled(false);
        console.log(`CardsInitializer: spawned ${this._deckMeshes.length} deck cards`);
    };

    public onStop(): void {
        GameNetworkManagerComponent.instance?.off("gameStarted", this.handleGameStarted);
        for (const mesh of this._deckMeshes) mesh.dispose();
        this._deckMeshes = [];
    }
}
