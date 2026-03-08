import type { Mesh } from '@babylonjs/core/Meshes/mesh';
import type { Scene } from '@babylonjs/core/scene';
import type { IScript } from 'babylonjs-editor-tools';
import type { PointerInfo } from '@babylonjs/core/Events/pointerEvents';
import { PointerEventTypes } from '@babylonjs/core/Events/pointerEvents';

import GameNetworkManagerComponent from '../GameNetworkManagerComponent';
import { CardEntityManager } from '../entities/CardEntityManager';
import type { CardEntity } from '../entities/CardEntity';
import { CardVisualState } from '../game/models';
import type { ValidAction } from '../game/types';
import { ActionBuilder } from '../state/ActionBuilder';

const INTERACTABLE_OUTLINE_WIDTH = 0.01;
const INTERACTABLE_OUTLINE_COLOR = { r: 0.5, g: 0.7, b: 0.3 };

export default class InteractionManager implements IScript {
	private _scene: Scene;
	private _cardManager!: CardEntityManager;
	private _actionBuilder!: ActionBuilder;

	private _enabled = true;
	private _hoveredEntity: CardEntity | null = null;
	private _selectedEntity: CardEntity | null = null;
	private _interactableIds = new Set<string>();
	private _targetIds = new Set<string>();
	private _pendingAction: ValidAction | null = null;
	private _selectionMode: 'source' | 'target' = 'source';

	private _pointerObserver: ReturnType<Scene['onPointerObservable']['add']> | null = null;

	public constructor(scene: Scene) {
		this._scene = scene;
	}

	// ====================================================================
	// IScript lifecycle
	// ====================================================================

	public onStart(): void {
		const networkManager = GameNetworkManagerComponent.instance;
		if (!networkManager) throw new Error('InteractionManager: GameNetworkManagerComponent not initialized');

		const store = networkManager.getStateStore();
		if (!store) throw new Error('InteractionManager: GameStateStore not initialized');

		const connection = networkManager.getConnection();
		if (!connection) throw new Error('InteractionManager: GameConnection not initialized');

		const cardManager = CardEntityManager.instance;
		if (!cardManager) throw new Error('InteractionManager: CardEntityManager not initialized');
		this._cardManager = cardManager;

		this._actionBuilder = new ActionBuilder(store, connection);

		this._pointerObserver = this._scene.onPointerObservable.add(this._handlePointer);
		store.on('validActionsChanged', this._onValidActionsChanged);
	}

	public onUpdate(): void {
		if (!this._enabled) {
			this._clearHover();
			return;
		}

		const pickResult = this._scene.pick(this._scene.pointerX, this._scene.pointerY);
		const entity = pickResult?.hit && pickResult.pickedMesh
			? this._resolveCardEntity(pickResult.pickedMesh as Mesh)
			: null;

		this._updateHover(entity);
		this._updateCursor(entity);
	}

	public onStop(): void {
		if (this._pointerObserver) {
			this._scene.onPointerObservable.remove(this._pointerObserver);
			this._pointerObserver = null;
		}
	}

	// ====================================================================
	// Public API
	// ====================================================================

	public get hoveredEntity(): CardEntity | null {
		return this._hoveredEntity;
	}

	public setEnabled(enabled: boolean): void {
		this._enabled = enabled;
		if (!enabled) {
			this._clearSelection();
			this._clearHover();
		}
	}

	// ====================================================================
	// Hover
	// ====================================================================

	private _updateHover(entity: CardEntity | null): void {
		if (entity === this._hoveredEntity) return;

		// Reset previous hover (but don't touch selected or target entities)
		if (this._hoveredEntity && this._hoveredEntity !== this._selectedEntity
			&& !this._targetIds.has(this._hoveredEntity.instanceId)) {
			this._hoveredEntity.setVisualState(CardVisualState.IDLE);
			this._applyInteractableOutline(this._hoveredEntity);
		}

		this._hoveredEntity = entity;

		if (!entity) return;
		if (entity === this._selectedEntity) return;
		if (!this._interactableIds.has(entity.instanceId) && !this._targetIds.has(entity.instanceId)) return;

		entity.setVisualState(CardVisualState.HOVERED);
	}

	private _clearHover(): void {
		if (!this._hoveredEntity) return;
		if (this._hoveredEntity !== this._selectedEntity
			&& !this._targetIds.has(this._hoveredEntity.instanceId)) {
			this._hoveredEntity.setVisualState(CardVisualState.IDLE);
			this._applyInteractableOutline(this._hoveredEntity);
		}
		this._hoveredEntity = null;
	}

	private _updateCursor(entity: CardEntity | null): void {
		const canvas = this._scene.getEngine().getRenderingCanvas();
		if (!canvas) return;
		const interactive = entity
			&& (this._interactableIds.has(entity.instanceId) || this._targetIds.has(entity.instanceId));
		canvas.style.cursor = interactive ? 'pointer' : 'default';
	}

