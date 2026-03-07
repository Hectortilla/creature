import { Animation } from '@babylonjs/core/Animations/animation';
import type { Vector3, Quaternion } from '@babylonjs/core/Maths/math.vector';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import type { CardEntity } from '../entities/CardEntity';
import type { Zone } from '../game/models';

export interface ZoneRenderer {
	readonly zone: Zone;
	readonly ownerId: string;

	addCard(entity: CardEntity, animate: boolean): Promise<void>;
	removeCard(instanceId: string): void;
	repositionAll(animate: boolean): Promise<void>;

	getEntryPosition(index?: number): Vector3;
	getExitPosition(index?: number): Vector3;

	getEntities(): CardEntity[];
	get count(): number;

	dispose(): void;
}

const ANIM_FPS = 60;
const DEFAULT_FRAMES = 18; // ~300ms at 60fps

export function animateTransform(
	node: TransformNode,
	targetPosition: Vector3,
	targetRotation?: Quaternion,
	frames: number = DEFAULT_FRAMES,
): Promise<void> {
	const animations: Animation[] = [];

	const posAnim = new Animation(
		'zonePos',
		'position',
		ANIM_FPS,
		Animation.ANIMATIONTYPE_VECTOR3,
		Animation.ANIMATIONLOOPMODE_CONSTANT,
	);
	posAnim.setKeys([
		{ frame: 0, value: node.position.clone() },
		{ frame: frames, value: targetPosition },
	]);
	animations.push(posAnim);

	if (targetRotation) {
		node.rotationQuaternion ??= targetRotation.clone();
		const rotAnim = new Animation(
			'zoneRot',
			'rotationQuaternion',
			ANIM_FPS,
			Animation.ANIMATIONTYPE_QUATERNION,
			Animation.ANIMATIONLOOPMODE_CONSTANT,
		);
		rotAnim.setKeys([
			{ frame: 0, value: node.rotationQuaternion!.clone() },
			{ frame: frames, value: targetRotation },
		]);
		animations.push(rotAnim);
	}

	return new Promise<void>((resolve) => {
		node
			.getScene()
			.beginDirectAnimation(node, animations, 0, frames, false)
			.onAnimationEndObservable.addOnce(() => resolve());
	});
}
