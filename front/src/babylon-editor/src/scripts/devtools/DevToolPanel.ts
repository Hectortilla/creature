import type { Scene } from '@babylonjs/core/scene';
import { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';
import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { StackPanel } from '@babylonjs/gui/2D/controls/stackPanel';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import { Button } from '@babylonjs/gui/2D/controls/button';

import { CardEntityManager } from '../entities/CardEntityManager';
import type { CardEntity } from '../entities/CardEntity';
import AnimationManager from '../animation/AnimationManager';
import type { Zone } from '../game/models';
import { createDummyCard, resetDummyCardIndex } from './dummyCards';

const DECK_SIZE = 22;
const FILL_DELAY_MS = 100;
const FACE_DOWN_ZONES: ReadonlySet<Zone> = new Set<Zone>(['DECK']);

const ZONE_BUTTONS: { zone: Zone; label: string }[] = [
	{ zone: 'DECK', label: 'Add to Deck' },
	{ zone: 'HAND', label: 'Add to Hand' },
	{ zone: 'SUPPORTING', label: 'Add to Supporting' },
	{ zone: 'ATTACKING', label: 'Add to Attacking' },
	{ zone: 'GRAVEYARD', label: 'Add to Graveyard' },
];

const COLORS = {
	bg: 'rgba(15, 10, 40, 0.85)',
	title: 'rgba(180, 180, 220, 1.0)',
	text: '#FFFFFF',
	btn: 'rgba(60, 60, 100, 0.9)',
	btnHover: 'rgba(80, 80, 130, 1.0)',
	danger: 'rgba(180, 40, 40, 0.9)',
	dangerHover: 'rgba(220, 60, 60, 1.0)',
} as const;

export class DevToolPanel {
	private _scene: Scene;
	private _cardManager: CardEntityManager;
	private _devEntities: CardEntity[] = [];

	private _guiTexture: AdvancedDynamicTexture | null = null;
	private _root: Rectangle | null = null;
	private _visible = false;

	constructor(scene: Scene) {
		this._scene = scene;
		this._cardManager = CardEntityManager.getOrCreate(scene);
		this._cardManager.initBlueprints('UpsideUpCard_BP', 'UpsideDownCard_BP');
	}

	// ── Actions ──────────────────────────────────────────────────────

	private async _addCard(zone: Zone): Promise<void> {
		const renderer = AnimationManager.instance?.getMyRenderer(zone);
		if (!renderer) {
			console.warn(`DevToolPanel: no renderer for zone ${zone} (is a game running?)`);
			return;
		}
		const faceUp = !FACE_DOWN_ZONES.has(zone);
		const entity = this._cardManager.createEntity(createDummyCard(zone), faceUp);
		this._devEntities.push(entity);
		await renderer.addCard(entity, true);
	}

	private _fillZone(zone: Zone, count: number): void {
		for (let i = 0; i < count; i++) {
			setTimeout(() => this._addCard(zone), i * FILL_DELAY_MS);
		}
	}

	private _clearDevCards(): void {
		const anim = AnimationManager.instance;
		for (const entity of this._devEntities) {
			anim?.getMyRenderer(entity.zone)?.removeCard(entity.instanceId);
			this._cardManager.destroyEntity(entity.instanceId);
		}
		this._devEntities = [];
		resetDummyCardIndex();
	}

	// ── Visibility ───────────────────────────────────────────────────

	toggle(): void {
		this._visible ? this.hide() : this.show();
	}

	show(): void {
		if (!this._guiTexture) this._buildUI();
		this._root!.isVisible = true;
		this._visible = true;
	}

	hide(): void {
		if (this._root) this._root.isVisible = false;
		this._visible = false;
	}

	dispose(): void {
		this._clearDevCards();
		this._guiTexture?.dispose();
		this._guiTexture = null;
		this._root = null;
	}

	// ── UI (internal) ────────────────────────────────────────────────

	private _buildUI(): void {
		this._guiTexture = AdvancedDynamicTexture.CreateFullscreenUI('DevToolUI', true, this._scene);

		const stack = new StackPanel('devTool_stack');
		stack.isVertical = true;
		stack.isPointerBlocker = false;

		const title = new TextBlock('devTool_title', 'Dev Tools');
		title.color = COLORS.title;
		title.fontSize = 14;
		title.fontWeight = 'bold';
		title.height = '28px';
		title.paddingBottom = '4px';
		stack.addControl(title);

		for (const { zone, label } of ZONE_BUTTONS) {
			this._addButton(stack, label, COLORS.btn, COLORS.btnHover, () => this._addCard(zone));
		}
		this._addButton(stack, `Fill Deck (${DECK_SIZE})`, COLORS.btn, COLORS.btnHover, () => this._fillZone('DECK', DECK_SIZE));
		this._addButton(stack, 'Clear Dev Cards', COLORS.danger, COLORS.dangerHover, () => this._clearDevCards());

		this._root = this._createPanel(stack);
		this._guiTexture.addControl(this._root);
	}

	private _createPanel(content: StackPanel): Rectangle {
		const panel = new Rectangle('devTool_root');
		panel.width = '200px';
		panel.adaptHeightToChildren = true;
		panel.left = '10px';
		panel.top = '10px';
		panel.verticalAlignment = Rectangle.VERTICAL_ALIGNMENT_TOP;
		panel.horizontalAlignment = Rectangle.HORIZONTAL_ALIGNMENT_LEFT;
		panel.background = COLORS.bg;
		panel.cornerRadius = 8;
		panel.thickness = 0;
		panel.paddingTop = '8px';
		panel.paddingBottom = '8px';
		panel.isPointerBlocker = false;
		panel.addControl(content);
		return panel;
	}

	private _addButton(parent: StackPanel, label: string, bg: string, hover: string, onClick: () => void): void {
		const btn = Button.CreateSimpleButton(`devBtn_${label}`, label);
		btn.width = '170px';
		btn.height = '32px';
		btn.color = COLORS.text;
		btn.fontSize = 12;
		btn.cornerRadius = 6;
		btn.thickness = 0;
		btn.background = bg;
		btn.paddingTop = '4px';
		btn.paddingBottom = '4px';
		btn.isPointerBlocker = true;
		btn.onPointerClickObservable.add(onClick);
		btn.onPointerEnterObservable.add(() => { btn.background = hover; });
		btn.onPointerOutObservable.add(() => { btn.background = bg; });
		parent.addControl(btn);
	}
}
