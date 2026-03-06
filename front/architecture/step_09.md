# Step 9: Interaction Manager

> **Depends on:** Step 4 (CardEntityManager), Step 7 (BoardController), Step 8 (ActionBuilder)  
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

1. Get singletons: `CardEntityManager.instance`, `GameStateStore.instance`, `GameNetworkManagerComponent.instance`.
2. Create `ActionBuilder` from store + connection.
3. Register pointer observer on the scene:
   ```typescript
   this._scene.onPointerObservable.add(this.handlePointer);
   ```
4. Subscribe to `stateStore.on("validActionsChanged", ...)` to refresh interactable cards.

### Per-Frame Update (`onUpdate`)

Perform ray picking every frame for hover feedback:

1. If not enabled, clear any hover state and return.
2. Get the picking ray from the scene:
   ```typescript
   const pickResult = this._scene.pick(this._scene.pointerX, this._scene.pointerY);
   ```
3. If pick hit a mesh, look up the `CardEntity`:
   ```typescript
   const entity = this._cardManager.getByMesh(pickResult.pickedMesh);
   ```
4. Update hover state:
   - If entity is different from current `_hoveredEntity`:
     - Reset previous hover: `_hoveredEntity?.setVisualState(previousState)`
     - Set new hover: `entity?.setVisualState(CardVisualState.HOVERED)` (only if interactable)
     - Update `_hoveredEntity`
5. Set cursor style based on whether the hovered entity is interactable:
   ```typescript
   this._scene.getEngine().getRenderingCanvas()!.style.cursor =
     entity && this._interactableIds.has(entity.instanceId) ? "pointer" : "default";
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

  const entity = this._cardManager.getByMesh(pickResult.pickedMesh);
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

  // Check if any action requires a target
  const needsTarget = actions.some(a =>
    a.target_card_id !== undefined ||
    a.attacking_card_id !== undefined
  );

  if (actions.length === 1 && !needsTarget) {
    // Single action, no target needed — execute immediately
    this._actionBuilder.execute(actions[0]);
    return;
  }

  if (needsTarget) {
    // Enter target selection mode
    this._selectedEntity = entity;
    this._selectedEntity.setVisualState(CardVisualState.SELECTED);
    this._selectionMode = "target";
    this._pendingAction = actions[0];  // or show a picker if multiple action types

    // Compute valid targets and highlight them
    const targetIds = this._actionBuilder.getValidTargetIds(actions[0]);
    this._targetIds = new Set(targetIds);
    this.highlightTargets();
    return;
  }

  // Multiple actions on same card, no target — show action menu
  // (For now, execute the first one; a proper UI picker comes in Step 10)
  this._actionBuilder.execute(actions[0]);
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

  // Find the specific action matching source + target
  const sourceId = this._selectedEntity!.instanceId;
  const actions = this._actionBuilder.getActionsForCard(sourceId);
  const matchingAction = actions.find(a =>
    a.target_card_id === entity.instanceId ||
    a.attacking_card_id === entity.instanceId
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

// Apply glow/outline to all interactable cards
private applyInteractableHighlights(): void {
  for (const entity of this._cardManager.getAllEntities()) {
    if (this._interactableIds.has(entity.instanceId)) {
      if (entity.visualState === CardVisualState.IDLE) {
        // Subtle highlight indicating this card can be clicked
        // (different from HOVERED — this is a passive "available" glow)
      }
    } else {
      if (entity !== this._selectedEntity) {
        entity.setVisualState(CardVisualState.IDLE);
      }
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
- Operates on `CardEntity` instances, never on raw meshes for game logic.
- Does NOT know about zone renderers or animation pipeline — it only talks to `ActionBuilder` and `CardEntityManager`.
- `setEnabled(false)` must be called during animations to prevent input during visual transitions.

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

Implement the InteractionManager as specified. Key rules:
1. IScript with onStart, onUpdate, onStop.
2. onUpdate: ray pick every frame for hover feedback (highlight interactable cards on hover).
3. Pointer tap handling: source selection → target selection two-step flow.
4. Uses ActionBuilder.getActionsForCard() to determine what clicking a card does.
5. Supports two-step actions: click source card, highlight valid targets, click target.
6. setEnabled(false) disables all interaction and clears selection state.
7. Subscribes to validActionsChanged to refresh interactable card highlights.
8. Updates cursor style based on whether hovered card is interactable.
9. Register in scripts.ts after creation.
```
