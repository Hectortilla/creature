import type { Mesh } from '@babylonjs/core/Meshes/mesh';
import type { Scene } from '@babylonjs/core/scene';
import { CardEntity } from './CardEntity';
import type { ClientCard, Zone } from '../game/models';
import { cloneMeshWithScripts } from '../cloneWithScripts';

export class CardEntityManager {
	static instance: CardEntityManager | null = null;

	private _entities = new Map<string, CardEntity>();
	private _meshToEntity = new Map<Mesh, CardEntity>();
	private _scene: Scene;

	private _faceUpBlueprint: Mesh | null = null;
	private _faceDownBlueprint: Mesh | null = null;

	private constructor(scene: Scene) {
		this._scene = scene;
	}

	static getOrCreate(scene: Scene): CardEntityManager {
		if (!CardEntityManager.instance) {
			CardEntityManager.instance = new CardEntityManager(scene);
		}
		return CardEntityManager.instance;
	}

	// ── Blueprint Management ─────────────────────────────────────────

	initBlueprints(faceUpName: string, faceDownName: string): void {
		this._faceUpBlueprint = this._scene.getMeshByName(faceUpName) as Mesh | null;
		this._faceDownBlueprint = this._scene.getMeshByName(faceDownName) as Mesh | null;

		if (!this._faceUpBlueprint) {
			console.warn(`CardEntityManager: face-up blueprint "${faceUpName}" not found`);
		}
		if (!this._faceDownBlueprint) {
			console.warn(`CardEntityManager: face-down blueprint "${faceDownName}" not found`);
		}
	}

	// ── Entity Lifecycle ─────────────────────────────────────────────

	createEntity(cardData: ClientCard, faceUp: boolean): CardEntity {
		const blueprint = faceUp ? this._faceUpBlueprint : this._faceDownBlueprint;
		if (!blueprint) {
			throw new Error(
				`CardEntityManager: no ${faceUp ? 'face-up' : 'face-down'} blueprint. Call initBlueprints() first.`,
			);
		}

		const meshName = `Card_${cardData.instanceId}`;
		const mesh = cloneMeshWithScripts(blueprint, meshName);
		if (!mesh) {
			throw new Error(`CardEntityManager: failed to clone blueprint for ${cardData.instanceId}`);
		}

		mesh.setEnabled(true);

		const entity = new CardEntity(cardData.instanceId, mesh, cardData);
		this._entities.set(cardData.instanceId, entity);
		this._meshToEntity.set(mesh, entity);

		return entity;
	}

	destroyEntity(instanceId: string): void {
		const entity = this._entities.get(instanceId);
		if (!entity) return;

		this._meshToEntity.delete(entity.mesh);
		this._entities.delete(instanceId);
		entity.dispose();
	}

	// ── Lookups ──────────────────────────────────────────────────────

	getByInstanceId(instanceId: string): CardEntity | undefined {
		return this._entities.get(instanceId);
	}

	getByMesh(mesh: Mesh): CardEntity | undefined {
		return this._meshToEntity.get(mesh);
	}

	getEntitiesInZone(ownerId: string, zone: Zone): CardEntity[] {
		const result: CardEntity[] = [];
		for (const entity of this._entities.values()) {
			if (entity.ownerId === ownerId && entity.zone === zone) {
				result.push(entity);
			}
		}
		return result;
	}

	getAllEntities(): CardEntity[] {
		return Array.from(this._entities.values());
	}

	// ── Cleanup ──────────────────────────────────────────────────────

	dispose(): void {
		for (const entity of this._entities.values()) {
			entity.dispose();
		}
		this._entities.clear();
		this._meshToEntity.clear();
		this._faceUpBlueprint = null;
		this._faceDownBlueprint = null;
		CardEntityManager.instance = null;
	}
}
