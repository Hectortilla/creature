import type { Mesh } from '@babylonjs/core/Meshes/mesh';
import type { Scene } from '@babylonjs/core/scene';
import { CardEntity } from './CardEntity';
import { CardTextureManager } from './CardTextureManager';
import type { ClientCard, Zone } from '../game/models';
import { cloneMeshWithScripts } from '../utils';

export class CardEntityManager {
	static instance: CardEntityManager | null = null;

	private _entities = new Map<string, CardEntity>();
	private _meshToEntity = new Map<Mesh, CardEntity>();
	private _scene: Scene;

	private _faceUpBlueprint: Mesh | null = null;
	private _faceDownBlueprint: Mesh | null = null;
	private _textureManager: CardTextureManager;

	private constructor(scene: Scene) {
		this._scene = scene;
		this._textureManager = CardTextureManager.getOrCreate(scene);
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

		const meshName = `Card_${cardData.instanceId}`;
		const mesh = cloneMeshWithScripts(blueprint, meshName);

		mesh.setEnabled(true);

		const entity = new CardEntity(cardData.instanceId, mesh, cardData);
		this._entities.set(cardData.instanceId, entity);
		this._meshToEntity.set(mesh, entity);

		if (faceUp) {
			this._textureManager.applyTexture(entity);
		}

		return entity;
	}

	destroyEntity(instanceId: string): void {
		const entity = this._entities.get(instanceId);
		if (!entity) return;

		this._meshToEntity.delete(entity.mesh);
		this._entities.delete(instanceId);
		entity.dispose();
	}

	syncFromState(cards: Record<string, ClientCard>): void {
		for (const card of Object.values(cards)) {
			const existing = this._entities.get(card.instanceId);
			if (!existing) {
				this.createEntity(card, card.faceUp);
				continue;
			}
			const wasFaceUp = existing.cardData.faceUp;
			existing.updateCardData(card);
			if (card.faceUp !== wasFaceUp) {
				this._swapMesh(existing, card.faceUp);
			}
		}
	}

	private _swapMesh(entity: CardEntity, faceUp: boolean): void {
		const blueprint = faceUp ? this._faceUpBlueprint : this._faceDownBlueprint;
		const oldMesh = entity.mesh;

		const newMesh = cloneMeshWithScripts(blueprint, oldMesh.name);
		newMesh.position.copyFrom(oldMesh.position);
		newMesh.rotation.copyFrom(oldMesh.rotation);
		if (oldMesh.rotationQuaternion) {
			newMesh.rotationQuaternion = oldMesh.rotationQuaternion.clone();
		}
		newMesh.scaling.copyFrom(oldMesh.scaling);
		newMesh.setEnabled(oldMesh.isEnabled());

		this._meshToEntity.delete(oldMesh);
		const oldMat = oldMesh.material;
		oldMesh.dispose();
		if (oldMat && oldMat.name.startsWith('CardMat_')) {
			oldMat.dispose();
		}

		entity.mesh = newMesh;
		this._meshToEntity.set(newMesh, entity);

		if (faceUp) {
			this._textureManager.applyTexture(entity);
		}
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
		this._textureManager.dispose();
		CardEntityManager.instance = null;
	}
}
