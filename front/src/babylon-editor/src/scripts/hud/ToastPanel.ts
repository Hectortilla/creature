import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import type { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';

import type BoardController from '../BoardController';
import type { ActionFailedData } from '../state/events';

const BG_COLOR = 'rgba(120, 30, 30, 0.92)';
const TEXT_COLOR = '#FFFFFF';
const TOAST_DURATION_MS = 3500;

export class ToastPanel {
	private _root: Rectangle;
	private _text: TextBlock;
	private _board: BoardController;
	private _hideTimeout: ReturnType<typeof setTimeout> | null = null;

	constructor(gui: AdvancedDynamicTexture, board: BoardController) {
		this._board = board;

		this._root = new Rectangle('toast_root');
		this._root.width = '480px';
		this._root.height = '52px';
		this._root.verticalAlignment = Rectangle.VERTICAL_ALIGNMENT_BOTTOM;
		this._root.horizontalAlignment = Rectangle.HORIZONTAL_ALIGNMENT_CENTER;
		this._root.top = '-140px';
		this._root.background = BG_COLOR;
		this._root.cornerRadius = 8;
		this._root.thickness = 0;
		this._root.isPointerBlocker = false;
		this._root.isVisible = false;
		gui.addControl(this._root);

		this._text = new TextBlock('toast_text', '');
		this._text.color = TEXT_COLOR;
		this._text.fontSize = 14;
		this._text.textWrapping = true;
		this._text.paddingLeft = '12px';
		this._text.paddingRight = '12px';
		this._text.isPointerBlocker = false;
		this._root.addControl(this._text);

		board.on('actionFailed', this._onActionFailed);
	}

	dispose(): void {
		this._board.off('actionFailed', this._onActionFailed);
		if (this._hideTimeout) clearTimeout(this._hideTimeout);
		this._root.dispose();
	}

	private _onActionFailed = (data: ActionFailedData): void => {
		const code = data.errorCode ? ` [${data.errorCode}]` : '';
		this._text.text = `${data.error}${code}`;
		this._root.isVisible = true;

		if (this._hideTimeout) clearTimeout(this._hideTimeout);
		this._hideTimeout = setTimeout(() => {
			this._root.isVisible = false;
			this._hideTimeout = null;
		}, TOAST_DURATION_MS);
	};
}
