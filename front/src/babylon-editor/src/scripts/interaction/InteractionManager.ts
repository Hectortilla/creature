import type { Mesh } from '@babylonjs/core/Meshes/mesh';
import type { Scene } from '@babylonjs/core/scene';
import type { IScript } from 'babylonjs-editor-tools';
import type { PointerInfo } from '@babylonjs/core/Events/pointerEvents';
import { PointerEventTypes } from '@babylonjs/core/Events/pointerEvents';

import GameConnection from '../game/GameConnection';
import BoardController from '../BoardController';
import { CardEntityManager } from '../entities/CardEntityManager';
import type { CardEntity } from '../entities/CardEntity';
import { CardVisualState } from '../game/models';
import type { ValidAction } from '../game/types';
import { ActionBuilder } from '../state/ActionBuilder';
import type { ValidActionsChangedData } from '../state/events';
import type { AttackPickerPanel } from '../hud/AttackPickerPanel';

const INTERACTABLE_OUTLINE_WIDTH = 0.01;
const INTERACTABLE_OUTLINE_COLOR = { r: 0.5, g: 0.7, b: 0.3 };

type SelectionMode = 'source' | 'attackPick' | 'target';

export default class InteractionManager implements IScript {
	private _scene: Scene;
	private _board!: BoardController;
	private _cardManager!: CardEntityManager;
	public actionBuilder!: ActionBuilder;

	private _enabled = true;
	private _hoveredEntity: CardEntity | null = null;
	private _selectedEntity: CardEntity | null = null;
	private _interactableIds = new Set<string>();
	private _targetIds = new Set<string>();
	private _pendingAction: ValidAction | null = null;
	private _pendingAttackId: number | null = null;
	private _selectionMode: SelectionMode = 'source';

	private _attackPicker: AttackPickerPanel | null = null;

	private _pointerObserver: ReturnType<Scene['onPointerObservable']['add']> | null = null;

	public constructor(scene: Scene) {
		this._scene = scene;
	}

	// ====================================================================
	// IScript lifecycle
	// ====================================================================

	public onStart(): void {
		const board = BoardController.instance;
		if (!board) throw new Error('InteractionManager: BoardController not initialized');
		this._board = board;

		const conn = GameConnection.instance;
		if (!conn) throw new Error('InteractionManager: GameConnection not initialized');

		this._cardManager = CardEntityManager.getOrCreate(this._scene);

		this.actionBuilder = new ActionBuilder(conn);

		this._pointerObserver = this._scene.onPointerObservable.add(this._handlePointer);
		board.on('validActionsChanged', this._onValidActionsChanged);
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

	public setAttackPicker(panel: AttackPickerPanel): void {
		this._attackPicker = panel;
	}

	// ====================================================================
	// Hover
	// ====================================================================

	private _updateHover(entity: CardEntity | null): void {
		if (entity === this._hoveredEntity) return;

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

		// Ignore board clicks while the attack picker is open — picker handles its own input.
		if (this._selectionMode === 'attackPick') return;

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
		} else if (this._selectionMode === 'target') {
			this._handleTargetSelection(entity);
		}
	};

	// ====================================================================
	// Source selection
	// ====================================================================

	private _handleSourceSelection(entity: CardEntity): void {
		if (!this._interactableIds.has(entity.instanceId)) return;

		const actions = this.actionBuilder.getActionsForCard(entity.instanceId);
		if (actions.length === 0) return;

		const attackActions = actions.filter(a => a.action === 'attack');
		const otherTwoStep = actions.filter(a => a.action !== 'attack' && this.actionBuilder.isTwoStepAction(a));
		const instant = actions.filter(a => !this.actionBuilder.isTwoStepAction(a));

		// 1. Attack flow (may need a picker for multi-attack cards)
		if (attackActions.length > 0) {
			this._beginAttackFlow(entity);
			return;
		}

		// 2. Other two-step actions (swap, associate, evolve)
		if (otherTwoStep.length > 0) {
			this._enterTargetMode(entity, otherTwoStep[0]);
			return;
		}

		// 3. Instant actions
		if (instant.length > 0) {
			this.actionBuilder.execute(instant[0]);
		}
	}

	// ====================================================================
	// Attack flow
	// ====================================================================

