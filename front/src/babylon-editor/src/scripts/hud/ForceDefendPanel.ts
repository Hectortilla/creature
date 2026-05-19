import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import { StackPanel } from '@babylonjs/gui/2D/controls/stackPanel';
import type { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';

import type BoardController from '../BoardController';
import type { NoDefenderData } from '../state/events';

const BG_COLOR = 'rgba(80, 20, 20, 0.92)';
const TITLE_COLOR = '#FFD37A';
const TEXT_COLOR = '#FFFFFF';

export class ForceDefendPanel {
	private _root: Rectangle;
	private _stack: StackPanel;
	private _board: BoardController;
	private _myPlayerId: string;

	constructor(gui: AdvancedDynamicTexture, board: BoardController, myPlayerId: string) {
		this._board = board;
		this._myPlayerId = myPlayerId;

		this._root = new Rectangle('forceDefend_root');
		this._root.width = '520px';
		this._root.adaptHeightToChildren = true;
		this._root.verticalAlignment = Rectangle.VERTICAL_ALIGNMENT_TOP;
		this._root.horizontalAlignment = Rectangle.HORIZONTAL_ALIGNMENT_CENTER;
		this._root.top = '120px';
		this._root.background = BG_COLOR;
		this._root.cornerRadius = 10;
		this._root.thickness = 0;
		this._root.isPointerBlocker = false;
		this._root.isVisible = false;
		this._root.paddingTop = '10px';
		this._root.paddingBottom = '10px';
		gui.addControl(this._root);

		this._stack = new StackPanel('forceDefend_stack');
		this._stack.isVertical = true;
		this._stack.isPointerBlocker = false;
		this._root.addControl(this._stack);

		board.on('noDefender', this._onNoDefender);
		board.on('phaseChanged', this._hide);
		board.on('turnChanged', this._hide);
		board.on('cardDestroyed', this._hide);
	}

	dispose(): void {
		this._board.off('noDefender', this._onNoDefender);
		this._board.off('phaseChanged', this._hide);
		this._board.off('turnChanged', this._hide);
		this._board.off('cardDestroyed', this._hide);
		this._root.dispose();
	}

	// ── Private ─────────────────────────────────────────────────────────

	private _onNoDefender = (data: NoDefenderData): void => {
		if (data.gameLost) return;
		if (!data.mustDefend) return;
		if (data.defenderId !== this._myPlayerId) return;
		this._show();
	};

	private _hide = (): void => {
		this._root.isVisible = false;
	};

	private _show(): void {
		const children = this._stack.children.slice();
		for (const c of children) c.dispose();

		this._addLine('No Defenders!', TITLE_COLOR, 22, true);
		this._addLine(
			'You have no creatures in your attacking zone.',
			TEXT_COLOR, 15, false,
		);
		this._addLine(
			'Promote a supporting creature to defend.',
			TEXT_COLOR, 15, false,
		);

		this._root.isVisible = true;
	}

	private _addLine(text: string, color: string, fontSize: number, bold: boolean): void {
		const tb = new TextBlock(`forceDefend_line_${Date.now()}_${Math.random()}`, text);
		tb.height = '30px';
		tb.fontSize = fontSize;
		tb.color = color;
		tb.fontWeight = bold ? 'bold' : 'normal';
		tb.textHorizontalAlignment = TextBlock.HORIZONTAL_ALIGNMENT_CENTER;
		tb.textWrapping = true;
		tb.resizeToFit = true;
		tb.isPointerBlocker = false;
		tb.paddingTop = '4px';
		tb.paddingBottom = '4px';
		this._stack.addControl(tb);
	}
}
