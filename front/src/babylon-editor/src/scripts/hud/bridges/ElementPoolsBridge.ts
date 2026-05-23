import type BoardController from '../../BoardController';
import type {
	ElementsChangedData,
	ElementPoolsUpdatedData,
	GameStartedEventData,
} from '../../state/events';
import type { ElementPoolsPayload } from '$lib/stores/babylon/elementPools';
import { HudBridge } from './HudBridge';

/**
 * Event-driven bridge between BoardController element-pool events and the Svelte overlay store.
 *
 * Unlike HoveredCardBridge (which polls Babylon hover state per frame), pool changes
 * arrive as discrete events, so we subscribe once and push on each emission.
 */
export class ElementPoolsBridge extends HudBridge<ElementPoolsPayload> {
	private _board: BoardController;
	private _myPlayerId = '';

	constructor(board: BoardController) {
		super();
		this._board = board;
		this._board.on('gameStarted', this._onGameStarted);
		this._board.on('elementPoolsUpdated', this._onPoolsUpdated);
		this._board.on('elementsConsumed', this._onElementsChanged);
		this._board.on('elementsRestored', this._onElementsChanged);
	}

	private _onGameStarted = (data: GameStartedEventData): void => {
		this._myPlayerId = data.myPlayerId;
		this._emit({
			myPool: {
				elements: data.myElementPool.elements,
				maxElements: data.myElementPool.maxElements,
			},
			oppPool: {
				elements: data.opponentElementPool.elements,
				maxElements: data.opponentElementPool.maxElements,
			},
		});
	};

	private _onPoolsUpdated = (data: ElementPoolsUpdatedData): void => {
		this._emit({
			myPool: { elements: data.myPool.elements, maxElements: data.myPool.maxElements },
			oppPool: { elements: data.oppPool.elements, maxElements: data.oppPool.maxElements },
		});
	};

	private _onElementsChanged = (data: ElementsChangedData): void => {
		if (!this._latest) return;
		const isMine = data.playerId === this._myPlayerId;
		const next: ElementPoolsPayload = isMine
			? {
					myPool: { elements: data.currentPool, maxElements: data.maxPool },
					oppPool: this._latest.oppPool,
				}
			: {
					myPool: this._latest.myPool,
					oppPool: { elements: data.currentPool, maxElements: data.maxPool },
				};
		this._emit(next);
	};

	override dispose(): void {
		this._board.off('gameStarted', this._onGameStarted);
		this._board.off('elementPoolsUpdated', this._onPoolsUpdated);
		this._board.off('elementsConsumed', this._onElementsChanged);
		this._board.off('elementsRestored', this._onElementsChanged);
		super.dispose();
	}
}
