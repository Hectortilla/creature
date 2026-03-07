import { Animation } from '@babylonjs/core/Animations/animation';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { Scene } from '@babylonjs/core/scene';
import type { CardEntity } from '../entities/CardEntity';
import type { GameAnimation } from './GameAnimation';
import { ANIM_FPS, isMeshDisposed, msToFrames } from './utils';

const DEFAULT_DURATION_MS = 600;
// Phase split: lunge 25%, hold ~17%, return 58%
const LUNGE_RATIO = 0.25;
const HOLD_RATIO = 0.42; // cumulative: lunge + hold

export class AttackAnimation implements GameAnimation {
	readonly name: string;
	readonly duration: number;

	private _attacker: CardEntity;
	private _targetPos: Vector3;
	private _origin: Vector3 | null = null;
	private _animatable: ReturnType<Scene['beginDirectAnimation']> | null = null;
	private _resolve: (() => void) | null = null;

	constructor(
		attacker: CardEntity,
		target: CardEntity | Vector3,
		duration: number = DEFAULT_DURATION_MS,
	) {
		this._attacker = attacker;
		this._targetPos = target instanceof Vector3 ? target.clone() : target.mesh.position.clone();
		this.duration = duration;
		this.name = `Attack(${attacker.instanceId})`;
	}

	execute(scene: Scene): Promise<void> {
		const mesh = this._attacker.mesh;
		if (isMeshDisposed(mesh)) return Promise.resolve();

		this._origin = mesh.position.clone();
		const frames = msToFrames(this.duration);
		const lungeFrame = Math.round(frames * LUNGE_RATIO);
		const holdFrame = Math.round(frames * HOLD_RATIO);

		// Lunge most of the way toward target, not all the way (stop ~80% there)
		const lungePos = Vector3.Lerp(this._origin, this._targetPos, 0.8);

		const posAnim = new Animation(
			'atkPos',
			'position',
			ANIM_FPS,
			Animation.ANIMATIONTYPE_VECTOR3,
			Animation.ANIMATIONLOOPMODE_CONSTANT,
		);
		posAnim.setKeys([
			{ frame: 0, value: this._origin.clone() },
			{ frame: lungeFrame, value: lungePos },
			{ frame: holdFrame, value: lungePos.clone() },
			{ frame: frames, value: this._origin.clone() },
		]);

		return new Promise<void>((resolve) => {
			this._resolve = resolve;
			this._animatable = scene.beginDirectAnimation(mesh, [posAnim], 0, frames, false);
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

		if (this._origin && !isMeshDisposed(this._attacker.mesh)) {
			this._attacker.mesh.position.copyFrom(this._origin);
		}

		this._resolve?.();
		this._resolve = null;
	}
}
