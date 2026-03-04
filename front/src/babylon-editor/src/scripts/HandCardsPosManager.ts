import { Scene } from "@babylonjs/core/scene";
import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import type { IScript } from "babylonjs-editor-tools";
import GameNetworkManagerComponent from "./GameNetworkManagerComponent";
import { cloneMeshWithScripts } from "./cloneWithScripts";
import { Quaternion, Vector3 } from "@babylonjs/core/Maths/math.vector";
import { Space } from "@babylonjs/core/Maths/math.axis";

// --- Blueprint ---
const BLUEPRINT_NAME = "UpsideUpCard_BP";

// --- Hand Layout ---
const MAX_HAND_SIZE = 10;
const HAND_LEFT = -153;
const HAND_RIGHT = 246;
const HAND_CENTER = (HAND_LEFT + HAND_RIGHT) / 2;
const HAND_HALF_RANGE = (HAND_RIGHT - HAND_LEFT) / 2;
const Y_POSITION = 110;
const Z_POSITION = -452;
const ARC_HEIGHT = 80;

// --- Rotation ---
const BASE_ROTATION = Quaternion.FromEulerAngles(1.1538920574673148, Math.PI, -Math.PI);
const Z_ROTATION_LEFT = (-20 * Math.PI) / 180;
const Z_ROTATION_RIGHT = (20 * Math.PI) / 180;
const MAX_JITTER = 0.08; // ~4.5 degrees

export default class HandCardsPosManager implements IScript {
    private _handMeshes: Mesh[] = [];

    public constructor(private _scene: Scene) {}

    public onStart(): void {
        const manager = GameNetworkManagerComponent.instance;
        if (!manager) {
            console.warn("HandCardsPosManager: GameNetworkManagerComponent not available");
            return;
        }
        manager.onGameEvent("CardDrawnEvent", this.handleCardDrawn);

        // /*
        for (let i = 1; i <= 22; i++) this.handleCardDrawn({ card_id: String(i) });
        // */
    }

    private handleCardDrawn = (_data: Record<string, unknown>): void => {
        const blueprint = this._scene.getMeshByName(BLUEPRINT_NAME) as Mesh;
        if (!blueprint) {
            console.warn(`HandCardsPosManager: blueprint "${BLUEPRINT_NAME}" not found`);
            return;
        }

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
            this.positionCard(this._handMeshes[i], i, n, halfSpan);
        }
    }

    private positionCard(mesh: Mesh, index: number, total: number, halfSpan: number): void {
        const t = total === 1 ? 0.5 : index / (total - 1);
        const jitter = (Math.random() * 2 - 1) * MAX_JITTER;
        const archOffset = 1 - (2 * t - 1) ** 2;

        mesh.position.x = HAND_CENTER - halfSpan + t * halfSpan * 2;
        mesh.position.y = Y_POSITION + archOffset * ARC_HEIGHT;
        mesh.position.z = Z_POSITION;

        const fanAngle = -(Z_ROTATION_LEFT + t * (Z_ROTATION_RIGHT - Z_ROTATION_LEFT));
        mesh.rotationQuaternion = BASE_ROTATION.clone();
        mesh.rotate(Vector3.Up(), fanAngle + jitter, Space.LOCAL);
        mesh.rotate(Vector3.Forward(), jitter, Space.LOCAL);
        mesh.rotate(Vector3.Right(), jitter / 4, Space.LOCAL);
    }

    public onStop(): void {
        GameNetworkManagerComponent.instance?.offGameEvent("CardDrawnEvent", this.handleCardDrawn);
        for (const mesh of this._handMeshes) mesh.dispose();
        this._handMeshes = [];
    }
}
