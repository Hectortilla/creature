import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import { StackPanel } from '@babylonjs/gui/2D/controls/stackPanel';
import { Button } from '@babylonjs/gui/2D/controls/button';
import type { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';
import type { ActionBuilder } from '../state/ActionBuilder';
import type BoardController from '../BoardController';
import type { ValidActionsChangedData } from '../state/events';

const BG_COLOR = 'rgba(15, 10, 40, 0.7)';
const BTN_COLOR = 'rgba(60, 60, 100, 0.9)';
const BTN_HOVER = 'rgba(80, 80, 130, 1.0)';
const BTN_DISABLED = 'rgba(40, 40, 60, 0.5)';
const TEXT_COLOR = '#FFFFFF';
const TEXT_DISABLED = 'rgba(255, 255, 255, 0.35)';
const CONCEDE_COLOR = 'rgba(180, 40, 40, 0.9)';
const CONCEDE_HOVER = 'rgba(220, 60, 60, 1.0)';

export class ActionButtonPanel {
	private _root: Rectangle;
	private _passBtn: Button;
	private _concedeBtn: Button;
	private _board: BoardController;
	private _actionBuilder: ActionBuilder;
	private _isMyTurn = false;
	private _confirmingConcede = false;

	constructor(gui: AdvancedDynamicTexture, board: BoardController, actionBuilder: ActionBuilder) {
		this._board = board;
		this._actionBuilder = actionBuilder;

		this._root = new Rectangle('actionBtnPanel_root');
		this._root.width = '240px';
		this._root.height = '120px';
		this._root.left = '-10px';
		this._root.top = '-10px';
		this._root.verticalAlignment = Rectangle.VERTICAL_ALIGNMENT_BOTTOM;
		this._root.horizontalAlignment = Rectangle.HORIZONTAL_ALIGNMENT_RIGHT;
		this._root.background = BG_COLOR;
		this._root.cornerRadius = 8;
		this._root.thickness = 0;
		this._root.isPointerBlocker = false;
		gui.addControl(this._root);

		const stack = new StackPanel('actionBtnPanel_stack');
		stack.isVertical = true;
		stack.isPointerBlocker = false;
		stack.verticalAlignment = StackPanel.VERTICAL_ALIGNMENT_CENTER;
		this._root.addControl(stack);

		this._passBtn = this._createButton(stack, 'btn_pass', 'Pass Phase', BTN_COLOR, () => this._onPass());
		this._concedeBtn = this._createButton(stack, 'btn_concede', 'Concede', CONCEDE_COLOR, () => this._onConcede());

		board.on('validActionsChanged', this._onActionsChanged);
		board.on('phaseChanged', () => this._refresh());
		board.on('turnChanged', () => { this._confirmingConcede = false; this._refresh(); });

		this._refresh();
	}

	private _createButton(
		parent: StackPanel,
		name: string,
		label: string,
		bgColor: string,
		onClick: () => void,
	): Button {
		const btn = Button.CreateSimpleButton(name, label);
		btn.width = '200px';
		btn.height = '44px';
		btn.color = TEXT_COLOR;
		btn.fontSize = 16;
		btn.cornerRadius = 6;
		btn.thickness = 0;
		btn.background = bgColor;
		btn.paddingTop = '6px';
		btn.paddingBottom = '6px';
		btn.isPointerBlocker = true;
		btn.onPointerClickObservable.add(onClick);
		btn.onPointerEnterObservable.add(() => {
			if (!btn.isEnabled) return;
			btn.background = name === 'btn_concede' ? CONCEDE_HOVER : BTN_HOVER;
		});
		btn.onPointerOutObservable.add(() => {
			if (!btn.isEnabled) return;
			btn.background = name === 'btn_concede' ? CONCEDE_COLOR : BTN_COLOR;
		});
		parent.addControl(btn);
		return btn;
	}

	private _onActionsChanged = (data: ValidActionsChangedData): void => {
		// ActionBuilder is shared with InteractionManager which already calls setValidActions
		this._isMyTurn = data.isMyTurn;
		this._refresh();
	};

	private _refresh(): void {
		const canPass = this._actionBuilder.canPass() && this._isMyTurn;
		this._setButtonEnabled(this._passBtn, canPass, BTN_COLOR);

		const canConcede = this._actionBuilder.canConcede();
		this._setButtonEnabled(this._concedeBtn, canConcede, CONCEDE_COLOR);

		if (this._confirmingConcede) {
			(this._concedeBtn.textBlock as TextBlock).text = 'Confirm?';
		} else {
			(this._concedeBtn.textBlock as TextBlock).text = 'Concede';
		}
	}

	private _setButtonEnabled(btn: Button, enabled: boolean, activeColor: string): void {
		btn.isEnabled = enabled;
		btn.background = enabled ? activeColor : BTN_DISABLED;
		if (btn.textBlock) btn.textBlock.color = enabled ? TEXT_COLOR : TEXT_DISABLED;
	}

	private _onPass(): void {
		const action = this._actionBuilder.getPassAction();
		if (action) this._actionBuilder.execute(action);
	}

	private _onConcede(): void {
		if (!this._confirmingConcede) {
			this._confirmingConcede = true;
			this._refresh();
			return;
		}
		this._confirmingConcede = false;
		const action = this._actionBuilder.getConcedeAction();
		if (action) this._actionBuilder.execute(action);
		this._refresh();
	}

	dispose(): void {
		this._board.off('validActionsChanged', this._onActionsChanged);
		this._root.dispose();
	}
}
