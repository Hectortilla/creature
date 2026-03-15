import { Vector3, Quaternion } from '@babylonjs/core/Maths/math.vector';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import type { CardEntity } from '../entities/CardEntity';
import type { Zone } from '../game/models';
import { type ZoneRenderer, animateTransform } from './ZoneRenderer';

// Fan layout constants
const MAX_TOTAL_WIDTH = 399;
const PREFERRED_CARD_SPACING = 100;
const ARC_HEIGHT = 80;
const MAX_FAN_ANGLE = (20 * Math.PI) / 180;
const MAX_JITTER = 0.08;


interface CardTransform {
	position: Vector3;
	rotation: Quaternion;
}

export class HandZoneRenderer implements ZoneRenderer {
	readonly zone: Zone = 'HAND';
	private _anchor: TransformNode;
	private _entities: CardEntity[] = [];

	constructor(anchorNode: TransformNode) {
		this._anchor = anchorNode;
	}

	async addCard(entity: CardEntity, animate: boolean): Promise<void> {
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

		const transforms = this._fanLayout(n);

		await Promise.all(
			this._entities.map((entity, i) => {
				const { position, rotation } = transforms[i];
				if (animate) return animateTransform(entity.mesh, position, rotation);
				entity.mesh.position.copyFrom(position);
				entity.mesh.rotationQuaternion = rotation;
				return Promise.resolve();
			}),
		);
	}

	getEntryPosition(): Vector3 {
		return this._anchor.getAbsolutePosition().clone();
	}

	getExitPosition(): Vector3 {
		return this._anchor.getAbsolutePosition().clone();
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

	private _anchorRotation(): Quaternion {
		return (
			this._anchor.rotationQuaternion?.clone() ??
			Quaternion.FromEulerAngles(
				this._anchor.rotation.x,
				this._anchor.rotation.y,
				this._anchor.rotation.z,
			)
		);
	}

	private _fanLayout(n: number): CardTransform[] {
		const base = this._anchor.getAbsolutePosition();
		const baseRot = this._anchorRotation();

		const desiredWidth = (n - 1) * PREFERRED_CARD_SPACING;
		const actualWidth = Math.min(desiredWidth, MAX_TOTAL_WIDTH);
		const halfSpan = actualWidth / 2;
		const spreadRatio = n <= 1 ? 0 : actualWidth / MAX_TOTAL_WIDTH;

		const result: CardTransform[] = [];

		for (let i = 0; i < n; i++) {
			const t = n === 1 ? 0.5 : i / (n - 1);
			const jitter = (Math.random() * 2 - 1) * MAX_JITTER;
			const archOffset = 1 - (2 * t - 1) ** 2;

			const position = new Vector3(
				base.x - halfSpan + t * actualWidth,
				base.y + archOffset * ARC_HEIGHT * spreadRatio,
				base.z,
			);

			const fanAngle = (-MAX_FAN_ANGLE + t * 2 * MAX_FAN_ANGLE) * spreadRatio;
			const rotation = baseRot
				.clone()
				.multiply(Quaternion.RotationAxis(Vector3.Up(), fanAngle + jitter))
				.multiply(Quaternion.RotationAxis(Vector3.Forward(), jitter))
				.multiply(Quaternion.RotationAxis(Vector3.Right(), jitter / 4));

			result.push({ position, rotation });
		}

		return result;
	}
}
