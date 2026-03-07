import { Vector3, Quaternion } from '@babylonjs/core/Maths/math.vector';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import type { CardEntity } from '../entities/CardEntity';
import type { Zone } from '../game/models';
import { type ZoneRenderer, animateTransform } from './ZoneRenderer';

const PILE_X_OFFSET = 5;
const PILE_Y_OFFSET = 1.5;
const PILE_Z_OFFSET = 3;

export class GraveyardZoneRenderer implements ZoneRenderer {
	readonly zone: Zone = 'GRAVEYARD';
	readonly ownerId: string;
	private _anchor: TransformNode;
	private _entities: CardEntity[] = [];

	constructor(ownerId: string, anchorNode: TransformNode) {
		this.ownerId = ownerId;
		this._anchor = anchorNode;
	}

	async addCard(entity: CardEntity, animate: boolean): Promise<void> {
		this._entities.push(entity);
		const pos = this._pilePosition(this._entities.length - 1);
		const rot = this._baseRotation();

		if (animate) {
			await animateTransform(entity.mesh, pos, rot);
		} else {
			entity.mesh.position.copyFrom(pos);
			entity.mesh.rotationQuaternion = rot;
		}
	}

	removeCard(instanceId: string): void {
		const idx = this._entities.findIndex((e) => e.instanceId === instanceId);
		if (idx !== -1) this._entities.splice(idx, 1);
	}

	async repositionAll(animate: boolean): Promise<void> {
		await Promise.all(
			this._entities.map((entity, i) => {
				const pos = this._pilePosition(i);
				if (animate) return animateTransform(entity.mesh, pos);
				entity.mesh.position.copyFrom(pos);
				return Promise.resolve();
			}),
		);
	}

	getEntryPosition(): Vector3 {
		return this._pilePosition(this._entities.length);
	}

	getExitPosition(): Vector3 {
		return this._pilePosition(Math.max(0, this._entities.length - 1));
	}

	getEntities(): CardEntity[] {
		return [...this._entities];
	}

	get count(): number {
		return this._entities.length;
	}

	dispose(): void {
		this._entities = [];
	}

	private _pilePosition(index: number): Vector3 {
		const base = this._anchor.getAbsolutePosition();
		return new Vector3(
			base.x + index * PILE_X_OFFSET,
			base.y + index * PILE_Y_OFFSET,
			base.z + index * PILE_Z_OFFSET,
		);
	}

	private _baseRotation(): Quaternion {
		return (
			this._anchor.rotationQuaternion?.clone() ??
			Quaternion.FromEulerAngles(
				this._anchor.rotation.x,
				this._anchor.rotation.y,
				this._anchor.rotation.z,
			)
		);
	}
}