	private _beginAttackFlow(entity: CardEntity): void {
		const attackIds = this.actionBuilder.getAttackIdsForAttacker(entity.instanceId);
		if (attackIds.length === 0) return;

		// Single available attack — skip the picker.
		if (attackIds.length === 1) {
			this._commitAttackChoice(entity, attackIds[0]);
			return;
		}

		// Multiple available attacks — open the picker. If the picker isn't
		// installed yet (HudController hasn't wired it), fall back to the
		// first available attack so the player isn't stuck.
		if (!this._attackPicker) {
			this._commitAttackChoice(entity, attackIds[0]);
			return;
		}

		const cardData = entity.cardData;
		const allAttacks = cardData.attacks ?? [];
		const affordable = new Set<number>(attackIds);

		this._selectedEntity = entity;
		entity.setVisualState(CardVisualState.SELECTED);
		this._selectionMode = 'attackPick';

		this._attackPicker.show(
			cardData,
			allAttacks,
			affordable,
			(attackId) => this._onAttackPicked(attackId),
			() => this._onAttackPickCancelled(),
		);
	}

	private _onAttackPicked(attackId: number): void {
		this._attackPicker?.hide();
		const entity = this._selectedEntity;
		if (!entity) {
			this._clearSelection();
			return;
		}
		this._commitAttackChoice(entity, attackId);
	}

	private _onAttackPickCancelled(): void {
		this._attackPicker?.hide();
		this._clearSelection();
	}

	private _commitAttackChoice(entity: CardEntity, attackId: number): void {
		this._pendingAttackId = attackId;

		// Find the candidate actions for this attacker × attack pair.
		const candidates = this.actionBuilder
			.getActionsForCard(entity.instanceId)
			.filter(a => a.action === 'attack' && a.attack_id === attackId);

		if (candidates.length === 0) {
			this._clearSelection();
			return;
		}

		// No-defender shortcut: opponent has no attacking creatures, so the
		// only matching action has target_card_id="". Fire immediately.
		const noDefenderAction = candidates.find(a => !(a.target_card_id ?? ''));
		const targetedActions = candidates.filter(a => !!(a.target_card_id ?? ''));

		if (targetedActions.length === 0 && noDefenderAction) {
			this.actionBuilder.execute(noDefenderAction);
			this._clearSelection();
			return;
		}

		this._enterTargetMode(entity, targetedActions[0] ?? candidates[0]);
	}

	// ====================================================================
	// Target selection
	// ====================================================================

	private _enterTargetMode(entity: CardEntity, action: ValidAction): void {
		this._selectedEntity = entity;
		entity.setVisualState(CardVisualState.SELECTED);
		this._selectionMode = 'target';
		this._pendingAction = action;

		this._targetIds = new Set(this.actionBuilder.getValidTargetIds(action));
		this._highlightTargets();
	}

	private _handleTargetSelection(entity: CardEntity): void {
		if (!this._targetIds.has(entity.instanceId)) {
			this._clearSelection();
			return;
		}

		const sourceId = this._selectedEntity!.instanceId;
		const targetId = entity.instanceId;
		const actionType = this._pendingAction!.action;

		let matchingAction: ValidAction | undefined;

		if (actionType === 'attack' && this._pendingAttackId != null) {
			matchingAction = this.actionBuilder.findAttackAction(
				sourceId, this._pendingAttackId, targetId,
			);
		} else {
			matchingAction = this.actionBuilder.getActionsForCard(sourceId).find(a =>
				a.action === actionType
				&& (a.target_card_id === targetId || a.attacking_card_id === targetId),
			);
		}

		if (matchingAction) {
			this.actionBuilder.execute(matchingAction);
		}

		this._clearSelection();
	}

	// ====================================================================
	// Highlights
	// ====================================================================

	private _onValidActionsChanged = (data: ValidActionsChangedData): void => {
		this.actionBuilder.setValidActions(data.actions);
		this._interactableIds = new Set(this.actionBuilder.getInteractableCardIds());
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
		this._attackPicker?.hide();
		this._selectedEntity?.setVisualState(CardVisualState.IDLE);
		this._selectedEntity = null;
		this._selectionMode = 'source';
		this._pendingAction = null;
		this._pendingAttackId = null;
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
