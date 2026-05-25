import type { Scene } from '@babylonjs/core/scene';
import type { IScript } from 'babylonjs-editor-tools';
import { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';

import BoardController from '../BoardController';
import GameConnection from '../game/GameConnection';
import { CardEntityManager } from '../entities/CardEntityManager';

import { PhaseIndicator } from './PhaseIndicator';
import { TurnBanner } from './TurnBanner';
import { ElementPoolsBridge } from './bridges/ElementPoolsBridge';
import { HoveredCardBridge } from './bridges/HoveredCardBridge';
import { HealthBarManager } from './HealthBar';
import { ActionButtonPanel } from './ActionButtonPanel';
import { AttackPickerPanel } from './AttackPickerPanel';
import { ForceDefendPanel } from './ForceDefendPanel';
import { ToastPanel } from './ToastPanel';
import InteractionManager from '../interaction/InteractionManager';
import { getScriptByClassForObject } from 'babylonjs-editor-tools';
import type { HoveredCardSetter } from '$lib/stores/babylon/hoveredCard';
import type { ElementPoolsSetter } from '$lib/stores/babylon/elementPools';

export default class HudController implements IScript {
	private _scene: Scene;
	private _guiTexture!: AdvancedDynamicTexture;

	private _phaseIndicator!: PhaseIndicator;
	private _turnBanner!: TurnBanner;
	private _elementPoolsBridge: ElementPoolsBridge | null = null;
	private _pendingElementPoolsSetter: ElementPoolsSetter | null = null;
	private _hoveredCardBridge: HoveredCardBridge | null = null;
	private _pendingHoveredCardSetter: HoveredCardSetter | null = null;
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
		this._elementPoolsBridge = new ElementPoolsBridge(board);
		if (this._pendingElementPoolsSetter) {
			this._elementPoolsBridge.setSetter(this._pendingElementPoolsSetter);
			this._pendingElementPoolsSetter = null;
		}
		this._healthBars = new HealthBarManager(this._guiTexture, board, cardManager);
		this._toastPanel = new ToastPanel(this._guiTexture, board);

		// Reuse the InteractionManager's ActionBuilder — single source of truth
		if (interactionManager) {
			this._actionButtons = new ActionButtonPanel(this._guiTexture, board, interactionManager.actionBuilder);
			this._hoveredCardBridge = new HoveredCardBridge(interactionManager);
			if (this._pendingHoveredCardSetter) {
				this._hoveredCardBridge.setSetter(this._pendingHoveredCardSetter);
				this._pendingHoveredCardSetter = null;
			}
			this._attackPicker = new AttackPickerPanel(this._guiTexture);
			interactionManager.setAttackPicker(this._attackPicker);
		}

		const myPlayerId = GameConnection.instance?.getStateStore()?.myPlayerId ?? '';
		if (myPlayerId) {
			this._forceDefendPanel = new ForceDefendPanel(this._guiTexture, board, myPlayerId);
		}
	}

	public onUpdate(): void {
		this._hoveredCardBridge?.update();
	}

	public setHoveredCardSetter(fn: HoveredCardSetter): void {
		if (this._hoveredCardBridge) {
			this._hoveredCardBridge.setSetter(fn);
		} else {
			this._pendingHoveredCardSetter = fn;
		}
	}

	public setElementPoolsSetter(fn: ElementPoolsSetter): void {
		if (this._elementPoolsBridge) {
			this._elementPoolsBridge.setSetter(fn);
		} else {
			this._pendingElementPoolsSetter = fn;
		}
	}

	public onStop(): void {
		this._phaseIndicator?.dispose();
		this._turnBanner?.dispose();
		this._elementPoolsBridge?.dispose();
		this._healthBars?.dispose();
		this._actionButtons?.dispose();
		this._attackPicker?.dispose();
		this._forceDefendPanel?.dispose();
		this._toastPanel?.dispose();
		this._guiTexture?.dispose();
	}
}
