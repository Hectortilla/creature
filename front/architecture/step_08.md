# Step 8: Action Builder

> **Depends on:** Step 2 (GameStateStore)  
> **Produces:** `scripts/state/ActionBuilder.ts`  
> **See also:** [Architecture Overview](./overview.md) — "Layer Descriptions → 7. Action Builder"

## Goal

Create the bridge between the backend's `valid_actions` list and the interactive 3D board. The `ActionBuilder` answers questions like: "What can I do with this card?" and "Which cards should glow right now?" — without re-implementing any game rules. It purely reads the `valid_actions` data that the backend already computed.

## What to Implement

### File: `front/src/babylon-editor/src/scripts/state/ActionBuilder.ts`

```typescript
import type { GameConnection } from "../game/GameConnection";
import type { ValidAction, ActionData } from "../game/types";
import { GameStateStore } from "./GameStateStore";
import { Zone, TurnPhase } from "../game/models";

class ActionBuilder {
  private _stateStore: GameStateStore;
  private _connection: GameConnection;

  constructor(stateStore: GameStateStore, connection: GameConnection);

  // ---- Card-level queries ----

  // What actions can the player take involving this specific card?
  getActionsForCard(instanceId: string): ValidAction[];

  // Can this card be interacted with at all right now?
  isCardInteractable(instanceId: string): boolean;

  // ---- Phase-level queries ----

  // Get all cards that can be interacted with in the current phase
  getInteractableCardIds(): string[];

  // Get all cards that are valid targets for a given action
  getValidTargetIds(action: ValidAction): string[];

  // ---- Action categories ----

  // Does the player have a pass action available?
  canPass(): boolean;

  // Does the player have a concede action available?
  canConcede(): boolean;

  // Get pass action if available
  getPassAction(): ValidAction | undefined;

  // Get concede action if available
  getConcedeAction(): ValidAction | undefined;

  // ---- Action execution ----

  // Send an action to the server
  execute(action: ValidAction): void;

  // Convenience: execute by building ActionData from a ValidAction
  private toActionData(action: ValidAction): ActionData;
}
```

### Action Matching Logic

The backend's `valid_actions` contains entries like:

```json
[
  { "action": "play_card", "player_id": "abc", "card_id": "inst_123", "description": "Play Fireling to supporting zone" },
  { "action": "play_card", "player_id": "abc", "card_id": "inst_456", "description": "Play Aqua to supporting zone" },
  { "action": "promote", "player_id": "abc", "card_id": "inst_789", "description": "Promote Stoneguard" },
  { "action": "attack", "player_id": "abc", "attacker_id": "inst_789", "attack_id": 3, "target_card_id": "inst_999" },
  { "action": "pass_phase", "player_id": "abc", "description": "Pass to next phase" },
  { "action": "concede", "player_id": "abc", "description": "Concede the game" }
]
```

**`getActionsForCard(instanceId)`** filters `valid_actions` where ANY of these fields matches:
- `card_id === instanceId`
- `attacker_id === instanceId`
- `supporting_card_id === instanceId`
- `attacking_card_id === instanceId`
- `association_card_id === instanceId`
- `evolution_card_id === instanceId`

**`getInteractableCardIds()`** collects all unique card instance IDs from the above fields across all valid actions (excluding pass/concede).

**`getValidTargetIds(action)`** extracts target-related fields:
- For `attack`: returns valid `target_card_id` values
- For `swap`: returns valid `attacking_card_id` values (when selecting a supporting card first)
- For `association`/`evolution`: returns valid `target_card_id` values

### Two-Step Interaction Pattern

Some actions require two selections (e.g., attack: select attacker THEN select target, swap: select supporting card THEN select attacking card). The `ActionBuilder` supports this by:

1. First click: `getActionsForCard(clickedCardId)` returns multiple actions with different targets.
2. The `InteractionManager` (Step 9) sees multiple targets → enters "target selection" mode.
3. `getValidTargetIds(partialAction)` returns which cards can be targeted.
4. Second click: the specific action matching both source and target is executed.

```typescript
// Example: player clicked attacker_id "abc", now find valid targets
getValidTargetsForAttacker(attackerId: string): string[] {
  return this._stateStore.validActions
    .filter(a => a.action === "attack" && a.attacker_id === attackerId)
    .map(a => a.target_card_id as string)
    .filter(Boolean);
}
```

### `execute(action)`

Converts the `ValidAction` into an `ActionData` and sends it via `GameConnection.sendAction()`:

```typescript
execute(action: ValidAction): void {
  const actionData: ActionData = {
    action_type: action.action,
    ...this.extractActionParams(action),
  };
  this._connection.sendAction(actionData);
}
```

Where `extractActionParams` strips `action`, `player_id`, and `description` from the object, keeping only the action-specific parameters.

## Constraints

- Does NOT re-implement any game rules — purely reads `valid_actions` from the backend.
- Does NOT know about meshes or BabylonJS — works with instance IDs and action data only.
- The `InteractionManager` (Step 9) is the consumer of this class.
- Should be instantiated by the `BoardController` or `InteractionManager`.

## Agent Prompt

```
Create `front/src/babylon-editor/src/scripts/state/ActionBuilder.ts`.

Read these files for context:
- front/architecture/step_08.md (this step's spec)
- front/architecture/overview.md (full architecture)
- front/src/babylon-editor/src/scripts/state/GameStateStore.ts (state store from Step 2)
- front/src/babylon-editor/src/scripts/game/types.ts (ValidAction, ActionData types)
- front/src/babylon-editor/src/scripts/game/GameConnection.ts (sendAction method)
- back/app/game/engine.py (get_valid_actions to see action field names)

Implement the ActionBuilder as specified. Key rules:
1. Reads valid_actions from GameStateStore — never re-implements game rules.
2. getActionsForCard(instanceId) matches against all possible card-referencing fields.
3. getInteractableCardIds() aggregates all card IDs from valid_actions.
4. Supports the two-step interaction pattern (source selection → target selection).
5. execute() converts ValidAction to ActionData and sends via GameConnection.
6. No BabylonJS dependencies — pure data logic.
```
