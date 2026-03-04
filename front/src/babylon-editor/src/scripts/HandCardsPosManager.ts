import { Scene } from "@babylonjs/core/scene";
import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import type { IScript } from "babylonjs-editor-tools";
import GameNetworkManagerComponent from "./GameNetworkManagerComponent";
import { cloneMeshWithScripts } from "./cloneWithScripts";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import { Space } from "@babylonjs/core/Maths/math.axis";

const BLUEPRINT_NAME = "UpsideUpCard_BP";

const MAX_RANDOM_ROTATION = 0.08; // ~4.5 degrees in radians
const HAND_LEFT = -153;
const HAND_RIGHT = 246;
const HAND_CENTER = (HAND_LEFT + HAND_RIGHT) / 2;
const HAND_HALF_RANGE = (HAND_RIGHT - HAND_LEFT) / 2;
const Z_ROTATION_LEFT = -20 * Math.PI / 180;
const Z_ROTATION_RIGHT = 20 * Math.PI / 180;
const Y_POSITION = 110;
const Z_POSITION = -452;
const ARC_HEIGHT = 80;
const MAX_HAND_SIZE = 10;

export default class HandCardsPosManager implements IScript {
    private _handMeshes: Mesh[] = [];
    private _baseRotation: Vector3 = Vector3.Zero();

    public constructor(private _scene: Scene) {}

    public onStart(): void {
        const manager = GameNetworkManagerComponent.instance;
        if (!manager) {
            console.warn("HandCardsPosManager: GameNetworkManagerComponent not available");
            return;
        }
        manager.onGameEvent("CardDrawnEvent", this.handleCardDrawn);
        /*
        this.handleCardDrawn({card_id: "1"})
        this.handleCardDrawn({card_id: "2"})
        this.handleCardDrawn({card_id: "3"})
        this.handleCardDrawn({card_id: "4"})
        this.handleCardDrawn({card_id: "5"})
        this.handleCardDrawn({card_id: "6"})
        this.handleCardDrawn({card_id: "7"})
        this.handleCardDrawn({card_id: "8"})
        this.handleCardDrawn({card_id: "9"})
        this.handleCardDrawn({card_id: "10"})
        this.handleCardDrawn({card_id: "11"})
        this.handleCardDrawn({card_id: "12"})
        this.handleCardDrawn({card_id: "13"})
        this.handleCardDrawn({card_id: "14"})
        this.handleCardDrawn({card_id: "15"})
        this.handleCardDrawn({card_id: "16"})
        this.handleCardDrawn({card_id: "17"})
        this.handleCardDrawn({card_id: "18"})
        this.handleCardDrawn({card_id: "19"})
        this.handleCardDrawn({card_id: "20"})
        this.handleCardDrawn({card_id: "21"})
        this.handleCardDrawn({card_id: "22"})
        */
    }

    private handleCardDrawn = (_data: Record<string, unknown>): void => {
        const blueprint = this._scene.getMeshByName(BLUEPRINT_NAME) as Mesh;
        if (!blueprint) {
            console.warn(`HandCardsPosManager: blueprint "${BLUEPRINT_NAME}" not found`);
            return;
        }

        this._baseRotation = blueprint.rotation.clone();

        const clone = cloneMeshWithScripts(blueprint, `hand_card_${this._handMeshes.length}`);
        if (!clone) return;
        clone.setEnabled(true);

        this._handMeshes.push(clone);
        this.repositionHand();
        blueprint.setEnabled(false);
    };

    private repositionHand(): void {
        const n = this._handMeshes.length;
        if (n === 0) return;

        const spreadFactor = Math.min(n - 1, MAX_HAND_SIZE - 1) / (MAX_HAND_SIZE - 1);
        const halfSpan = HAND_HALF_RANGE * spreadFactor;

        for (let i = 0; i < n; i++) {
            const t = n === 1 ? 0.5 : i / (n - 1);
            const xPos = HAND_CENTER - halfSpan + t * halfSpan * 2;
            const zRotation = -1 * (Z_ROTATION_LEFT + t * (Z_ROTATION_RIGHT - Z_ROTATION_LEFT));
            const rotJitter = (Math.random() * 2 - 1) * MAX_RANDOM_ROTATION;

            const mesh = this._handMeshes[i];
            const archOffset = 1 - (2 * t - 1) * (2 * t - 1);
            mesh.position.x = xPos;
            mesh.position.y = Y_POSITION + archOffset * ARC_HEIGHT;
            mesh.position.z = Z_POSITION;
            mesh.rotationQuaternion = null;
            mesh.rotation.copyFrom(this._baseRotation);
            mesh.rotate(Vector3.Up(), zRotation + rotJitter, Space.LOCAL);
            mesh.rotate(Vector3.Forward(), rotJitter, Space.LOCAL);
            mesh.rotate(Vector3.Right(), rotJitter/4, Space.LOCAL);
        }
    }

    public onStop(): void {
        GameNetworkManagerComponent.instance?.offGameEvent("CardDrawnEvent", this.handleCardDrawn);
        for (const mesh of this._handMeshes) mesh.dispose();
        this._handMeshes = [];
    }
}
