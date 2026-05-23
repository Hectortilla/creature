import { createHudStore, type HudStoreSetter } from './createHudStore';

export interface ElementPoolSnapshot {
	elements: Record<string, number>;
	maxElements: Record<string, number>;
}

export interface ElementPoolsPayload {
	myPool: ElementPoolSnapshot;
	oppPool: ElementPoolSnapshot;
}

export type ElementPoolsSetter = HudStoreSetter<ElementPoolsPayload>;

export const [elementPools, setElementPools] = createHudStore<ElementPoolsPayload>();
