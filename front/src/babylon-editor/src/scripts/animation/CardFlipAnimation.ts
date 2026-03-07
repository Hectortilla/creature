import { Animation } from '@babylonjs/core/Animations/animation';
import type { Scene } from '@babylonjs/core/scene';
import type { CardEntity } from '../entities/CardEntity';
import type { GameAnimation } from './GameAnimation';
import { ANIM_FPS, isMeshDisposed, msToFrames } from './utils';

const DEFAULT_DURATION_MS = 300;

export class CardFlipAnimation implements GameAnimation {
	readonly name: string;
	readonly duration: number;

	private _entity: CardEntity;
	private _faceUp: boolean;
	private _animatable: ReturnType<Scene['beginDirectAnimation']> | null = null;
	private _resolve: (() => void) | null = null;

	constructor(entity: CardEntity, faceUp: boolean, duration: number = DEFAULT_DURATION_MS) {
		this._entity = entity;
		this._faceUp = faceUp;
		this.duration = duration;
		this.name = `Flip(${entity.instanceId}, ${faceUp ? 'up' : 'down'})`;
	}

	execute(scene: Scene): Promise<void> {
		const mesh = this._entity.mesh;
		if (isMeshDisposed(mesh)) return Promise.resolve();

		const frames = msToFrames(this.duration);
		const startX = mesh.rotation.x;
		const endX = this._faceUp ? 0 : Math.PI;

		const flipAnim = new Animation(
			'flipX',
			'rotation.x',
			ANIM_FPS,
			Animation.ANIMATIONTYPE_FLOAT,
			Animation.ANIMATIONLOOPMODE_CONSTANT,
		);
		flipAnim.setKeys([
			{ frame: 0, value: startX },
			{ frame: frames, value: endX },
		]);

		return new Promise<void>((resolve) => {
			this._resolve = resolve;
			this._animatable = scene.beginDirectAnimation(mesh, [flipAnim], 0, frames, false);
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
			mesh.rotation.x = this._faceUp ? 0 : Math.PI;
		}

		this._resolve?.();
		this._resolve = null;
	}
}
