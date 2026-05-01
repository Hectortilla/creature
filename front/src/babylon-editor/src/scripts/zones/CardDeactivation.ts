import { Quaternion, Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { ClientCard } from '../game/models';

const DEG_TO_RAD = Math.PI / 180;

export function getDeactivationAngle(card: ClientCard): number {
	if (card.has_attacked_this_turn) return 90;
	if (card.zone === 'SUPPORTING' && card.turns_in_zone === 0 && !card.swapped_this_turn) {
		return 90;
	}
	if (card.swapped_this_turn) return 45;
	return 0;
}

export function getDeactivationQuaternion(card: ClientCard): Quaternion {
	const angle = getDeactivationAngle(card);
	if (angle === 0) return Quaternion.Identity();
	return Quaternion.RotationAxis(Vector3.Up(), angle * DEG_TO_RAD);
}
