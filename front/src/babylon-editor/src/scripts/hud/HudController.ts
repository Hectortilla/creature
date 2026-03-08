import type { Scene } from '@babylonjs/core/scene';
import type { IScript } from 'babylonjs-editor-tools';
import { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';

import GameNetworkManagerComponent from '../game/GameNetworkManagerComponent';
import { CardEntityManager } from '../entities/CardEntityManager';
import InteractionManager from '../interaction/InteractionManager';
import { ActionBuilder } from '../state/ActionBuilder';

import { PhaseIndicator } from './PhaseIndicator';
import { TurnBanner } from './TurnBanner';
import { ElementPoolDisplay } from './ElementPoolDisplay';
import { CardDetailPanel } from './CardDetailPanel';
import { HealthBarManager } from './HealthBar';
import { ActionButtonPanel } from './ActionButtonPanel';
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

	public constructor(scene: Scene) {
		this._scene = scene;
	}

	public onStart(): void {
		const networkManager = GameNetworkManagerComponent.instance;
		if (!networkManager) throw new Error('HudController: GameNetworkManagerComponent not initialized');

		const store = networkManager.getStateStore();
		if (!store) throw new Error('HudController: GameStateStore not initialized');

		const connection = networkManager.getConnection();
		if (!connection) throw new Error('HudController: GameConnection not initialized');

		const cardManager = CardEntityManager.instance;
		if (!cardManager) throw new Error('HudController: CardEntityManager not initialized');

		const interactionManager = getScriptByClassForObject(this._scene, InteractionManager);

		const actionBuilder = new ActionBuilder(store, connection);

		this._guiTexture = AdvancedDynamicTexture.CreateFullscreenUI('GameHUD', true, this._scene);

		this._phaseIndicator = new PhaseIndicator(this._guiTexture, store);
		this._turnBanner = new TurnBanner(this._guiTexture, store);
		this._elementPoolDisplay = new ElementPoolDisplay(this._guiTexture, store);
		this._healthBars = new HealthBarManager(this._guiTexture, store, cardManager);
		this._actionButtons = new ActionButtonPanel(this._guiTexture, store, actionBuilder);

		if (interactionManager) {
			this._cardDetailPanel = new CardDetailPanel(this._guiTexture, interactionManager);
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
		this._guiTexture?.dispose();
	}
}
