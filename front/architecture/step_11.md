# Step 11: Integration & Wiring

> **Depends on:** All previous steps (1–10)  
> **Modifies:** `scripts.ts`, `Battle.scene` anchors, removes old scripts  
> **See also:** [Architecture Overview](./overview.md) — "Existing Code Disposition"

## Goal

Wire everything together, register all new scene scripts, set up the Battle scene with anchor nodes, remove the old `*PosManager` scripts, and clean up backward-compatibility code from `GameNetworkManagerComponent`.

This is the final step that makes the full architecture operational.

## What to Do

### 1. Update `scripts.ts` — Register All New Scene Scripts

The following scripts need to be imported and added to `scriptsMap`:

```typescript
import scripts_BoardController from "./scripts/BoardController";
import scripts_InteractionManager from "./scripts/interaction/InteractionManager";
import scripts_HudController from "./scripts/hud/HudController";

export const scriptsMap = {
  // Existing
  "scripts/GameNetworkManagerComponent.ts": scripts_GameNetworkManagerComponent,
  "scripts/HoverAnimation.ts": scripts_HoverAnimation,

  // New
  "scripts/BoardController.ts": scripts_BoardController,
  "scripts/interaction/InteractionManager.ts": scripts_InteractionManager,
  "scripts/hud/HudController.ts": scripts_HudController,

  // Remove these (old)
  // "scripts/DeckCardsPosManager.ts": scripts_DeckCardsPosManager,
  // "scripts/HandCardsPosManager.ts": scripts_HandCardsPosManager,
};
```

### 2. Set Up Battle Scene Anchor Nodes

In the `Battle.scene` (or via code in `BoardController.onStart`), create empty `TransformNode` markers for all zones:

**Option A: Scene editor** (preferred)  
Add empty nodes in the BabylonJS Editor with these exact names and appropriate positions:

| Node Name | Position (approximate) | Purpose |
|---|---|---|
| `My_Deck_Anchor` | Right side, near player | Local player's deck pile |
| `My_Hand_Anchor` | Center-bottom, toward camera | Local player's hand fan |
| `My_Supporting_Anchor` | Center, inner row | Local player's supporting zone |
| `My_Attacking_Anchor` | Center, middle row | Local player's attacking zone |
| `My_Graveyard_Anchor` | Left side, near player | Local player's graveyard |
| `Opp_Deck_Anchor` | Right side, far from camera | Opponent's deck |
| `Opp_Hand_Anchor` | Center-top, away from camera | Opponent's hand |
| `Opp_Supporting_Anchor` | Center, inner row (opponent side) | Opponent's supporting zone |
| `Opp_Attacking_Anchor` | Center, middle row (opponent side) | Opponent's attacking zone |
| `Opp_Graveyard_Anchor` | Left side, far from camera | Opponent's graveyard |

**Option B: Code fallback**  
`BoardController` creates `TransformNode` objects programmatically with default positions if scene nodes aren't found:

```typescript
private getOrCreateAnchor(name: string, fallbackPosition: Vector3): TransformNode {
  let node = this._scene.getTransformNodeByName(name);
  if (!node) {
    node = new TransformNode(name, this._scene);
    node.position = fallbackPosition;
  }
  return node;
}
```

### 3. Attach Scripts to Scene Nodes

In the `Battle.scene`:

1. **`GameNetworkManagerComponent`** — already attached (keep as-is).
2. **`BoardController`** — attach to the root node or a `GameManager` empty node.
3. **`InteractionManager`** — attach to the same node as `BoardController`.
4. **`HudController`** — attach to the same node as `BoardController`.

Script execution order matters: `GameNetworkManagerComponent` must start first (it creates the store), then `BoardController`, then `InteractionManager` and `HudController`.

### 4. Remove Old Scripts

Delete the following files (their functionality is now in the new architecture):

- `scripts/DeckCardsPosManager.ts`
- `scripts/HandCardsPosManager.ts`

