import type { Scene } from '@babylonjs/core/scene';
import type { IScript } from 'babylonjs-editor-tools';
import { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';

import BoardController from '../BoardController';
import GameConnection from '../game/GameConnection';
import { CardEntityManager } from '../entities/CardEntityManager';

import { PhaseIndicator } from './PhaseIndicator';
import { TurnBanner } from './TurnBanner';
import { ElementPoolDisplay } from './ElementPoolDisplay';
import { CardDetailPanel } from './CardDetailPanel';
import { HealthBarManager } from './HealthBar';
import { ActionButtonPanel } from './ActionButtonPanel';
import { AttackPickerPanel } from './AttackPickerPanel';
import { ForceDefendPanel } from './ForceDefendPanel';
import { ToastPanel } from './ToastPanel';
import InteractionManager from '../interaction/InteractionManager';
import { getScriptByClassForObject } from 'babylonjs-editor-tools';

export default class HudController implements IScript {
	private _scene: Scene;
	private _guiTexture!: AdvancedDynamicTexture;

	private _phaseIndicator!: PhaseIndicator;
	private _turnBanner!: TurnBanner;
	private _elementPoolDisplay!: ElementPoolDisplay;
	private _cardDetailPanel!: CardDetailPanel;
	private _healthBars!: HealthBarManager;
	private _actionButtons!: ActionButtonPanel;
	private _attackPicker!: AttackPickerPanel;
	private _forceDefendPanel: ForceDefendPanel | null = null;
	private _toastPanel!: ToastPanel;

	public constructor(scene: Scene) {
		this._scene = scene;
	}

	public onStart(): void {
		const board = BoardController.instance;
		if (!board) throw new Error('HudController: BoardController not initialized');

		const cardManager = CardEntityManager.getOrCreate(this._scene);
		const interactionManager = getScriptByClassForObject(this._scene, InteractionManager);

		this._guiTexture = AdvancedDynamicTexture.CreateFullscreenUI('GameHUD', true, this._scene);

		this._phaseIndicator = new PhaseIndicator(this._guiTexture, board);
		this._turnBanner = new TurnBanner(this._guiTexture, board);
		this._elementPoolDisplay = new ElementPoolDisplay(this._guiTexture, board);
		this._healthBars = new HealthBarManager(this._guiTexture, board, cardManager);
		this._toastPanel = new ToastPanel(this._guiTexture, board);

		// Reuse the InteractionManager's ActionBuilder — single source of truth
		if (interactionManager) {
			this._actionButtons = new ActionButtonPanel(this._guiTexture, board, interactionManager.actionBuilder);
			this._cardDetailPanel = new CardDetailPanel(this._guiTexture, interactionManager);
			this._attackPicker = new AttackPickerPanel(this._guiTexture);
			interactionManager.setAttackPicker(this._attackPicker);
		}

		const myPlayerId = GameConnection.instance?.getStateStore()?.myPlayerId ?? '';
		if (myPlayerId) {
			this._forceDefendPanel = new ForceDefendPanel(this._guiTexture, board, myPlayerId);
		}
	}

	public onUpdate(): void {
		this._cardDetailPanel?.update();
	}

	public onStop(): void {
		this._phaseIndicator?.dispose();
		this._turnBanner?.dispose();
		this._elementPoolDisplay?.dispose();
		this._cardDetailPanel?.dispose();
		this._healthBars?.dispose();
		this._actionButtons?.dispose();
		this._attackPicker?.dispose();
		this._forceDefendPanel?.dispose();
		this._toastPanel?.dispose();
		this._guiTexture?.dispose();
	}
}
