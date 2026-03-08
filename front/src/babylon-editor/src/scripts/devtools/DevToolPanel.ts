import type { Scene } from '@babylonjs/core/scene';
import { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';
import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { StackPanel } from '@babylonjs/gui/2D/controls/stackPanel';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import { Button } from '@babylonjs/gui/2D/controls/button';

import { CardEntityManager } from '../entities/CardEntityManager';
import { DeckZoneRenderer } from '../zones/DeckZoneRenderer';
import type { CardEntity } from '../entities/CardEntity';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import { createDummyCard, resetDummyCardIndex } from './dummyCards';

const DEV_OWNER_ID = 'dev-tool';

const BG_COLOR = 'rgba(15, 10, 40, 0.85)';
const BTN_COLOR = 'rgba(60, 60, 100, 0.9)';
const BTN_HOVER = 'rgba(80, 80, 130, 1.0)';
const CLEAR_COLOR = 'rgba(180, 40, 40, 0.9)';
const CLEAR_HOVER = 'rgba(220, 60, 60, 1.0)';
const TEXT_COLOR = '#FFFFFF';
const TITLE_COLOR = 'rgba(180, 180, 220, 1.0)';

export class DevToolPanel {
	private _scene: Scene;
	private _guiTexture: AdvancedDynamicTexture | null = null;
	private _root: Rectangle | null = null;
	private _visible = false;

	private _cardManager: CardEntityManager;
	private _deckAnchor: TransformNode;
	private _devEntities: CardEntity[] = [];
	private _deckRenderer: DeckZoneRenderer;

	constructor(scene: Scene) {
		this._scene = scene;

		this._cardManager = CardEntityManager.getOrCreate(scene);
		this._cardManager.initBlueprints('UpsideUpCard_BP', 'UpsideDownCard_BP');

		const anchor = scene.getTransformNodeByName('My_Deck_Anchor');
		if (!anchor) throw new Error('DevToolPanel: My_Deck_Anchor not found in scene');
		this._deckAnchor = anchor;

		this._deckRenderer = new DeckZoneRenderer(DEV_OWNER_ID, this._deckAnchor);
	}

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

	get isVisible(): boolean {
		return this._visible;
	}

	dispose(): void {
		this._clearDevCards();
		this._guiTexture?.dispose();
		this._guiTexture = null;
		this._root = null;
	}

	// ── UI ───────────────────────────────────────────────────────────

	private _buildUI(): void {
		this._guiTexture = AdvancedDynamicTexture.CreateFullscreenUI('DevToolUI', true, this._scene);

		this._root = new Rectangle('devTool_root');
		this._root.width = '200px';
		this._root.adaptHeightToChildren = true;
		this._root.left = '10px';
		this._root.top = '10px';
		this._root.verticalAlignment = Rectangle.VERTICAL_ALIGNMENT_TOP;
		this._root.horizontalAlignment = Rectangle.HORIZONTAL_ALIGNMENT_LEFT;
		this._root.background = BG_COLOR;
		this._root.cornerRadius = 8;
		this._root.thickness = 0;
		this._root.paddingTop = '8px';
		this._root.paddingBottom = '8px';
		this._root.isPointerBlocker = false;
		this._guiTexture.addControl(this._root);

		const stack = new StackPanel('devTool_stack');
		stack.isVertical = true;
		stack.isPointerBlocker = false;
		this._root.addControl(stack);

		const title = new TextBlock('devTool_title', 'Dev Tools');
		title.color = TITLE_COLOR;
		title.fontSize = 14;
		title.fontWeight = 'bold';
		title.height = '28px';
		title.paddingBottom = '4px';
		stack.addControl(title);

		this._createButton(stack, 'devBtn_addCard', 'Add Card to Deck', BTN_COLOR, BTN_HOVER, () => this._addCardToDeck());
		this._createButton(stack, 'devBtn_fillDeck', 'Fill Deck (22)', BTN_COLOR, BTN_HOVER, () => this._fillDeck());
		this._createButton(stack, 'devBtn_clear', 'Clear Dev Cards', CLEAR_COLOR, CLEAR_HOVER, () => this._clearDevCards());
	}

	private _createButton(
		parent: StackPanel,
		name: string,
		label: string,
		bgColor: string,
		hoverColor: string,
		onClick: () => void,
	): Button {
		const btn = Button.CreateSimpleButton(name, label);
		btn.width = '170px';
		btn.height = '32px';
		btn.color = TEXT_COLOR;
		btn.fontSize = 12;
		btn.cornerRadius = 6;
		btn.thickness = 0;
		btn.background = bgColor;
		btn.paddingTop = '4px';
		btn.paddingBottom = '4px';
		btn.isPointerBlocker = true;
		btn.onPointerClickObservable.add(onClick);
		btn.onPointerEnterObservable.add(() => { btn.background = hoverColor; });
		btn.onPointerOutObservable.add(() => { btn.background = bgColor; });
		parent.addControl(btn);
		return btn;
	}

	// ── Actions ──────────────────────────────────────────────────────

	private _fillDeck(): void {
		for (let i = 0; i < 22; i++) this._addCardToDeck();
	}

	private _addCardToDeck(): void {
		const entity = this._cardManager.createEntity(createDummyCard(), false);
		this._devEntities.push(entity);
		this._deckRenderer.addCard(entity, false);
	}

	private _clearDevCards(): void {
		const cardManager = CardEntityManager.instance;
		if (cardManager) {
			for (const entity of this._devEntities) {
				cardManager.destroyEntity(entity.instanceId);
			}
		}
		this._devEntities = [];
		this._deckRenderer?.dispose();
		this._deckRenderer = null;
		resetDummyCardIndex();
	}
}