	// ====================================================================
	// Pointer tap
	// ====================================================================

	private _handlePointer = (pointerInfo: PointerInfo): void => {
		if (!this._enabled) return;
		if (pointerInfo.type !== PointerEventTypes.POINTERTAP) return;

		const pickResult = pointerInfo.pickInfo;
		if (!pickResult?.hit || !pickResult.pickedMesh) {
			this._clearSelection();
			return;
		}

		const entity = this._resolveCardEntity(pickResult.pickedMesh as Mesh);
		if (!entity) {
			this._clearSelection();
			return;
		}

		if (this._selectionMode === 'source') {
			this._handleSourceSelection(entity);
		} else {
			this._handleTargetSelection(entity);
		}
	};

	// ====================================================================
	// Source selection
	// ====================================================================

	private _handleSourceSelection(entity: CardEntity): void {
		if (!this._interactableIds.has(entity.instanceId)) return;

		const actions = this._actionBuilder.getActionsForCard(entity.instanceId);
		if (actions.length === 0) return;

		const twoStep = actions.filter(a => this._actionBuilder.isTwoStepAction(a));
		const instant = actions.filter(a => !this._actionBuilder.isTwoStepAction(a));

		if (twoStep.length > 0) {
			this._selectedEntity = entity;
			entity.setVisualState(CardVisualState.SELECTED);
			this._selectionMode = 'target';
			this._pendingAction = twoStep[0];

			this._targetIds = new Set(this._actionBuilder.getValidTargetIds(twoStep[0]));
			this._highlightTargets();
			return;
		}

		// Single or multiple instant actions — execute immediately (picker deferred to HUD step)
		if (instant.length > 0) {
			this._actionBuilder.execute(instant[0]);
		}
	}

	// ====================================================================
	// Target selection
	// ====================================================================

	private _handleTargetSelection(entity: CardEntity): void {
		if (!this._targetIds.has(entity.instanceId)) {
			this._clearSelection();
			return;
		}

		const sourceId = this._selectedEntity!.instanceId;
		const actionType = this._pendingAction!.action;
		const matchingAction = this._actionBuilder.getActionsForCard(sourceId).find(a =>
			a.action === actionType
			&& (a.target_card_id === entity.instanceId || a.attacking_card_id === entity.instanceId),
		);

		if (matchingAction) {
			this._actionBuilder.execute(matchingAction);
		}

		this._clearSelection();
	}

	// ====================================================================
	// Highlights
	// ====================================================================

	private _onValidActionsChanged = (): void => {
		this._interactableIds = new Set(this._actionBuilder.getInteractableCardIds());
		this._applyInteractableHighlights();
	};

	private _applyInteractableHighlights(): void {
		for (const entity of this._cardManager.getAllEntities()) {
			if (entity === this._selectedEntity) continue;
			if (this._targetIds.has(entity.instanceId)) continue;

			if (this._interactableIds.has(entity.instanceId)) {
				if (entity.visualState === CardVisualState.IDLE) {
					this._applyInteractableOutline(entity);
				}
			} else {
				entity.setVisualState(CardVisualState.IDLE);
			}
		}
	}

	private _applyInteractableOutline(entity: CardEntity): void {
		if (!this._interactableIds.has(entity.instanceId)) return;
		entity.mesh.renderOutline = true;
		entity.mesh.outlineWidth = INTERACTABLE_OUTLINE_WIDTH;
		entity.mesh.outlineColor.set(
			INTERACTABLE_OUTLINE_COLOR.r,
			INTERACTABLE_OUTLINE_COLOR.g,
			INTERACTABLE_OUTLINE_COLOR.b,
		);
	}

	private _highlightTargets(): void {
		for (const entity of this._cardManager.getAllEntities()) {
			if (this._targetIds.has(entity.instanceId)) {
				entity.setVisualState(CardVisualState.HOVERED);
			}
		}
	}

	// ====================================================================
	// Selection reset
	// ====================================================================

	private _clearSelection(): void {
		this._selectedEntity?.setVisualState(CardVisualState.IDLE);
		this._selectedEntity = null;
		this._selectionMode = 'source';
		this._pendingAction = null;
		this._targetIds.clear();
		this._applyInteractableHighlights();
	}

	// ====================================================================
	// Mesh → CardEntity resolution
	// ====================================================================

	private _resolveCardEntity(mesh: Mesh | null): CardEntity | null {
		let current: Mesh | null = mesh;
		while (current) {
			const entity = this._cardManager.getByMesh(current);
			if (entity) return entity;
			current = current.parent as Mesh | null;
		}
		return null;
	}
}
