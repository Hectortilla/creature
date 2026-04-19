import { Animation } from '@babylonjs/core/Animations/animation';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { Scene } from '@babylonjs/core/scene';
import type { Animatable } from '@babylonjs/core/Animations/animatable';
import type { CardEntity } from '../entities/CardEntity';
import type { GameAnimation } from './GameAnimation';
import { ANIM_FPS, isMeshDisposed, msToFrames } from './utils';

const LUNGE_RATIO = 0.25;
const HOLD_RATIO = 0.42;

export function attackLunge(
	attacker: CardEntity,
	target: CardEntity | Vector3,
	duration = 600,
): GameAnimation {
	const targetPos = target instanceof Vector3 ? target.clone() : target.mesh.position.clone();
	let origin: Vector3 | null = null;
	let animatable: Animatable | null = null;
	let resolve: (() => void) | null = null;

	return {
		name: `Attack(${attacker.instanceId})`,
		duration,

		execute(scene: Scene) {
			const mesh = attacker.mesh;
			if (isMeshDisposed(mesh)) return Promise.resolve();

			origin = mesh.position.clone();
			const frames = msToFrames(duration);
			const lungePos = Vector3.Lerp(origin, targetPos, 0.8);

			const posAnim = new Animation('atkPos', 'position', ANIM_FPS, Animation.ANIMATIONTYPE_VECTOR3, Animation.ANIMATIONLOOPMODE_CONSTANT);
			posAnim.setKeys([
				{ frame: 0, value: origin.clone() },
				{ frame: Math.round(frames * LUNGE_RATIO), value: lungePos },
				{ frame: Math.round(frames * HOLD_RATIO), value: lungePos.clone() },
				{ frame: frames, value: origin.clone() },
			]);

			return new Promise<void>(res => {
				resolve = res;
				animatable = scene.beginDirectAnimation(mesh, [posAnim], 0, frames, false);
				animatable.onAnimationEndObservable.addOnce(() => { animatable = null; resolve = null; res(); });
			});
		},

		cancel() {
			animatable?.stop();
			animatable = null;
			if (origin && !isMeshDisposed(attacker.mesh)) attacker.mesh.position.copyFrom(origin);
			resolve?.();
			resolve = null;
		},
	};
}
