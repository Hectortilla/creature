import type { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { CardEntity } from '../entities/CardEntity';
import type { Zone } from '../game/models';

export { animateTransform } from '../animation/utils';

export interface ZoneRenderer {
	readonly zone: Zone;

	addCard(entity: CardEntity, animate: boolean): Promise<void>;
	removeCard(instanceId: string): CardEntity | undefined;
	repositionAll(animate: boolean): Promise<void>;

	getEntryPosition(index?: number): Vector3;
	getExitPosition(index?: number): Vector3;

	getEntities(): CardEntity[];
	get count(): number;

	dispose(): void;
}

/**
 * Shared zone behaviour. Subclasses must own the entity list and expose it via
 * `entityList` so `removeCard` / `getEntities` / `count` / `dispose` read the same
 * array that `addCard` mutates (avoids class-field inheritance edge cases in some builds).
 */
export abstract class ZoneRendererBase implements ZoneRenderer {
	/** The live `CardEntity[]` for this zone (same reference used for add/remove). */
	protected abstract get entityList(): CardEntity[];

	abstract readonly zone: Zone;
	abstract addCard(entity: CardEntity, animate: boolean): Promise<void>;
	abstract repositionAll(animate: boolean): Promise<void>;
	abstract getEntryPosition(index?: number): Vector3;
	abstract getExitPosition(index?: number): Vector3;

	removeCard(instanceId: string): CardEntity | undefined {
		const list = this.entityList;
		const idx = list.findIndex((e) => e.instanceId === instanceId);
		if (idx === -1) return undefined;
		const [removed] = list.splice(idx, 1);
		return removed;
	}

	getEntities(): CardEntity[] {
		return [...this.entityList];
	}

	get count(): number {
		return this.entityList.length;
	}

	dispose(): void {
		this.entityList.length = 0;
	}
}
