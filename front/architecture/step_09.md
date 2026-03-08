COMPLETED ✅

# Step 9: Interaction Manager

> **Depends on:** Step 1 (Game Models — `CardVisualState`), Step 2 (GameStateStore), Step 3 (GameNetworkManagerComponent), Step 4 (CardEntityManager), Step 8 (ActionBuilder)  
> **Produces:** `scripts/interaction/InteractionManager.ts`  
> **See also:** [Architecture Overview](./overview.md) — "Layer Descriptions → 8. Interaction Manager"

## Goal

Create the scene script that handles all player input on the 3D board. The `InteractionManager` translates mouse/pointer events into game actions by:

1. **Ray picking** — determining which card (if any) is under the pointer.
2. **Hover feedback** — highlighting interactable cards with glow/outline.
3. **Click handling** — selecting cards and executing actions via `ActionBuilder`.
4. **Target selection** — supporting two-step actions (select source → select target).
5. **Interaction gating** — disabling input while animations are playing.

## What to Implement

### File: `front/src/babylon-editor/src/scripts/interaction/InteractionManager.ts`

```typescript
import type { Scene } from "@babylonjs/core/scene";
import type { IScript } from "babylonjs-editor-tools";
import type { PointerInfo } from "@babylonjs/core/Events/pointerEvents";
import { PointerEventTypes } from "@babylonjs/core/Events/pointerEvents";

class InteractionManager implements IScript {
  private _scene: Scene;
  private _cardManager: CardEntityManager;
  private _actionBuilder: ActionBuilder;
  private _stateStore: GameStateStore;

  // Interaction state
  private _enabled = true;
  private _hoveredEntity: CardEntity | null = null;
  private _selectedEntity: CardEntity | null = null;
  private _interactableIds = new Set<string>();
  private _targetIds = new Set<string>();
  private _pendingAction: ValidAction | null = null;  // for two-step actions

  // Selection mode
  private _selectionMode: "source" | "target" = "source";

  constructor(scene: Scene);

  public onStart(): void;
  public onUpdate(): void;
  public onStop(): void;

  // Called by BoardController to enable/disable during animations
  public setEnabled(enabled: boolean): void;
}
```

### Initialization (`onStart`)

1. Get `GameNetworkManagerComponent.instance` (null-guard with thrown error, same pattern as `BoardController`).
2. Get the state store via `networkManager.getStateStore()` and the connection via `networkManager.getConnection()`.
3. Get `CardEntityManager.instance`.
4. Create `ActionBuilder` from store + connection.
5. Register pointer observer on the scene:
   ```typescript
   this._scene.onPointerObservable.add(this.handlePointer);
   ```
6. Subscribe to `stateStore.on("validActionsChanged", ...)` to refresh interactable cards.

### Per-Frame Update (`onUpdate`)

Perform ray picking every frame for hover feedback:

1. If not enabled, clear any hover state and return.
2. Get the picking ray from the scene:
   ```typescript
   const pickResult = this._scene.pick(this._scene.pointerX, this._scene.pointerY);
   ```
3. If pick hit a mesh, resolve the `CardEntity`. `scene.pick()` returns `AbstractMesh`, so cast to `Mesh`. The picked mesh may be a child of the card root — walk up `mesh.parent` until `CardEntityManager.getByMesh()` returns a match:
   ```typescript
   const entity = this._resolveCardEntity(pickResult.pickedMesh as Mesh);
   ```
4. Update hover state:
   - If entity is the same as current `_hoveredEntity`, no-op.
   - If entity is `_selectedEntity`, don't downgrade it to `HOVERED` — just update cursor.
   - Otherwise:
     - Reset previous hover to `IDLE` (unless it is the `_selectedEntity` or a target).
     - Set new hover: `entity?.setVisualState(CardVisualState.HOVERED)` (only if interactable).
     - Update `_hoveredEntity`.
5. Set cursor style based on whether the hovered entity is interactable:
   ```typescript
   this._scene.getEngine().getRenderingCanvas()!.style.cursor =
     entity && this._interactableIds.has(entity.instanceId) ? "pointer" : "default";
   ```

### Mesh Resolution Helper

Walk up the parent hierarchy to find a registered `CardEntity`:

