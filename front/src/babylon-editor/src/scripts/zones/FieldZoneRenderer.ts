import { Vector3, Quaternion } from '@babylonjs/core/Maths/math.vector';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import type { CardEntity } from '../entities/CardEntity';
import { getDeactivationQuaternion, type Zone } from '../game/models';
import { ZoneRendererBase, animateTransform } from './ZoneRenderer';

const DEFAULT_SLOT_SPACING = 150;

export class FieldZoneRenderer extends ZoneRendererBase {
	readonly zone: Zone;
	private _anchor: TransformNode;
	private _maxSlots: number;
	private _slotSpacing: number;
	private readonly _entities: CardEntity[] = [];

	protected get entityList(): CardEntity[] {
		return this._entities;
	}

	constructor(
		zone: Zone,
		anchorNode: TransformNode,
		maxSlots: number,
		slotSpacing: number = DEFAULT_SLOT_SPACING,
	) {
		super();
		this.zone = zone;
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
				const targetRot = baseRot.multiply(getDeactivationQuaternion(entity.cardData));
				if (animate) return animateTransform(entity.mesh, pos, targetRot);
				entity.mesh.position.copyFrom(pos);
				entity.mesh.rotationQuaternion = targetRot;
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
