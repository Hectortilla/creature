import type { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { CardEntity } from '../entities/CardEntity';
import type { Zone } from '../game/models';

export { animateTransform } from '../animation/utils';

export interface ZoneRenderer {
	readonly zone: Zone;

	addCard(entity: CardEntity, animate: boolean): Promise<void>;
	removeCard(instanceId: string): void;
	repositionAll(animate: boolean): Promise<void>;

	getEntryPosition(index?: number): Vector3;
	getExitPosition(index?: number): Vector3;

	getEntities(): CardEntity[];
	get count(): number;

	dispose(): void;
}
