import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import { StackPanel } from '@babylonjs/gui/2D/controls/stackPanel';
import type { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';
import type BoardController from '../BoardController';
import type { ElementsChangedData, ElementPoolsUpdatedData, GameStartedEventData } from '../state/events';

const BG_COLOR = 'rgba(15, 10, 40, 0.7)';
const LABEL_COLOR = '#D4AF37';
const VALUE_COLOR = '#FFFFFF';
const DEPLETED_COLOR = 'rgba(255, 255, 255, 0.35)';
const OPPONENT_LABEL_COLOR = '#C0392B';

export class ElementPoolDisplay {
	private _root: Rectangle;
	private _stack: StackPanel;
	private _board: BoardController;
	private _myPlayerId = '';
	private _myRows = new Map<string, TextBlock>();
	private _oppRows = new Map<string, TextBlock>();

	constructor(gui: AdvancedDynamicTexture, board: BoardController) {
		this._board = board;

		this._root = new Rectangle('elementPool_root');
		this._root.width = '210px';
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

		board.on('elementsConsumed', this._onElementsChanged);
		board.on('elementsRestored', this._onElementsChanged);
		board.on('gameStarted', this._onGameStarted);
		board.on('elementPoolsUpdated', this._onPoolsUpdated);
	}

	private _onGameStarted = (data: GameStartedEventData): void => {
		this._myPlayerId = data.myPlayerId;
		this._rebuildAll(
			data.myElementPool.elements,
			data.myElementPool.maxElements,
			data.opponentElementPool.elements,
			data.opponentElementPool.maxElements,
		);
	};

	private _onPoolsUpdated = (data: ElementPoolsUpdatedData): void => {
		this._rebuildAll(
			data.myPool.elements,
			data.myPool.maxElements,
			data.oppPool.elements,
			data.oppPool.maxElements,
		);
	};

	private _onElementsChanged = (data: ElementsChangedData): void => {
		const isMine = data.playerId === this._myPlayerId;
		const rows = isMine ? this._myRows : this._oppRows;
		this._updateRows(rows, data.currentPool, data.maxPool);
	};

	private _rebuildAll(
		myElements: Record<string, number>,
		myMax: Record<string, number>,
		oppElements: Record<string, number>,
		oppMax: Record<string, number>,
	): void {
		for (const tb of this._myRows.values()) tb.dispose();
		for (const tb of this._oppRows.values()) tb.dispose();
		this._myRows.clear();
		this._oppRows.clear();

		// Clear all children and rebuild
		const children = this._stack.children.slice();
		for (const c of children) c.dispose();

		// My elements section
		this._addSectionTitle('My Elements', LABEL_COLOR);
		this._buildRows('my', myElements, myMax, this._myRows);

		// Opponent elements section
		this._addSectionTitle('Opponent', OPPONENT_LABEL_COLOR);
		this._buildRows('opp', oppElements, oppMax, this._oppRows);
	}

	private _addSectionTitle(text: string, color: string): void {
		const title = new TextBlock(`elemTitle_${text}`, text);
		title.height = '32px';
		title.fontSize = 16;
		title.fontWeight = 'bold';
		title.color = color;
		title.isPointerBlocker = false;
		this._stack.addControl(title);
	}

	private _buildRows(
		prefix: string,
		elements: Record<string, number>,
		maxElements: Record<string, number>,
		rows: Map<string, TextBlock>,
	): void {
		for (const [elemId, current] of Object.entries(elements)) {
			const max = maxElements[elemId] ?? current;
			const row = new TextBlock(`elemRow_${prefix}_${elemId}`, `  Elem ${elemId}: ${current} / ${max}`);
			row.height = '26px';
			row.fontSize = 14;
			row.color = (current as number) > 0 ? VALUE_COLOR : DEPLETED_COLOR;
			row.textHorizontalAlignment = TextBlock.HORIZONTAL_ALIGNMENT_LEFT;
			row.isPointerBlocker = false;
			this._stack.addControl(row);
			rows.set(elemId, row);
		}
	}

	private _updateRows(
		rows: Map<string, TextBlock>,
		elements: Record<string, number>,
		maxElements: Record<string, number>,
	): void {
		for (const [elemId, current] of Object.entries(elements)) {
			const max = maxElements[elemId] ?? current;
			const row = rows.get(elemId);
			if (row) {
				row.text = `  Elem ${elemId}: ${current} / ${max}`;
				row.color = (current as number) > 0 ? VALUE_COLOR : DEPLETED_COLOR;
			}
		}
	}

	dispose(): void {
		this._board.off('elementsConsumed', this._onElementsChanged);
		this._board.off('elementsRestored', this._onElementsChanged);
		this._board.off('gameStarted', this._onGameStarted);
		this._board.off('elementPoolsUpdated', this._onPoolsUpdated);
		this._root.dispose();
	}
}
