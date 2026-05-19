import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import { StackPanel } from '@babylonjs/gui/2D/controls/stackPanel';
import { Button } from '@babylonjs/gui/2D/controls/button';
import type { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';

import type { ClientCard, AttackDefinition } from '../game/models';
import { formatAttackLines } from './attackFormat';

const BG_COLOR = 'rgba(15, 10, 40, 0.92)';
const TITLE_COLOR = '#D4AF37';
const ROW_BG = 'rgba(60, 60, 100, 0.9)';
const ROW_HOVER = 'rgba(80, 80, 130, 1.0)';
const ROW_DISABLED = 'rgba(40, 40, 60, 0.5)';
const TEXT_COLOR = '#FFFFFF';
const TEXT_DISABLED = 'rgba(255, 255, 255, 0.35)';
const DIM_COLOR = 'rgba(255, 255, 255, 0.6)';
const CANCEL_COLOR = 'rgba(120, 60, 60, 0.9)';
const CANCEL_HOVER = 'rgba(160, 80, 80, 1.0)';

export type AttackPickerCallback = (attackId: number) => void;

export class AttackPickerPanel {
	private _root: Rectangle;
	private _stack: StackPanel;
	private _onPick: AttackPickerCallback | null = null;
	private _onCancel: (() => void) | null = null;

	constructor(gui: AdvancedDynamicTexture) {
		this._root = new Rectangle('attackPicker_root');
		this._root.width = '460px';
		this._root.adaptHeightToChildren = true;
		this._root.verticalAlignment = Rectangle.VERTICAL_ALIGNMENT_CENTER;
		this._root.horizontalAlignment = Rectangle.HORIZONTAL_ALIGNMENT_CENTER;
		this._root.background = BG_COLOR;
		this._root.cornerRadius = 10;
		this._root.thickness = 0;
		this._root.isPointerBlocker = true;
		this._root.isVisible = false;
		this._root.paddingTop = '8px';
		this._root.paddingBottom = '8px';
		gui.addControl(this._root);

		this._stack = new StackPanel('attackPicker_stack');
		this._stack.isVertical = true;
		this._stack.isPointerBlocker = false;
		this._root.addControl(this._stack);
	}

	public isOpen(): boolean {
		return this._root.isVisible;
	}

	/**
	 * Show the picker for the given attacker. `affordableIds` is the set of
	 * attack_ids that currently have a valid action (sufficient elements +
	 * a valid target or no-defender path). Other attacks are shown disabled.
	 */
	public show(
		card: ClientCard,
		attacks: AttackDefinition[],
		affordableIds: Set<number>,
		onPick: AttackPickerCallback,
		onCancel: () => void,
	): void {
		this._onPick = onPick;
		this._onCancel = onCancel;

		const children = this._stack.children.slice();
		for (const c of children) c.dispose();

		this._addLine(`Choose attack — ${card.name ?? 'Card'}`, TITLE_COLOR, 18, true);

		for (const atk of attacks) {
			const enabled = affordableIds.has(atk.attack_id);
			this._addAttackButton(atk, enabled);
		}

		this._addCancelButton();

		this._root.isVisible = true;
	}

	public hide(): void {
		if (!this._root.isVisible) return;
		this._root.isVisible = false;
		this._onPick = null;
		this._onCancel = null;
	}

	dispose(): void {
		this._root.dispose();
	}

	// ── Private ─────────────────────────────────────────────────────────

	private _addAttackButton(atk: AttackDefinition, enabled: boolean): void {
		const lines = formatAttackLines(atk);

		const btn = Button.CreateSimpleButton(`attackPicker_atk_${atk.attack_id}`, '');
		btn.width = '430px';
		btn.height = '92px';
		btn.cornerRadius = 6;
		btn.thickness = 0;
		btn.background = enabled ? ROW_BG : ROW_DISABLED;
		btn.color = TEXT_COLOR;
		btn.paddingTop = '4px';
		btn.paddingBottom = '4px';
		btn.isPointerBlocker = true;
		btn.isEnabled = enabled;

		const inner = new StackPanel(`attackPicker_atk_${atk.attack_id}_stack`);
		inner.isVertical = true;
		inner.isPointerBlocker = false;
		btn.addControl(inner);

		const titleColor = enabled ? TEXT_COLOR : TEXT_DISABLED;
		const subColor = enabled ? DIM_COLOR : TEXT_DISABLED;

		this._addRow(inner, lines.title, titleColor, 15, true);
		this._addRow(inner, lines.stats, titleColor, 14, false);
		const sub: string[] = [];
		if (lines.cost) sub.push(lines.cost);
		sub.push(lines.id);
		this._addRow(inner, sub.join(' | '), subColor, 13, false);
		if (lines.effect) this._addRow(inner, lines.effect, subColor, 12, false);

		if (enabled) {
			btn.onPointerEnterObservable.add(() => { btn.background = ROW_HOVER; });
			btn.onPointerOutObservable.add(() => { btn.background = ROW_BG; });
			btn.onPointerClickObservable.add(() => {
				const cb = this._onPick;
				if (cb) cb(atk.attack_id);
			});
		}

		this._stack.addControl(btn);
	}

	private _addCancelButton(): void {
		const btn = Button.CreateSimpleButton('attackPicker_cancel', 'Cancel');
		btn.width = '160px';
		btn.height = '36px';
		btn.cornerRadius = 6;
		btn.thickness = 0;
		btn.background = CANCEL_COLOR;
		btn.color = TEXT_COLOR;
		btn.fontSize = 14;
		btn.paddingTop = '6px';
		btn.paddingBottom = '4px';
		btn.isPointerBlocker = true;
		btn.onPointerEnterObservable.add(() => { btn.background = CANCEL_HOVER; });
		btn.onPointerOutObservable.add(() => { btn.background = CANCEL_COLOR; });
		btn.onPointerClickObservable.add(() => {
			const cb = this._onCancel;
			if (cb) cb();
		});
		this._stack.addControl(btn);
	}

	private _addLine(text: string, color: string, fontSize: number, bold: boolean): void {
		const tb = new TextBlock(`attackPicker_line_${Date.now()}_${Math.random()}`, text);
		tb.height = '28px';
		tb.fontSize = fontSize;
		tb.color = color;
		tb.fontWeight = bold ? 'bold' : 'normal';
		tb.textHorizontalAlignment = TextBlock.HORIZONTAL_ALIGNMENT_CENTER;
		tb.resizeToFit = true;
		tb.isPointerBlocker = false;
		tb.paddingTop = '6px';
		tb.paddingBottom = '4px';
		this._stack.addControl(tb);
	}

	private _addRow(parent: StackPanel, text: string, color: string, fontSize: number, bold: boolean): void {
		const tb = new TextBlock(`attackPicker_row_${Date.now()}_${Math.random()}`, text);
		tb.height = '20px';
		tb.fontSize = fontSize;
		tb.color = color;
		tb.fontWeight = bold ? 'bold' : 'normal';
		tb.textHorizontalAlignment = TextBlock.HORIZONTAL_ALIGNMENT_LEFT;
		tb.resizeToFit = true;
		tb.isPointerBlocker = false;
		tb.paddingLeft = '12px';
		tb.paddingRight = '12px';
		parent.addControl(tb);
	}
}
