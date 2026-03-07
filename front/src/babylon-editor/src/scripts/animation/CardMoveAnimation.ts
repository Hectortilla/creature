import { Animation } from '@babylonjs/core/Animations/animation';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { Quaternion } from '@babylonjs/core/Maths/math.vector';
import type { Scene } from '@babylonjs/core/scene';
import type { CardEntity } from '../entities/CardEntity';
import type { GameAnimation } from './GameAnimation';
import { ANIM_FPS, isMeshDisposed, msToFrames } from './utils';

const DEFAULT_DURATION_MS = 400;
const ARC_HEIGHT_FACTOR = 0.15;

export class CardMoveAnimation implements GameAnimation {
	readonly name: string;
	readonly duration: number;

	private _entity: CardEntity;
	private _from: Vector3;
	private _to: Vector3;
	private _toRotation: Quaternion | undefined;
	private _animatable: ReturnType<Scene['beginDirectAnimation']> | null = null;
	private _resolve: (() => void) | null = null;

	constructor(
		entity: CardEntity,
		fromPosition: Vector3,
		toPosition: Vector3,
		toRotation?: Quaternion,
		duration: number = DEFAULT_DURATION_MS,
	) {
		this._entity = entity;
		this._from = fromPosition;
		this._to = toPosition;
		this._toRotation = toRotation;
		this.duration = duration;
		this.name = `Move(${entity.instanceId})`;
	}

	execute(scene: Scene): Promise<void> {
		const mesh = this._entity.mesh;
		if (isMeshDisposed(mesh)) {
			return Promise.resolve();
		}

		const frames = msToFrames(this.duration);
		const midFrame = Math.round(frames / 2);
		const animations: Animation[] = [];

		// Bezier arc: raise Y at midpoint for a slight parabolic curve
		const dist = Vector3.Distance(this._from, this._to);
		const arcPeak = dist * ARC_HEIGHT_FACTOR;
		const mid = Vector3.Lerp(this._from, this._to, 0.5);
		mid.y += arcPeak;

		const posAnim = new Animation(
			'movePos',
			'position',
			ANIM_FPS,
			Animation.ANIMATIONTYPE_VECTOR3,
			Animation.ANIMATIONLOOPMODE_CONSTANT,
		);
		posAnim.setKeys([
			{ frame: 0, value: this._from.clone() },
			{ frame: midFrame, value: mid },
			{ frame: frames, value: this._to.clone() },
		]);
		animations.push(posAnim);

		if (this._toRotation) {
			mesh.rotationQuaternion ??= this._toRotation.clone();
			const rotAnim = new Animation(
				'moveRot',
				'rotationQuaternion',
				ANIM_FPS,
				Animation.ANIMATIONTYPE_QUATERNION,
				Animation.ANIMATIONLOOPMODE_CONSTANT,
			);
			rotAnim.setKeys([
				{ frame: 0, value: mesh.rotationQuaternion!.clone() },
				{ frame: frames, value: this._toRotation },
			]);
			animations.push(rotAnim);
		}

		mesh.position.copyFrom(this._from);

		return new Promise<void>((resolve) => {
			this._resolve = resolve;
			this._animatable = scene.beginDirectAnimation(mesh, animations, 0, frames, false);
			this._animatable.onAnimationEndObservable.addOnce(() => {
				this._animatable = null;
				this._resolve = null;
				resolve();
			});
		});
	}

	cancel(): void {
		this._animatable?.stop();
		this._animatable = null;

		const mesh = this._entity.mesh;
		if (!isMeshDisposed(mesh)) {
			mesh.position.copyFrom(this._to);
			if (this._toRotation) mesh.rotationQuaternion = this._toRotation.clone();
		}

		this._resolve?.();
		this._resolve = null;
	}
}
