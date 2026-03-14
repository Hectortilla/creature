import { Vector3, Quaternion } from '@babylonjs/core/Maths/math.vector';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import type { CardEntity } from '../entities/CardEntity';
import type { Zone } from '../game/models';
import { type ZoneRenderer, animateTransform } from './ZoneRenderer';

// Fan layout constants
const MAX_TOTAL_WIDTH = 399; // maximum horizontal span for the hand
const PREFERRED_CARD_SPACING = 100; // ideal gap between cards
const ARC_HEIGHT = 80;
const MAX_FAN_ANGLE = (20 * Math.PI) / 180; // max rotation at the edges
const MAX_JITTER = 0.08;

// Opponent compact layout
const OPP_CARD_SPACING = 20;

interface CardTransform {
	position: Vector3;
	rotation: Quaternion;
}

export class HandZoneRenderer implements ZoneRenderer {
	readonly zone: Zone = 'HAND';
	private _anchor: TransformNode;
	private _isLocalPlayer: boolean;
	private _entities: CardEntity[] = [];

	constructor(anchorNode: TransformNode, isLocalPlayer: boolean) {
		this._anchor = anchorNode;
		this._isLocalPlayer = isLocalPlayer;
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

		const transforms = this._isLocalPlayer
			? this._fanLayout(n)
			: this._compactLayout(n);

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
		// Scale arc and rotation proportionally to how spread out the cards are
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

	private _compactLayout(n: number): CardTransform[] {
		const base = this._anchor.getAbsolutePosition();
		const baseRot = this._anchorRotation();
		const totalWidth = (n - 1) * OPP_CARD_SPACING;
		const result: CardTransform[] = [];

		for (let i = 0; i < n; i++) {
			const position = new Vector3(
				base.x - totalWidth / 2 + i * OPP_CARD_SPACING,
				base.y,
				base.z,
			);
			result.push({ position, rotation: baseRot.clone() });
		}

		return result;
	}
}
