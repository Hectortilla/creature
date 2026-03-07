import { Vector3, Quaternion } from '@babylonjs/core/Maths/math.vector';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import type { CardEntity } from '../entities/CardEntity';
import type { Zone } from '../game/models';
import { type ZoneRenderer, animateTransform } from './ZoneRenderer';

const DEFAULT_SLOT_SPACING = 100;

export class FieldZoneRenderer implements ZoneRenderer {
	readonly zone: Zone;
	readonly ownerId: string;
	private _anchor: TransformNode;
	private _maxSlots: number;
	private _slotSpacing: number;
	private _entities: CardEntity[] = [];

	constructor(
		zone: Zone,
		ownerId: string,
		anchorNode: TransformNode,
		maxSlots: number,
		_isLocalPlayer: boolean,
		slotSpacing: number = DEFAULT_SLOT_SPACING,
	) {
		this.zone = zone;
		this.ownerId = ownerId;
		this._anchor = anchorNode;
		this._maxSlots = maxSlots;
		this._slotSpacing = slotSpacing;
	}

	async addCard(entity: CardEntity, animate: boolean): Promise<void> {
		if (this._entities.length >= this._maxSlots) {
			console.warn(
				`FieldZoneRenderer(${this.zone}): max slots (${this._maxSlots}) reached`,
			);
		}
		this._entities.push(entity);
		await this.repositionAll(animate);
	}

	removeCard(instanceId: string): void {
		const idx = this._entities.findIndex((e) => e.instanceId === instanceId);
		if (idx !== -1) this._entities.splice(idx, 1);
	}

	async repositionAll(animate: boolean): Promise<void> {
		const n = this._entities.length;
		if (n === 0) return;

		const base = this._anchor.getAbsolutePosition();
		const baseRot =
			this._anchor.rotationQuaternion?.clone() ??
			Quaternion.FromEulerAngles(
				this._anchor.rotation.x,
				this._anchor.rotation.y,
				this._anchor.rotation.z,
			);

		const totalWidth = (n - 1) * this._slotSpacing;

		await Promise.all(
			this._entities.map((entity, i) => {
				const pos = new Vector3(
					base.x - totalWidth / 2 + i * this._slotSpacing,
					base.y,
					base.z,
				);
				if (animate) return animateTransform(entity.mesh, pos, baseRot);
				entity.mesh.position.copyFrom(pos);
				entity.mesh.rotationQuaternion = baseRot.clone();
				return Promise.resolve();
			}),
		);
	}

	getEntryPosition(index?: number): Vector3 {
		const n = index ?? this._entities.length;
		return this._slotPosition(n);
	}

	getExitPosition(index?: number): Vector3 {
		const n = index ?? Math.max(0, this._entities.length - 1);
		return this._slotPosition(n);
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

	private _slotPosition(index: number): Vector3 {
		const base = this._anchor.getAbsolutePosition();
		const total = Math.max(this._entities.length, 1);
		const totalWidth = (total - 1) * this._slotSpacing;
		return new Vector3(
			base.x - totalWidth / 2 + index * this._slotSpacing,
			base.y,
			base.z,
		);
	}
}
