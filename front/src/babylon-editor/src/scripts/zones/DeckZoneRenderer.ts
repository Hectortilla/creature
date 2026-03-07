import { Vector3, Quaternion } from '@babylonjs/core/Maths/math.vector';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import type { CardEntity } from '../entities/CardEntity';
import type { Zone } from '../game/models';
import { type ZoneRenderer, animateTransform } from './ZoneRenderer';

const CARD_STACK_Y_OFFSET = 1.5;
const MAX_JITTER = 0.08;

export class DeckZoneRenderer implements ZoneRenderer {
	readonly zone: Zone = 'DECK';
	readonly ownerId: string;
	private _anchor: TransformNode;
	private _entities: CardEntity[] = [];

	constructor(ownerId: string, anchorNode: TransformNode) {
		this.ownerId = ownerId;
		this._anchor = anchorNode;
	}

	async addCard(entity: CardEntity, animate: boolean): Promise<void> {
		this._entities.push(entity);
		const pos = this._stackPosition(this._entities.length - 1);
		const rot = this._jitteredRotation();

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
				const pos = this._stackPosition(i);
				if (animate) return animateTransform(entity.mesh, pos);
				entity.mesh.position.copyFrom(pos);
				return Promise.resolve();
			}),
		);
	}

	getEntryPosition(): Vector3 {
		return this._stackPosition(this._entities.length);
	}

	getExitPosition(): Vector3 {
		return this._stackPosition(Math.max(0, this._entities.length - 1));
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

	private _stackPosition(index: number): Vector3 {
		const base = this._anchor.getAbsolutePosition();
		return new Vector3(base.x, base.y + index * CARD_STACK_Y_OFFSET, base.z);
	}

	private _jitteredRotation(): Quaternion {
		const base =
			this._anchor.rotationQuaternion?.clone() ??
			Quaternion.FromEulerAngles(
				this._anchor.rotation.x,
				this._anchor.rotation.y,
				this._anchor.rotation.z,
			);
		return base.multiply(
			Quaternion.RotationAxis(Vector3.Up(), (Math.random() * 2 - 1) * MAX_JITTER),
		);
	}
}
