import { Animation } from '@babylonjs/core/Animations/animation';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { Scene } from '@babylonjs/core/scene';
import type { CardEntity } from '../entities/CardEntity';
import type { GameAnimation } from './GameAnimation';
import { ANIM_FPS, isMeshDisposed, msToFrames } from './utils';

const DEFAULT_DURATION_MS = 500;

export class DestroyAnimation implements GameAnimation {
	readonly name: string;
	readonly duration: number;

	private _entity: CardEntity;
	private _graveyardPos: Vector3;
	private _animatable: ReturnType<Scene['beginDirectAnimation']> | null = null;
	private _resolve: (() => void) | null = null;

	constructor(entity: CardEntity, graveyardPosition: Vector3, duration: number = DEFAULT_DURATION_MS) {
		this._entity = entity;
		this._graveyardPos = graveyardPosition;
		this.duration = duration;
		this.name = `Destroy(${entity.instanceId})`;
	}

	execute(scene: Scene): Promise<void> {
		const mesh = this._entity.mesh;
		if (isMeshDisposed(mesh)) return Promise.resolve();

		const frames = msToFrames(this.duration);
		const animations: Animation[] = [];

		// Move toward graveyard
		const posAnim = new Animation(
			'destroyPos',
			'position',
			ANIM_FPS,
			Animation.ANIMATIONTYPE_VECTOR3,
			Animation.ANIMATIONLOOPMODE_CONSTANT,
		);
		posAnim.setKeys([
			{ frame: 0, value: mesh.position.clone() },
			{ frame: frames, value: this._graveyardPos.clone() },
		]);
		animations.push(posAnim);

		// Scale down
		const scaleAnim = new Animation(
			'destroyScale',
			'scaling',
			ANIM_FPS,
			Animation.ANIMATIONTYPE_VECTOR3,
			Animation.ANIMATIONLOOPMODE_CONSTANT,
		);
		scaleAnim.setKeys([
			{ frame: 0, value: mesh.scaling.clone() },
			{ frame: frames, value: Vector3.Zero() },
		]);
		animations.push(scaleAnim);

		// Fade out
		const fadeAnim = new Animation(
			'destroyFade',
			'visibility',
			ANIM_FPS,
			Animation.ANIMATIONTYPE_FLOAT,
			Animation.ANIMATIONLOOPMODE_CONSTANT,
		);
		fadeAnim.setKeys([
			{ frame: 0, value: mesh.visibility },
			{ frame: frames, value: 0 },
		]);
		animations.push(fadeAnim);

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
			mesh.position.copyFrom(this._graveyardPos);
			mesh.scaling.setAll(0);
			mesh.visibility = 0;
		}

		this._resolve?.();
		this._resolve = null;
	}
}
