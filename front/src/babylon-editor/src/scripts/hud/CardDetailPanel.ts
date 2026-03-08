import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import { StackPanel } from '@babylonjs/gui/2D/controls/stackPanel';
import type { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';
import type InteractionManager from '../interaction/InteractionManager';
import type { ClientCard } from '../game/models';

const BG_COLOR = 'rgba(15, 10, 40, 0.85)';
const TITLE_COLOR = '#D4AF37';
const VALUE_COLOR = '#FFFFFF';
const DIM_COLOR = 'rgba(255, 255, 255, 0.6)';

export class CardDetailPanel {
	private _root: Rectangle;
	private _stack: StackPanel;
	private _nameText: TextBlock;
	private _healthText: TextBlock;
	private _defenceText: TextBlock;
	private _attacksText: TextBlock;
	private _interactionManager: InteractionManager;
	private _lastInstanceId: string | null = null;

	constructor(gui: AdvancedDynamicTexture, interactionManager: InteractionManager) {
		this._interactionManager = interactionManager;

		this._root = new Rectangle('cardDetail_root');
		this._root.width = '200px';
		this._root.adaptHeightToChildren = true;
		this._root.left = '-10px';
		this._root.top = '80px';
		this._root.verticalAlignment = Rectangle.VERTICAL_ALIGNMENT_TOP;
		this._root.horizontalAlignment = Rectangle.HORIZONTAL_ALIGNMENT_RIGHT;
		this._root.background = BG_COLOR;
		this._root.cornerRadius = 8;
		this._root.thickness = 0;
		this._root.isPointerBlocker = false;
		this._root.isVisible = false;
		this._root.paddingBottom = '6px';
		gui.addControl(this._root);

		this._stack = new StackPanel('cardDetail_stack');
		this._stack.isVertical = true;
		this._stack.isPointerBlocker = false;
		this._root.addControl(this._stack);

		this._nameText = this._addLine('cardDetail_name', '', TITLE_COLOR, 14, true);
		this._healthText = this._addLine('cardDetail_health', '', VALUE_COLOR, 11, false);
		this._defenceText = this._addLine('cardDetail_defence', '', VALUE_COLOR, 11, false);
		this._attacksText = this._addLine('cardDetail_attacks', '', DIM_COLOR, 10, false);
	}

	/** Called every frame by HudController. */
	update(): void {
		const entity = this._interactionManager.hoveredEntity;
		if (!entity) {
			if (this._root.isVisible) {
				this._root.isVisible = false;
				this._lastInstanceId = null;
			}
			return;
		}

		if (entity.instanceId === this._lastInstanceId) return;
		this._lastInstanceId = entity.instanceId;

		const card = entity.cardData;
		if (!card.faceUp) {
			this._root.isVisible = false;
			return;
		}

		this._populate(card);
		this._root.isVisible = true;
	}

	private _populate(card: ClientCard): void {
		this._nameText.text = card.name || 'Unknown';
		this._healthText.text = `  HP: ${card.currentHealth} / ${card.maxHealth}`;
		this._defenceText.text = `  DEF: ${card.physicalDefence} phys · ${card.magicDefence} mag`;

		if (card.attacks && card.attacks.length > 0) {
			const lines = card.attacks.map(a => `  · ${a.name ?? 'Attack'} (${a.damage ?? '?'} dmg)`);
			this._attacksText.text = lines.join('\n');
		} else {
			this._attacksText.text = '  No attacks';
		}
	}

	private _addLine(name: string, initial: string, color: string, fontSize: number, bold: boolean): TextBlock {
		const tb = new TextBlock(name, initial);
		tb.height = '22px';
		tb.fontSize = fontSize;
		tb.color = color;
		tb.fontWeight = bold ? 'bold' : 'normal';
		tb.textHorizontalAlignment = TextBlock.HORIZONTAL_ALIGNMENT_LEFT;
		tb.textWrapping = true;
		tb.resizeToFit = true;
		tb.isPointerBlocker = false;
		tb.paddingLeft = '8px';
		tb.paddingRight = '8px';
		this._stack.addControl(tb);
		return tb;
	}

	dispose(): void {
		this._root.dispose();
	}
}
