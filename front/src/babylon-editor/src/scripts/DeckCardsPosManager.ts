import { Scene } from "@babylonjs/core/scene";
import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import type { IScript } from "babylonjs-editor-tools";
import GameNetworkManagerComponent from "./GameNetworkManagerComponent";
import { cloneMeshWithScripts } from "./cloneWithScripts";

// --- Blueprint ---
const BLUEPRINT_NAME = "UpsideDownCard_BP";

// --- Stack Layout ---
const CARD_STACK_Y_OFFSET = 1.5;
const MAX_JITTER = 0.08; // ~4.5 degrees

export default class DeckInstanciator implements IScript {
    private _deckMeshes: Mesh[] = [];

    public constructor(private _scene: Scene) {}

    public onStart(): void {
        const manager = GameNetworkManagerComponent.instance;
        if (!manager) {
            console.warn("DeckInstanciator: GameNetworkManagerComponent not available");
            return;
        }
        manager.on("gameStarted", this.handleGameStarted);
    }

    private handleGameStarted = (data: Record<string, unknown>): void => {
        const blueprint = this._scene.getMeshByName(BLUEPRINT_NAME) as Mesh;
        if (!blueprint) {
            throw new Error(`DeckInstanciator: blueprint mesh "${BLUEPRINT_NAME}" not found`);
        }

        const totalCards = (data.game_state as Record<string, unknown>).total_cards as number;

        for (let i = 0; i < totalCards; i++) {
            const clone = cloneMeshWithScripts(blueprint, `deck_card_${i}`);
            if (!clone) continue;

            clone.setEnabled(true);
            clone.position = blueprint.position.clone();
            clone.position.y += i * CARD_STACK_Y_OFFSET;
            clone.rotation = blueprint.rotation.clone();
            clone.rotation.y += (Math.random() * 2 - 1) * MAX_JITTER;
            this._deckMeshes.push(clone);
        }

        blueprint.setEnabled(false);
        console.log(`DeckInstanciator: spawned ${this._deckMeshes.length} deck cards`);
    };

    public onStop(): void {
        GameNetworkManagerComponent.instance?.off("gameStarted", this.handleGameStarted);
        for (const mesh of this._deckMeshes) mesh.dispose();
        this._deckMeshes = [];
    }
}
