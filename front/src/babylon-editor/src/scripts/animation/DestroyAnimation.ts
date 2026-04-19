import { Animation } from '@babylonjs/core/Animations/animation';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { Scene } from '@babylonjs/core/scene';
import type { Animatable } from '@babylonjs/core/Animations/animatable';
import type { CardEntity } from '../entities/CardEntity';
import type { GameAnimation } from './GameAnimation';
import { ANIM_FPS, isMeshDisposed, msToFrames } from './utils';

export function destroyCard(entity: CardEntity, graveyardPos: Vector3, duration = 500): GameAnimation {
	let animatable: Animatable | null = null;
	let resolve: (() => void) | null = null;

	return {
		name: `Destroy(${entity.instanceId})`,
		duration,

		execute(scene: Scene) {
			const mesh = entity.mesh;
			if (isMeshDisposed(mesh)) return Promise.resolve();

			const frames = msToFrames(duration);
			const posAnim = new Animation('destroyPos', 'position', ANIM_FPS, Animation.ANIMATIONTYPE_VECTOR3, Animation.ANIMATIONLOOPMODE_CONSTANT);
			posAnim.setKeys([{ frame: 0, value: mesh.position.clone() }, { frame: frames, value: graveyardPos.clone() }]);

			const scaleAnim = new Animation('destroyScale', 'scaling', ANIM_FPS, Animation.ANIMATIONTYPE_VECTOR3, Animation.ANIMATIONLOOPMODE_CONSTANT);
			scaleAnim.setKeys([{ frame: 0, value: mesh.scaling.clone() }, { frame: frames, value: Vector3.Zero() }]);

			const fadeAnim = new Animation('destroyFade', 'visibility', ANIM_FPS, Animation.ANIMATIONTYPE_FLOAT, Animation.ANIMATIONLOOPMODE_CONSTANT);
			fadeAnim.setKeys([{ frame: 0, value: mesh.visibility }, { frame: frames, value: 0 }]);

			return new Promise<void>(res => {
				resolve = res;
				animatable = scene.beginDirectAnimation(mesh, [posAnim, scaleAnim, fadeAnim], 0, frames, false);
				animatable.onAnimationEndObservable.addOnce(() => { animatable = null; resolve = null; res(); });
			});
		},

		cancel() {
			animatable?.stop();
			animatable = null;
			if (!isMeshDisposed(entity.mesh)) {
				entity.mesh.position.copyFrom(graveyardPos);
				entity.mesh.scaling.setAll(0);
				entity.mesh.visibility = 0;
			}
			resolve?.();
			resolve = null;
		},
	};
}