```typescript
private _resolveCardEntity(mesh: Mesh | null): CardEntity | null {
  let current: Mesh | null = mesh;
  while (current) {
    const entity = this._cardManager.getByMesh(current);
    if (entity) return entity;
    current = current.parent as Mesh | null;
  }
  return null;
}
```

### Pointer Event Handling

```typescript
private handlePointer = (pointerInfo: PointerInfo): void => {
  if (!this._enabled) return;
  if (pointerInfo.type !== PointerEventTypes.POINTERTAP) return;

  const pickResult = pointerInfo.pickInfo;
  if (!pickResult?.hit || !pickResult.pickedMesh) {
    this.clearSelection();
    return;
  }

  const entity = this._resolveCardEntity(pickResult.pickedMesh as Mesh);
  if (!entity) {
    this.clearSelection();
    return;
  }

  if (this._selectionMode === "source") {
    this.handleSourceSelection(entity);
  } else {
    this.handleTargetSelection(entity);
  }
};
```

### Source Selection

```typescript
private handleSourceSelection(entity: CardEntity): void {
  if (!this._interactableIds.has(entity.instanceId)) return;

  const actions = this._actionBuilder.getActionsForCard(entity.instanceId);
  if (actions.length === 0) return;

  // Separate two-step actions (attack, swap, associate, evolve) from instant ones
  const twoStep = actions.filter(a => this._actionBuilder.isTwoStepAction(a));
  const instant = actions.filter(a => !this._actionBuilder.isTwoStepAction(a));

  if (twoStep.length > 0) {
    // Enter target selection mode
    this._selectedEntity = entity;
    this._selectedEntity.setVisualState(CardVisualState.SELECTED);
    this._selectionMode = "target";
    this._pendingAction = twoStep[0];  // TODO: if multiple two-step types exist, show picker (Step 10)

    // Compute valid targets and highlight them
    const targetIds = this._actionBuilder.getValidTargetIds(twoStep[0]);
    this._targetIds = new Set(targetIds);
    this.highlightTargets();
    return;
  }

  if (instant.length === 1) {
    // Single instant action — execute immediately
    this._actionBuilder.execute(instant[0]);
    return;
  }

  // Multiple instant actions on same card — show action menu
  // (For now, execute the first one; a proper UI picker comes in Step 10)
  this._actionBuilder.execute(instant[0]);
}
```

### Target Selection

```typescript
private handleTargetSelection(entity: CardEntity): void {
  if (!this._targetIds.has(entity.instanceId)) {
    // Clicked a non-target — cancel selection
    this.clearSelection();
    return;
  }

  // Find the specific action matching source + target + action type
  const sourceId = this._selectedEntity!.instanceId;
  const actionType = this._pendingAction!.action;
  const actions = this._actionBuilder.getActionsForCard(sourceId);
  const matchingAction = actions.find(a =>
    a.action === actionType &&
    (a.target_card_id === entity.instanceId ||
     a.attacking_card_id === entity.instanceId)
  );

  if (matchingAction) {
    this._actionBuilder.execute(matchingAction);
  }

  this.clearSelection();
}
```

### Helper Methods

```typescript
// Refresh the set of interactable card IDs (called when valid_actions changes)
private refreshInteractableCards(): void {
  this._interactableIds = new Set(this._actionBuilder.getInteractableCardIds());
  this.applyInteractableHighlights();
}

// Apply a subtle outline to all interactable cards so players see which cards
// are clickable, distinct from the brighter HOVERED / SELECTED states.
// Uses renderOutline directly rather than a full CardVisualState, because
// this is an additive "available" indicator — not a mutually exclusive state.
private applyInteractableHighlights(): void {
  for (const entity of this._cardManager.getAllEntities()) {
    if (entity === this._selectedEntity) continue;
    if (this._targetIds.has(entity.instanceId)) continue;

    if (this._interactableIds.has(entity.instanceId)) {
      if (entity.visualState === CardVisualState.IDLE) {
        entity.mesh.renderOutline = true;
        entity.mesh.outlineWidth = 0.01;
        entity.mesh.outlineColor.set(0.5, 0.7, 0.3);  // subtle green "available" glow
      }
    } else {
      entity.setVisualState(CardVisualState.IDLE);
    }
  }
}

// Highlight valid target cards
private highlightTargets(): void {
  for (const entity of this._cardManager.getAllEntities()) {
    if (this._targetIds.has(entity.instanceId)) {
      entity.setVisualState(CardVisualState.HOVERED);  // or a TARGET state
    }
  }
}

// Clear all selection state
private clearSelection(): void {
  this._selectedEntity?.setVisualState(CardVisualState.IDLE);
  this._selectedEntity = null;
  this._selectionMode = "source";
  this._pendingAction = null;
  this._targetIds.clear();
  this.applyInteractableHighlights();
}

// Enable/disable interaction (called by BoardController during animations)
public setEnabled(enabled: boolean): void {
  this._enabled = enabled;
  if (!enabled) {
    this.clearSelection();
    this._hoveredEntity?.setVisualState(CardVisualState.IDLE);
    this._hoveredEntity = null;
  }
}
```

