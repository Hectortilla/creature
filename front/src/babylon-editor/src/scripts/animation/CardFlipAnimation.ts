import { Animation } from '@babylonjs/core/Animations/animation';
import type { Scene } from '@babylonjs/core/scene';
import type { Animatable } from '@babylonjs/core/Animations/animatable';
import type { CardEntity } from '../entities/CardEntity';
import type { GameAnimation } from './GameAnimation';
import { ANIM_FPS, isMeshDisposed, msToFrames } from './utils';

export function cardFlip(entity: CardEntity, faceUp: boolean, duration = 300): GameAnimation {
	let animatable: Animatable | null = null;
	let resolve: (() => void) | null = null;
	const endX = faceUp ? 0 : Math.PI;

	return {
		name: `Flip(${entity.instanceId}, ${faceUp ? 'up' : 'down'})`,
		duration,

		execute(scene: Scene) {
			const mesh = entity.mesh;
			if (isMeshDisposed(mesh)) return Promise.resolve();

			const frames = msToFrames(duration);
			const flipAnim = new Animation('flipX', 'rotation.x', ANIM_FPS, Animation.ANIMATIONTYPE_FLOAT, Animation.ANIMATIONLOOPMODE_CONSTANT);
			flipAnim.setKeys([
				{ frame: 0, value: mesh.rotation.x },
				{ frame: frames, value: endX },
			]);

			return new Promise<void>(res => {
				resolve = res;
				animatable = scene.beginDirectAnimation(mesh, [flipAnim], 0, frames, false);
				animatable.onAnimationEndObservable.addOnce(() => { animatable = null; resolve = null; res(); });
			});
		},

		cancel() {
			animatable?.stop();
			animatable = null;
			if (!isMeshDisposed(entity.mesh)) entity.mesh.rotation.x = endX;
			resolve?.();
			resolve = null;
		},
	};
}
