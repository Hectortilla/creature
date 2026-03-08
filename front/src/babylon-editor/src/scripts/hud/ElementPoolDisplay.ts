import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import { StackPanel } from '@babylonjs/gui/2D/controls/stackPanel';
import type { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';
import type { GameStateStore, ElementsChangedData } from '../state/GameStateStore';

const BG_COLOR = 'rgba(15, 10, 40, 0.7)';
const LABEL_COLOR = '#D4AF37';
const VALUE_COLOR = '#FFFFFF';
const DEPLETED_COLOR = 'rgba(255, 255, 255, 0.35)';

export class ElementPoolDisplay {
	private _root: Rectangle;
	private _stack: StackPanel;
	private _title: TextBlock;
	private _elementRows = new Map<string, TextBlock>();
	private _stateStore: GameStateStore;

	constructor(gui: AdvancedDynamicTexture, stateStore: GameStateStore) {
		this._stateStore = stateStore;

		this._root = new Rectangle('elementPool_root');
		this._root.width = '150px';
		this._root.adaptHeightToChildren = true;
		this._root.left = '10px';
		this._root.top = '-10px';
		this._root.verticalAlignment = Rectangle.VERTICAL_ALIGNMENT_BOTTOM;
		this._root.horizontalAlignment = Rectangle.HORIZONTAL_ALIGNMENT_LEFT;
		this._root.background = BG_COLOR;
		this._root.cornerRadius = 8;
		this._root.thickness = 0;
		this._root.isPointerBlocker = false;
		this._root.paddingBottom = '6px';
		gui.addControl(this._root);

		this._stack = new StackPanel('elementPool_stack');
		this._stack.isVertical = true;
		this._stack.isPointerBlocker = false;
		this._root.addControl(this._stack);

		this._title = new TextBlock('elementPool_title', 'Elements');
		this._title.height = '24px';
		this._title.fontSize = 12;
		this._title.fontWeight = 'bold';
		this._title.color = LABEL_COLOR;
		this._title.isPointerBlocker = false;
		this._stack.addControl(this._title);

		stateStore.on('elementsConsumed', this._onElementsChanged);
		stateStore.on('elementsRestored', this._onElementsChanged);
		stateStore.on('gameStarted', () => this._rebuild());

		this._rebuild();
	}

	private _onElementsChanged = (_data: ElementsChangedData): void => {
		this._rebuild();
	};

	private _rebuild(): void {
		for (const tb of this._elementRows.values()) tb.dispose();
		this._elementRows.clear();

		const myId = this._stateStore.myPlayerId;
		const player = this._stateStore.state?.players[myId];
		if (!player) return;

		const pool = player.elementPool;
		const elements = pool.elements ?? {};
		const maxElements = pool.max_elements ?? {};

		for (const [elemId, current] of Object.entries(elements)) {
			const max = (maxElements as Record<string, number>)[elemId] ?? current;
			const row = new TextBlock(`elemRow_${elemId}`, `  Elem ${elemId}: ${current} / ${max}`);
			row.height = '20px';
			row.fontSize = 11;
			row.color = (current as number) > 0 ? VALUE_COLOR : DEPLETED_COLOR;
			row.textHorizontalAlignment = TextBlock.HORIZONTAL_ALIGNMENT_LEFT;
			row.isPointerBlocker = false;
			this._stack.addControl(row);
			this._elementRows.set(elemId, row);
		}
	}

	dispose(): void {
		this._stateStore.off('elementsConsumed', this._onElementsChanged);
		this._stateStore.off('elementsRestored', this._onElementsChanged);
		this._root.dispose();
	}
}