Also remove their entries from `scriptsMap` in `scripts.ts`.

### 5. Clean Up GameNetworkManagerComponent

Now that all consumers use `GameStateStore` instead of the old event APIs:

1. **Remove `onGameEvent` / `offGameEvent`** methods and `_gameEventListeners` map.
2. **Remove legacy `emit` calls** for `gameStarted`, `validActionsChange`, `gameStateChange` — the store handles these now.
3. **Keep:** `on("connectionChange")` and `on("error")` — these are transport-level events that the store doesn't handle.
4. **Keep:** `getConnection()` — still needed by `ActionBuilder`.
5. **Keep:** `getStateStore()` — the primary way other scripts access the store.

### 6. Verify Blueprint Meshes

Ensure the scene contains the two blueprint meshes:

- `"UpsideUpCard_BP"` — face-up card (disabled by default).
- `"UpsideDownCard_BP"` — face-down card (disabled by default).

These are already in the scene from the old implementation. Verify they're still present and disabled.

### 7. Install BabylonJS GUI Dependency

If not already installed, add `@babylonjs/gui` to the project:

```bash
cd front/src/babylon-editor
npm install @babylonjs/gui
```

### 8. Smoke Test Checklist

After integration, verify:

- [ ] WebSocket connects successfully
- [ ] `GameStateStore` receives and processes `game_started` event
- [ ] `BoardController` creates card entities for all initial cards
- [ ] Deck appears as a stack at `My_Deck_Anchor` and `Opp_Deck_Anchor`
- [ ] Hand cards fan out at `My_Hand_Anchor` after draw events
- [ ] Phase indicator shows and updates with phase changes
- [ ] Clicking an interactable hand card during PLACEMENT sends `play_card` action
- [ ] Card animates from hand → supporting zone
- [ ] Pass button advances to next phase
- [ ] Opponent's cards appear on the opposite side of the board
- [ ] Health bars appear above field cards
- [ ] Attack flow works: select attacker → highlight targets → select target → animation plays
- [ ] Game over detection and display

## Order of Operations

Recommended implementation order within this step:

1. Update `scripts.ts` with new imports.
2. Add anchor nodes to the scene (or verify code fallbacks work).
3. Attach new scripts to scene nodes.
4. Run the game and verify the full flow works end-to-end.
5. Once verified, delete old scripts (`DeckCardsPosManager`, `HandCardsPosManager`).
6. Clean up `GameNetworkManagerComponent` legacy event APIs.
7. Final smoke test.

## Agent Prompt

```
Perform the final integration of the card game architecture.

Read these files for context:
- front/architecture/step_11.md (this step's spec)
- front/architecture/overview.md (full architecture)
- front/src/babylon-editor/src/scripts.ts (current script registration)
- front/src/babylon-editor/src/scripts/GameNetworkManagerComponent.ts
- front/src/babylon-editor/src/scripts/BoardController.ts (from Step 7)
- front/src/babylon-editor/src/scripts/interaction/InteractionManager.ts (from Step 9)
- front/src/babylon-editor/src/scripts/hud/HudController.ts (from Step 10)

Tasks:
1. Update scripts.ts: add imports and registrations for BoardController, InteractionManager, HudController.
   Remove DeckCardsPosManager and HandCardsPosManager registrations.
2. In BoardController.onStart, add fallback code to create TransformNode anchors with default positions
   if they don't exist in the scene (getOrCreateAnchor helper).
3. Delete scripts/DeckCardsPosManager.ts and scripts/HandCardsPosManager.ts.
4. Clean up GameNetworkManagerComponent: remove onGameEvent/offGameEvent and _gameEventListeners
   since all consumers now use GameStateStore. Keep on/off for connectionChange and error events.
   Keep getConnection() and getStateStore().
5. Verify that @babylonjs/gui is in package.json dependencies. If not, note that it needs to be installed.
6. Do NOT modify GameConnection.ts or cloneWithScripts.ts.
```
