import { Animation } from '@babylonjs/core/Animations/animation';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { Quaternion } from '@babylonjs/core/Maths/math.vector';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';

export const ANIM_FPS = 60;
const DEFAULT_FRAMES = 18; // ~300ms at 60fps

export function msToFrames(ms: number): number {
	return Math.round((ms / 1000) * ANIM_FPS);
}

export function animateTransform(
	node: TransformNode,
	targetPosition: Vector3,
	targetRotation?: Quaternion,
	targetScale: Vector3 = Vector3.One(),
	frames: number = DEFAULT_FRAMES,
	fromPosition?: Vector3,
	fromRotation?: Quaternion,
	fromScale?: Vector3,
): Promise<void> {
	const animations: Animation[] = [];

	const startPos = fromPosition?.clone() ?? node.position.clone();
	const startRot = fromRotation?.clone() ?? node.rotationQuaternion?.clone() ?? targetRotation?.clone();

	const posAnim = new Animation(
		'pos',
		'position',
		ANIM_FPS,
		Animation.ANIMATIONTYPE_VECTOR3,
		Animation.ANIMATIONLOOPMODE_CONSTANT,
	);
	posAnim.setKeys([
		{ frame: 0, value: startPos },
		{ frame: frames, value: targetPosition },
	]);
	animations.push(posAnim);

	if (targetRotation && startRot) {
		const rotAnim = new Animation(
			'rot',
			'rotationQuaternion',
			ANIM_FPS,
			Animation.ANIMATIONTYPE_QUATERNION,
			Animation.ANIMATIONLOOPMODE_CONSTANT,
		);
		rotAnim.setKeys([
			{ frame: 0, value: startRot },
			{ frame: frames, value: targetRotation },
		]);
		animations.push(rotAnim);
	}

	if (targetScale) {
		const startScl = fromScale?.clone() ?? node.scaling.clone();
		const scaleAnim = new Animation(
			'scl',
			'scaling',
			ANIM_FPS,
			Animation.ANIMATIONTYPE_VECTOR3,
			Animation.ANIMATIONLOOPMODE_CONSTANT,
		);
		scaleAnim.setKeys([
			{ frame: 0, value: startScl },
			{ frame: frames, value: targetScale },
		]);
		animations.push(scaleAnim);
	}

	return new Promise<void>((resolve) => {
		node
			.getScene()
			.beginDirectAnimation(node, animations, 0, frames, false)
			.onAnimationEndObservable.addOnce(() => resolve());
	});
}

/** Returns true if the mesh has been disposed or is otherwise unusable. */
export function isMeshDisposed(node: TransformNode): boolean {
	return !node || node.isDisposed();
}
