import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Texture } from '@babylonjs/core/Materials/Textures/texture';
import type { Scene } from '@babylonjs/core/scene';
import type { CardEntity } from './CardEntity';
import { CardDefinitionCache } from '../game/CardDefinitionCache';

const PLACEHOLDER_IMAGE = '/images/cards/placeholder.jpg';

export class CardTextureManager {
	static instance: CardTextureManager | null = null;

	private _scene: Scene;
	private _textureCache = new Map<string, Texture>();

	private constructor(scene: Scene) {
		this._scene = scene;
	}

	static getOrCreate(scene: Scene): CardTextureManager {
		if (!CardTextureManager.instance) {
			CardTextureManager.instance = new CardTextureManager(scene);
		}
		return CardTextureManager.instance;
	}

	/**
	 * Resolve the card's image URL and apply a textured PBRMaterial to its mesh.
	 * No-op if the card is face-down.
	 *
	 * If card definitions haven't loaded yet, defer applying the material
	 * until they have — otherwise the placeholder gets baked into the mesh
	 * and never re-resolves.
	 */
	applyTexture(entity: CardEntity): void {
		if (!entity.cardData.faceUp) return;

		const cache = CardDefinitionCache.getOrCreate();
		const meshAtCall = entity.mesh;

		if (!cache.initialized) {
			cache.whenReady().then(() => {
				if (!entity.cardData.faceUp) return;
				if (entity.mesh !== meshAtCall) return;
				if (meshAtCall.isDisposed()) return;
				this._applyNow(entity);
			});
			return;
		}

		this._applyNow(entity);
	}

	private _applyNow(entity: CardEntity): void {
		const imageUrl = this._resolveImageUrl(entity.instanceId);
		const texture = this._getOrLoadTexture(imageUrl);

		const matName = `CardMat_${entity.instanceId}`;
		const mat = new PBRMaterial(matName, this._scene);
		mat.albedoTexture = texture;
		mat.metallic = 0;
		mat.roughness = 1;

		entity.mesh.material = mat;
	}

	private _resolveImageUrl(instanceId: string): string {
		const cache = CardDefinitionCache.getOrCreate();
		const def = cache.getByInstanceId(instanceId);
		if (def?.image) return def.image;
		return PLACEHOLDER_IMAGE;
	}

	private _getOrLoadTexture(url: string): Texture {
		const cached = this._textureCache.get(url);
		if (cached) return cached;

		const texture = new Texture(url, this._scene);
		this._textureCache.set(url, texture);
		return texture;
	}

	dispose(): void {
		for (const texture of this._textureCache.values()) {
			texture.dispose();
		}
		this._textureCache.clear();
		CardTextureManager.instance = null;
	}
}
