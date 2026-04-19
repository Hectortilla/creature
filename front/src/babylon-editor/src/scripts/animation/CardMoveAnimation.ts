import { Animation } from '@babylonjs/core/Animations/animation';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { Quaternion } from '@babylonjs/core/Maths/math.vector';
import type { Scene } from '@babylonjs/core/scene';
import type { Animatable } from '@babylonjs/core/Animations/animatable';
import type { CardEntity } from '../entities/CardEntity';
import type { GameAnimation } from './GameAnimation';
import { ANIM_FPS, isMeshDisposed, msToFrames } from './utils';

const ARC_HEIGHT_FACTOR = 0.15;

export function cardMove(
	entity: CardEntity,
	from: Vector3,
	to: Vector3,
	toRotation?: Quaternion,
	duration = 400,
): GameAnimation {
	let animatable: Animatable | null = null;
	let resolve: (() => void) | null = null;

	return {
		name: `Move(${entity.instanceId})`,
		duration,

		execute(scene: Scene) {
			const mesh = entity.mesh;
			if (isMeshDisposed(mesh)) return Promise.resolve();

			const frames = msToFrames(duration);
			const midFrame = Math.round(frames / 2);
			const animations: Animation[] = [];

			const dist = Vector3.Distance(from, to);
			const mid = Vector3.Lerp(from, to, 0.5);
			mid.y += dist * ARC_HEIGHT_FACTOR;

			const posAnim = new Animation('movePos', 'position', ANIM_FPS, Animation.ANIMATIONTYPE_VECTOR3, Animation.ANIMATIONLOOPMODE_CONSTANT);
			posAnim.setKeys([
				{ frame: 0, value: from.clone() },
				{ frame: midFrame, value: mid },
				{ frame: frames, value: to.clone() },
			]);
			animations.push(posAnim);

			if (toRotation) {
				mesh.rotationQuaternion ??= toRotation.clone();
				const rotAnim = new Animation('moveRot', 'rotationQuaternion', ANIM_FPS, Animation.ANIMATIONTYPE_QUATERNION, Animation.ANIMATIONLOOPMODE_CONSTANT);
				rotAnim.setKeys([
					{ frame: 0, value: mesh.rotationQuaternion!.clone() },
					{ frame: frames, value: toRotation },
				]);
				animations.push(rotAnim);
			}

			mesh.position.copyFrom(from);

			return new Promise<void>(res => {
				resolve = res;
				animatable = scene.beginDirectAnimation(mesh, animations, 0, frames, false);
				animatable.onAnimationEndObservable.addOnce(() => { animatable = null; resolve = null; res(); });
			});
		},

		cancel() {
			animatable?.stop();
			animatable = null;
			const mesh = entity.mesh;
			if (!isMeshDisposed(mesh)) {
				mesh.position.copyFrom(to);
				if (toRotation) mesh.rotationQuaternion = toRotation.clone();
			}
			resolve?.();
			resolve = null;
		},
	};
}
