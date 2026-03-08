# Step 11: Integration & Wiring

> **Depends on:** All previous steps (1–10)  
> **Modifies:** `scripts.ts`, `Battle.scene` anchors, removes old scripts  
> **See also:** [Architecture Overview](./overview.md) — "Existing Code Disposition"

## Goal

Wire everything together, register all new scene scripts, set up the Battle scene with anchor nodes, remove the old `*PosManager` scripts, and clean up backward-compatibility code from `GameNetworkManagerComponent`.

This is the final step that makes the full architecture operational.

## What to Do

### ~~1. Update `scripts.ts` — Remove Old Scripts~~ DONE

~~`BoardController`, `InteractionManager`, and `HudController` are already registered from earlier steps. The only change needed is removing the old position managers.~~

~~Remove these imports and `scriptsMap` entries:~~
- ~~`scripts/DeckCardsPosManager.ts`~~
- ~~`scripts/HandCardsPosManager.ts`~~

~~After cleanup, `scriptsMap` should contain:~~

```typescript
export const scriptsMap = {
  "scripts/GameNetworkManagerComponent.ts": scripts_GameNetworkManagerComponent,
  "scripts/HoverAnimation.ts": scripts_HoverAnimation,
  "scripts/box.ts": scripts_box,
  "scripts/BoardController.ts": scripts_BoardController,
  "scripts/interaction/InteractionManager.ts": scripts_InteractionManager,
  "scripts/hud/HudController.ts": scripts_HudController,
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

~~**No code fallback** — if any anchor node is missing from the scene, `BoardController` should throw an error at startup:~~ DONE

```typescript
private requireAnchor(name: string): TransformNode {
  const node = this._scene.getTransformNodeByName(name);
  if (!node) {
    throw new Error(`Missing required anchor node "${name}" in scene`);
  }
  return node;
}
```

### 3. Attach Scripts to Scene Nodes

In the `Battle.scene`:

1. **`GameNetworkManagerComponent`** — already attached (keep as-is).
2. **`BoardController`** — attach to the root node or a `GameManager` empty node.
3. **`InteractionManager`** — attach to the same node as `BoardController`.
4. **`HudController`** — attach to the same node as `BoardController`. Must share the node with `InteractionManager` because `HudController` uses `_findInteractionManager()` to read `hoveredEntity` for the card detail panel.

Script execution order matters: `GameNetworkManagerComponent` must start first (it creates the store), then `BoardController`, then `InteractionManager` and `HudController`.

### ~~4. Remove Old Scripts~~ DONE

~~Delete the following files (their functionality is now in the new architecture):~~

- ~~`scripts/DeckCardsPosManager.ts`~~
- ~~`scripts/HandCardsPosManager.ts`~~

~~Also remove their entries from `scriptsMap` in `scripts.ts`.~~

### ~~5. Clean Up GameNetworkManagerComponent~~ DONE

~~Now that all consumers use `GameStateStore` instead of the old event APIs:~~

1. ~~**Remove `onGameEvent` / `offGameEvent`** methods and `_gameEventListeners` map.~~
2. ~~**Remove legacy `emit` calls** for `gameStarted`, `validActionsChange`, `gameStateChange` — the store handles these now.~~
3. ~~**Keep:** `on("connectionChange")` and `on("error")` — these are transport-level events that the store doesn't handle.~~
4. ~~**Keep:** `getConnection()` — still needed by `ActionBuilder`.~~
5. ~~**Keep:** `getStateStore()` — the primary way other scripts access the store.~~
6. ~~**Keep:** `getCardCache()` — still needed for card definition lookups by `CardEntityManager` and `BoardController`.~~

### 6. Verify Blueprint Meshes

Ensure the scene contains the two blueprint meshes:

- `"UpsideUpCard_BP"` — face-up card (disabled by default).
- `"UpsideDownCard_BP"` — face-down card (disabled by default).

These are already in the scene from the old implementation. Verify they're still present and disabled.

### ~~7. Verify BabylonJS GUI Dependency~~ DONE

~~`@babylonjs/gui` is already installed (`8.41.0` in `package.json`). Verify it's present — no action needed unless it was removed.~~

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

1. Remove old script entries from `scripts.ts` and verify new ones are present.
2. Add all 10 anchor nodes to the scene (required — no fallbacks).
3. Verify scripts are attached to scene nodes in the correct order.
4. Run the game and verify the full flow works end-to-end.
5. Once verified, delete old scripts (`DeckCardsPosManager`, `HandCardsPosManager`).
6. Clean up `GameNetworkManagerComponent` legacy event APIs (keep `getCardCache()`).
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
1. Update scripts.ts: remove DeckCardsPosManager and HandCardsPosManager imports and scriptsMap entries.
   BoardController, InteractionManager, and HudController are already registered — verify they're present.
2. In BoardController.onStart, add a requireAnchor helper that throws if a scene anchor node is missing.
   All 10 anchor nodes must be present in the scene — no code fallbacks.
3. Delete scripts/DeckCardsPosManager.ts and scripts/HandCardsPosManager.ts.
4. Clean up GameNetworkManagerComponent: remove onGameEvent/offGameEvent and _gameEventListeners
   since all consumers now use GameStateStore. Keep on/off for connectionChange and error events.
   Keep getConnection(), getStateStore(), and getCardCache().
5. Verify that @babylonjs/gui is in package.json dependencies (already installed at 8.41.0).
6. Do NOT modify GameConnection.ts or cloneWithScripts.ts.
```
