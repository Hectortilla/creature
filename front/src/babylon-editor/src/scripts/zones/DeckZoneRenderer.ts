import { Vector3, Quaternion } from '@babylonjs/core/Maths/math.vector';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import type { CardEntity } from '../entities/CardEntity';
import type { Zone } from '../game/models';
import { ZoneRendererBase, animateTransform } from './ZoneRenderer';

const CARD_STACK_Y_OFFSET = 1.5;
const MAX_POSITION_JITTER = 2;
const MAX_ROTATION_JITTER = 0.08;

export class DeckZoneRenderer extends ZoneRendererBase {
	readonly zone: Zone = 'DECK';
	private _anchor: TransformNode;
	private readonly _entities: CardEntity[] = [];

	protected get entityList(): CardEntity[] {
		return this._entities;
	}

	constructor(anchorNode: TransformNode) {
		super();
		this._anchor = anchorNode;
	}

	async addCard(entity: CardEntity, animate: boolean): Promise<void> {
		this._entities.push(entity);
		const pos = this._stackPosition(this._entities.length - 1);
		const from = this._fromPositionToAdd(this._entities.length - 1);
		const rot = this._jitteredRotation();

		if (animate) {
			await animateTransform(entity.mesh, pos, rot, undefined, undefined, from, undefined, Vector3.Zero());
		} else {
			entity.mesh.position.copyFrom(pos);
			entity.mesh.rotationQuaternion = rot;
		}
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

	private _stackPosition(index: number): Vector3 {
		const base = this._anchor.getAbsolutePosition();
		const jitterX = (Math.random() * 2 - 1) * MAX_POSITION_JITTER;
		const jitterZ = (Math.random() * 2 - 1) * MAX_POSITION_JITTER;
		return new Vector3(base.x + jitterX, base.y + index * CARD_STACK_Y_OFFSET, base.z + jitterZ);
	}

	private _fromPositionToAdd(index: number): Vector3 {
		const base = this._anchor.getAbsolutePosition();
		return new Vector3(base.x, base.y + index * CARD_STACK_Y_OFFSET + 1000, base.z);
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
			Quaternion.RotationAxis(Vector3.Up(), (Math.random() * 2 - 1) * MAX_ROTATION_JITTER),
		);
	}
}
