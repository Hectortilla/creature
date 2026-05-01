import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import { StackPanel } from '@babylonjs/gui/2D/controls/stackPanel';
import type { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';
import type InteractionManager from '../interaction/InteractionManager';
import type { ClientCard } from '../game/models';
import { formatAttackLines } from './attackFormat';

const BG_COLOR = 'rgba(15, 10, 40, 0.85)';
const TITLE_COLOR = '#D4AF37';
const SECTION_COLOR = '#8888CC';
const VALUE_COLOR = '#FFFFFF';
const DIM_COLOR = 'rgba(255, 255, 255, 0.6)';
const DISABLED_COLOR = 'rgba(255, 255, 255, 0.25)';

export class CardDetailPanel {
	private _root: Rectangle;
	private _stack: StackPanel;
	private _interactionManager: InteractionManager;
	private _lastInstanceId: string | null = null;

	constructor(gui: AdvancedDynamicTexture, interactionManager: InteractionManager) {
		this._interactionManager = interactionManager;

		this._root = new Rectangle('cardDetail_root');
		this._root.width = '420px';
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
		// Clear previous content
		const children = this._stack.children.slice();
		for (const c of children) c.dispose();

		// ── Header ──
		this._addLine(card.name || 'Unknown', TITLE_COLOR, 20, true);
		this._addLine(`id: ${card.card_id}  inst: ${card.instance_id.slice(0, 8)}`, DIM_COLOR, 13, false);

		// ── Status ──
		this._addSection('Status');
		this._addLine(`Zone: ${card.zone} | Status: ${card.status}`, VALUE_COLOR, 14, false);
		this._addLine(`Alive: ${card.is_alive} | Turns in zone: ${card.turns_in_zone}`, VALUE_COLOR, 14, false);
		this._addLine(`Attacked: ${card.has_attacked_this_turn} | Swapped: ${card.swapped_this_turn}`, VALUE_COLOR, 14, false);

		// ── Capabilities ──
		this._addSection('Capabilities');
		this._addLine(`Can Attack: ${card.can_attack} | Can Promote: ${card.can_promote}`, VALUE_COLOR, 14, false);
		this._addLine(`Can Evolve: ${card.can_evolve}`, VALUE_COLOR, 14, false);

		// ── Combat ──
		this._addSection('Combat');
		this._addLine(`HP: ${card.current_health} / ${card.health}`, VALUE_COLOR, 15, false);
		this._addLine(`DEF: ${card.physical_defence} phys | ${card.magic_defence} mag`, VALUE_COLOR, 15, false);

		// ── Elements ──
		this._addSection('Elements');
		this._addLine(`Element IDs: [${(card.element_ids ?? []).join(', ')}]`, VALUE_COLOR, 14, false);
		const contribStr = card.element_contribution?.map((e: { element_id: number; amount: number }) => `e${e.element_id}:${e.amount}`).join(', ') || 'none';
		this._addLine(`Contribution: ${contribStr}`, VALUE_COLOR, 14, false);

		// ── Evolution (conditional) ──
		if (card.evolves_from_id != null) {
			this._addSection('Evolution');
			this._addLine(`Evolves From: ${card.evolves_from_id}`, DIM_COLOR, 14, false);
		}

		// ── Associations (conditional) ──
		if ((card.association_ids ?? []).length > 0 || (card.associations ?? []).length > 0) {
			this._addSection('Associations');
			this._addLine(`Assoc IDs: [${(card.association_ids ?? []).join(', ')}]`, DIM_COLOR, 14, false);
			if ((card.associations ?? []).length > 0) {
				this._addLine(`Active: [${card.associations!.map((s: string) => s.slice(0, 8)).join(', ')}]`, DIM_COLOR, 14, false);
			}
		}

		// ── Skills (conditional) ──
		if ((card.skill_ids ?? []).length > 0) {
			this._addSection('Skills');
			this._addLine(`Skill IDs: [${card.skill_ids!.join(', ')}]`, DIM_COLOR, 14, false);
		}

		// ── Description (conditional) ──
		if (card.description) {
			this._addSection('Description');
			this._addLine(card.description, DIM_COLOR, 14, false);
		}

		// ── Attacks ──
		this._addSection('Attacks');
		if (card.attacks && card.attacks.length > 0) {
			const affordable = this._affordableAttackIds(card);
			for (const atk of card.attacks) {
				const lines = formatAttackLines(atk);
				const isAffordable = affordable.has(atk.attack_id);
				const titleColor = isAffordable ? SECTION_COLOR : DISABLED_COLOR;
				const valueColor = isAffordable ? VALUE_COLOR : DISABLED_COLOR;
				const dimColor = isAffordable ? DIM_COLOR : DISABLED_COLOR;

				this._addLine(lines.title, titleColor, 15, true);
				this._addLine(`  ${lines.stats}`, valueColor, 14, false);
				this._addLine(`  ${lines.id}`, dimColor, 13, false);
				if (lines.cost) this._addLine(`  ${lines.cost}`, dimColor, 14, false);
				if (lines.effect) this._addLine(`  ${lines.effect}`, dimColor, 14, false);
				if (lines.description) this._addLine(`  ${lines.description}`, dimColor, 13, false);
			}
		} else {
			this._addLine('  No attacks', DIM_COLOR, 14, false);
		}
	}

	/**
	 * Returns the set of attack_ids on this card that currently have a
	 * matching ValidAction (sufficient elements + a valid target or
	 * no-defender path). When the player isn't viewing their own attacker
	 * during the ATTACK phase, no actions match and every attack is treated
	 * as informational (and rendered at full brightness).
	 */
	private _affordableAttackIds(card: ClientCard): Set<number> {
		const actions = this._interactionManager.actionBuilder.getActionsForCard(card.instance_id);
		const attackActions = actions.filter(a => a.action === 'attack');
		if (attackActions.length === 0) {
			// Not in an attack-decision context — show all attacks normally.
			return new Set((card.attacks ?? []).map((a: { attack_id: number }) => a.attack_id));
		}
		const ids = new Set<number>();
		for (const a of attackActions) {
			if (typeof a.attack_id === 'number') ids.add(a.attack_id);
		}
		return ids;
	}

	private _addSection(title: string): void {
		const tb = new TextBlock(`cardDetail_sec_${title}`, `— ${title} —`);
		tb.height = '24px';
		tb.fontSize = 14;
		tb.color = SECTION_COLOR;
		tb.fontWeight = 'bold';
		tb.textHorizontalAlignment = TextBlock.HORIZONTAL_ALIGNMENT_LEFT;
		tb.resizeToFit = true;
		tb.isPointerBlocker = false;
		tb.paddingLeft = '12px';
		tb.paddingRight = '12px';
		tb.paddingTop = '6px';
		this._stack.addControl(tb);
	}

	private _addLine(text: string, color: string, fontSize: number, bold: boolean): TextBlock {
		const tb = new TextBlock(`cardDetail_${Date.now()}_${Math.random()}`, text);
		tb.height = '26px';
		tb.fontSize = fontSize;
		tb.color = color;
		tb.fontWeight = bold ? 'bold' : 'normal';
		tb.textHorizontalAlignment = TextBlock.HORIZONTAL_ALIGNMENT_LEFT;
		tb.textWrapping = true;
		tb.resizeToFit = true;
		tb.isPointerBlocker = false;
		tb.paddingLeft = '12px';
		tb.paddingRight = '12px';
		this._stack.addControl(tb);
		return tb;
	}

	dispose(): void {
		this._root.dispose();
	}
}
