import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import { StackPanel } from '@babylonjs/gui/2D/controls/stackPanel';
import type { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';
import type BoardController from '../BoardController';
import type { ElementsChangedData, GameStartedEventData } from '../state/events';

const BG_COLOR = 'rgba(15, 10, 40, 0.7)';
const LABEL_COLOR = '#D4AF37';
const VALUE_COLOR = '#FFFFFF';
const DEPLETED_COLOR = 'rgba(255, 255, 255, 0.35)';

export class ElementPoolDisplay {
	private _root: Rectangle;
	private _stack: StackPanel;
	private _title: TextBlock;
	private _elementRows = new Map<string, TextBlock>();
	private _board: BoardController;

	constructor(gui: AdvancedDynamicTexture, board: BoardController) {
		this._board = board;

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

		board.on('elementsConsumed', this._onElementsChanged);
		board.on('elementsRestored', this._onElementsChanged);
		board.on('gameStarted', this._onGameStarted);
	}

	private _onGameStarted = (data: GameStartedEventData): void => {
		this._rebuild(data.myElementPool.elements, data.myElementPool.maxElements);
	};

	private _onElementsChanged = (data: ElementsChangedData): void => {
		this._rebuild(data.currentPool, data.maxPool);
	};

	private _rebuild(elements: Record<string, number>, maxElements: Record<string, number>): void {
		for (const tb of this._elementRows.values()) tb.dispose();
		this._elementRows.clear();

		for (const [elemId, current] of Object.entries(elements)) {
			const max = maxElements[elemId] ?? current;
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
		this._board.off('elementsConsumed', this._onElementsChanged);
		this._board.off('elementsRestored', this._onElementsChanged);
		this._board.off('gameStarted', this._onGameStarted);
		this._root.dispose();
	}
}