### Scene Script Registration

Register in `scripts.ts` and attach to a scene node (same node as `BoardController`, or a sibling).

## Constraints

- This is an `IScript` scene script — it needs `onStart`, `onUpdate`, `onStop`.
- Uses `scene.pick()` for ray casting — no custom ray math needed.
- `scene.pick()` returns `AbstractMesh` — cast to `Mesh` and walk up the parent hierarchy to find the registered `CardEntity` root mesh.
- Operates on `CardEntity` instances, never on raw meshes for game logic.
- Does NOT know about zone renderers or animation pipeline — it only talks to `ActionBuilder` and `CardEntityManager`.
- `setEnabled(false)` must be called during animations to prevent input during visual transitions.
- **Multi-selection actions** (`multi_play_card`, `multi_swap`) are deferred. `ActionBuilder.getActionsForCard` and `getInteractableCardIds` already handle them for highlight purposes, but the `InteractionManager` only executes single-card actions in this step. Multi-card selection UI will be added in a future iteration.

## Agent Prompt

```
Create `front/src/babylon-editor/src/scripts/interaction/InteractionManager.ts`.

Read these files for context:
- front/architecture/step_09.md (this step's spec)
- front/architecture/overview.md (full architecture)
- front/src/babylon-editor/src/scripts/entities/CardEntity.ts (CardEntity from Step 4)
- front/src/babylon-editor/src/scripts/entities/CardEntityManager.ts (lookups from Step 4)
- front/src/babylon-editor/src/scripts/state/ActionBuilder.ts (action queries from Step 8)
- front/src/babylon-editor/src/scripts/state/GameStateStore.ts (valid actions from Step 2)
- front/src/babylon-editor/src/scripts/game/models.ts (CardVisualState enum)
- front/src/babylon-editor/src/scripts/GameNetworkManagerComponent.ts (getConnection, getStateStore)

Implement the InteractionManager as specified. Key rules:
1. IScript with onStart, onUpdate, onStop.
2. onStart: get dependencies via GameNetworkManagerComponent.instance (getStateStore,
   getConnection), CardEntityManager.instance, then create ActionBuilder.
3. onUpdate: ray pick every frame for hover feedback. scene.pick() returns AbstractMesh —
   cast to Mesh and walk up mesh.parent until CardEntityManager.getByMesh() matches.
   Implement _resolveCardEntity(mesh) helper for this traversal.
4. Hover logic: never overwrite SELECTED with HOVERED. When resetting a previously
   hovered entity, set it to IDLE only if it isn't the selected entity or a target.
5. Pointer tap handling: source selection → target selection two-step flow.
6. Use ActionBuilder.isTwoStepAction() to classify actions instead of checking
   raw field names. Keeps two-step logic in ActionBuilder (DRY).
7. Store _pendingAction when entering target mode. In handleTargetSelection,
   filter by _pendingAction.action to avoid cross-matching different action types
   that share the same source card.
8. setEnabled(false) disables all interaction and clears selection state.
9. Subscribes to validActionsChanged to refresh interactable card highlights.
10. applyInteractableHighlights: use a subtle outline (renderOutline, thin width,
    muted color) for interactable-but-not-hovered cards. Skip selected/target entities.
11. Updates cursor style based on whether hovered card is interactable.
12. Multi-selection actions (multi_play_card, multi_swap) are deferred — only
    single-card actions are handled in this step.
13. Register in scripts.ts after creation.
```
