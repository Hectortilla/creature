COMPLETED ✅

# Step 7: Board Controller

> **Depends on:** Step 2 (GameStateStore), Step 4 (CardEntityManager), Step 5 (Zone Renderers), Step 6 (AnimationPipeline)  
> **Produces:** `scripts/BoardController.ts`  
> **See also:** [Architecture Overview](./overview.md) — "Layer Descriptions → 6. Board Controller"

## Goal

Create the **single orchestrator** scene script that bridges the game state to the 3D world. The `BoardController` is the only component that subscribes to `GameStateStore` change events and translates them into entity creation/destruction, zone renderer updates, and animation pipeline commands.

This is the central nervous system of the visual game — no other script should listen to state changes or manage card visuals directly.

## Prerequisite: Add `cardsSwapped` event to GameStateStore

The `GameStateStore._handleCardSwapped()` currently emits two separate `cardMoved` events. This prevents the `BoardController` from batching them into a `ParallelAnimation` (two cards crossing paths simultaneously). Add a dedicated event:

**New interface (in `GameStateStore.ts`):**
```typescript
export interface CardsSwappedData {
  ownerId: string;
  supportingId: string;
  attackingId: string;
}
```

**Add to `StateChangeEvents`:**
```typescript
cardsSwapped: CardsSwappedData;
```

**In `_handleCardSwapped()`** — emit after the existing two `cardMoved` emissions:
```typescript
this._emit('cardsSwapped', {
  ownerId: playerId,
  supportingId,
  attackingId,
});
```

The two `cardMoved` events remain (other listeners may need them), but the `BoardController` uses `cardsSwapped` to build a `ParallelAnimation` and skips the individual `cardMoved` events for swapped cards.

## What to Implement

### File: `front/src/babylon-editor/src/scripts/BoardController.ts`

```typescript
import type { Scene } from "@babylonjs/core/scene";
import type { IScript } from "babylonjs-editor-tools";

class BoardController implements IScript {
  // Dependencies (initialized in onStart)
  private _stateStore!: GameStateStore;
  private _cardManager!: CardEntityManager;
  private _animationPipeline!: AnimationPipeline;

  // Zone renderers — keyed by "{my|opp}_{ZONE}"
  private _zones = new Map<string, ZoneRenderer>();

  // Tracks instanceIds involved in a swap so handleCardMoved skips them
  private _swapInProgress = new Set<string>();

  constructor(private _scene: Scene);

  public onStart(): void;
  public onUpdate(): void;
  public onStop(): void;
}
```

### Initialization (`onStart`)

1. **Get dependencies** (with null guard):
   ```typescript
   const networkManager = GameNetworkManagerComponent.instance;
   if (!networkManager) throw new Error("GameNetworkManagerComponent not initialized");

   const store = networkManager.getStateStore();
   if (!store) throw new Error("GameStateStore not initialized");
   this._stateStore = store;

   this._cardManager = CardEntityManager.getOrCreate(this._scene);
   this._animationPipeline = new AnimationPipeline(this._scene);
   ```

2. **Initialize blueprints:**
   ```typescript
   this._cardManager.initBlueprints("UpsideUpCard_BP", "UpsideDownCard_BP");
   ```

3. **Create zone renderers** using scene anchor nodes. Each zone type has a different constructor signature, so creation is explicit per zone:
   ```typescript
   const myId = this._stateStore.myPlayerId;
   const oppId = this._stateStore.getOpponentId();

   const anchor = (name: string): TransformNode => {
     const node = this._scene.getTransformNodeByName(name);
     if (!node) console.warn(`Anchor node "${name}" not found in scene`);
     return node!;
   };

   // Local player
   this._zones.set(this.zoneKey("my", "DECK"),
     new DeckZoneRenderer("DECK", myId, anchor("My_Deck_Anchor")));
   this._zones.set(this.zoneKey("my", "HAND"),
     new HandZoneRenderer(myId, anchor("My_Hand_Anchor"), true));
   this._zones.set(this.zoneKey("my", "SUPPORTING"),
     new FieldZoneRenderer("SUPPORTING", myId, anchor("My_Supporting_Anchor"), 3, true));
   this._zones.set(this.zoneKey("my", "ATTACKING"),
     new FieldZoneRenderer("ATTACKING", myId, anchor("My_Attacking_Anchor"), 2, true));
   this._zones.set(this.zoneKey("my", "GRAVEYARD"),
     new GraveyardZoneRenderer(myId, anchor("My_Graveyard_Anchor")));

   // Opponent
   this._zones.set(this.zoneKey("opp", "DECK"),
     new DeckZoneRenderer("DECK", oppId, anchor("Opp_Deck_Anchor")));
   this._zones.set(this.zoneKey("opp", "HAND"),
     new HandZoneRenderer(oppId, anchor("Opp_Hand_Anchor"), false));
   this._zones.set(this.zoneKey("opp", "SUPPORTING"),
     new FieldZoneRenderer("SUPPORTING", oppId, anchor("Opp_Supporting_Anchor"), 3, false));
   this._zones.set(this.zoneKey("opp", "ATTACKING"),
     new FieldZoneRenderer("ATTACKING", oppId, anchor("Opp_Attacking_Anchor"), 2, false));
   this._zones.set(this.zoneKey("opp", "GRAVEYARD"),
     new GraveyardZoneRenderer(oppId, anchor("Opp_Graveyard_Anchor")));
   ```

4. **Subscribe to state store events:**
   ```typescript
   this._stateStore.on("gameStarted", this.handleGameStarted);
   this._stateStore.on("stateReplaced", this.handleStateReplaced);
   this._stateStore.on("cardAdded", this.handleCardAdded);
   this._stateStore.on("cardMoved", this.handleCardMoved);
   this._stateStore.on("cardsSwapped", this.handleCardsSwapped);
   this._stateStore.on("attackDeclared", this.handleAttackDeclared);
   this._stateStore.on("cardHealthChanged", this.handleCardHealthChanged);
   this._stateStore.on("cardDestroyed", this.handleCardDestroyed);
   this._stateStore.on("phaseChanged", this.handlePhaseChanged);
   this._stateStore.on("turnChanged", this.handleTurnChanged);
   this._stateStore.on("gameOver", this.handleGameOver);
   ```

5. **Wire animation pipeline callbacks:**
   ```typescript
   this._animationPipeline.onQueueStarted = () => {
     // Disable interaction (InteractionManager will check this)
   };
   this._animationPipeline.onQueueDrained = () => {
     // Re-enable interaction
   };
   ```

### Event Handlers

#### `handleGameStarted(state: ClientGameState)`

Initial board setup — non-animated:

1. Create `CardEntity` for each card in `state.cards` (deck cards face-down, hand cards face-up for local player, all opponent cards face-down).
2. Add each entity to the appropriate zone renderer with `animate: false`.
3. This is the "instant setup" of the board after the `game_started` message.

#### `handleStateReplaced(state: ClientGameState)`

Full state sync — reconnection or authoritative correction:

1. Dispose all existing card entities via `CardEntityManager.dispose()`.
2. Clear all zone renderers (call `dispose()` on each, then recreate them).
3. Re-run the same logic as `handleGameStarted` to rebuild the board from scratch.

Extract the shared setup logic into a private `_buildBoard(state: ClientGameState)` method used by both handlers.

#### `handleCardAdded(card: ClientCard)`

A new card has appeared (e.g., drawn from deck). This fires **before** the corresponding `cardMoved` event in the same event batch.

1. Create a `CardEntity` via `CardEntityManager.createEntity()`.
2. The entity is **not** added to any zone renderer yet — `handleCardMoved` handles placement and animation.
3. The entity's mesh is left at its clone origin; `handleCardMoved` will determine the correct animation start position from `fromZone`.

> **Why not add to the source zone renderer?** State is already mutated — the card's `zone` field is the destination. Adding to the source renderer would be immediately undone by `handleCardMoved`. Keeping the entity unplaced avoids a wasted add/remove cycle.

#### `handleCardMoved(data: CardMovedData)`

A card moved between zones. Most common handler:

1. If `data.instanceId` is in `_swapInProgress`, **skip** — `handleCardsSwapped` manages swap animations.
2. Get the `CardEntity` by `instanceId`.
3. Determine source and dest zone renderer keys (e.g., `"my_DECK"` → `"my_HAND"`).
4. Remove entity from source zone renderer (no-op if entity wasn't in a renderer, i.e., freshly created by `handleCardAdded`).
5. Determine animation origin: if the entity was in a renderer, use its current mesh position. Otherwise (freshly added), use the source zone renderer's `getExitPosition()`.
6. Enqueue a `CardMoveAnimation` from origin to destination zone's `getEntryPosition()`.
7. If moving from DECK to HAND for the local player, also enqueue a `CardFlipAnimation(faceUp: true)` after the move.
8. After animation completes: add entity to destination zone renderer with `animate: false` (it's already in position).
9. Trigger source zone `repositionAll(animate: true)` to close gaps left by the removed card.

#### `handleCardsSwapped(data: CardsSwappedData)`

Two cards swap zones (SUPPORTING ↔ ATTACKING). Uses `ParallelAnimation` so both cards cross paths simultaneously:

1. Add both `data.supportingId` and `data.attackingId` to `_swapInProgress` (so `handleCardMoved` skips the individual events emitted before this one).
2. Get both `CardEntity` objects.
3. Remove each from its current zone renderer.
4. Build a `ParallelAnimation` containing two `CardMoveAnimation`s:
   - Former supporting card → attacking zone's `getEntryPosition()`
   - Former attacking card → supporting zone's `getEntryPosition()`
5. After animation completes: add each entity to its new zone renderer.
6. Clear both IDs from `_swapInProgress`.

#### `handleAttackDeclared(data: AttackDeclaredData)`

Enqueue an `AttackAnimation` — the attacker lunges toward the target:

1. Get attacker `CardEntity` by `data.attackerId`.
2. Get target `CardEntity` by `data.targetId` (may be `undefined` if attacking player directly — use a position vector fallback).
3. Enqueue `AttackAnimation(attacker, target)`.

#### `handleCardHealthChanged(data: CardHealthChangedData)`

Enqueue a `DamageAnimation` on the target card:

1. Get the `CardEntity` by `data.instanceId`.
2. Compute `damage = data.oldHealth - data.newHealth`.
3. Enqueue `DamageAnimation(entity, damage, data.newHealth)`.

#### `handleCardDestroyed(data: CardDestroyedData)`

1. Get the entity by `data.instanceId`.
2. Remove from its current zone renderer.
3. Get the graveyard zone renderer for this card's owner.
4. Enqueue `DestroyAnimation` toward graveyard's `getEntryPosition()`.
5. After animation: add to graveyard zone renderer (or dispose the entity if graveyard is decorative-only).

#### `handlePhaseChanged(data: PhaseChangedData)`

Enqueue a `DelayAnimation(200)` for pacing. The HUD layer (Step 10) independently subscribes to the state store for its own UI transitions (phase banner, etc.).

#### `handleTurnChanged(data: TurnChangedData)`

Enqueue a `DelayAnimation(800)` for the turn transition. The HUD layer handles the "Your Turn" / "Opponent's Turn" banner independently.

#### `handleGameOver(data: GameOverData)`

Stop the animation pipeline (`skipAll()`), show end-game state.

### Events Not Handled by BoardController

These state store events are intentionally handled by other layers or deferred:

| Event | Handled By | Reason |
|---|---|---|
| `validActionsChanged` | ActionBuilder (Step 8) | Drives interaction affordances, not 3D visuals |
| `elementsConsumed` / `elementsRestored` | HUD (Step 10) | Element pool is a UI display concern |
| `turnEnded` | HUD (Step 10) | End-of-turn bookkeeping, no 3D visual needed |
| `cardAssociated` | Future step | Association visuals TBD (attach VFX) |
| `cardEvolved` | Future step | Evolution visuals TBD (transform VFX) |
| `effectTriggered` / `effectApplied` | Future step | Effect VFX TBD |
| `noDefender` | Future step | No-defender visual cue TBD |

### Helper: Zone Renderer Key

```typescript
private zoneKey(perspective: "my" | "opp", zone: Zone): string {
  return `${perspective}_${zone}`;
}

private getZoneRendererForCard(ownerId: string, zone: Zone): ZoneRenderer | undefined {
  const perspective = ownerId === this._stateStore.myPlayerId ? "my" : "opp";
  return this._zones.get(this.zoneKey(perspective, zone));
}
```

### Cleanup (`onStop`)

1. Unsubscribe from all state store events.
2. Dispose animation pipeline.
3. Dispose all zone renderers.
4. Dispose card entity manager.

## Scene Script Registration

After creating this file, it must be registered in `scripts.ts`:

```typescript
"scripts/BoardController.ts": scripts_BoardController,
```

And attached to a node in the `Battle.scene` (e.g., the root node or a dedicated "GameManager" empty node).

## Constraints

- This is the ONLY component that subscribes to `GameStateStore` change events for **3D board** updates. The HUD layer (Step 10) independently subscribes for its own UI overlay updates — that separation is intentional.
- Zone renderers are created and owned by this controller — they don't exist independently.
- The animation pipeline is created and owned by this controller.
- The controller does NOT know about player input — that's the `InteractionManager` (Step 9).
- Must be a BabylonJS Editor `IScript` so it can be attached to a scene node.

## Agent Prompt

```
Create `front/src/babylon-editor/src/scripts/BoardController.ts` — the main game orchestrator
scene script.

Read these files for context:
- front/architecture/step_07.md (this step's spec)
- front/architecture/overview.md (full architecture)
- front/src/babylon-editor/src/scripts/state/GameStateStore.ts (state store from Step 2)
- front/src/babylon-editor/src/scripts/entities/CardEntityManager.ts (entity manager from Step 4)
- front/src/babylon-editor/src/scripts/zones/ZoneRenderer.ts (zone interface from Step 5)
- front/src/babylon-editor/src/scripts/zones/DeckZoneRenderer.ts
- front/src/babylon-editor/src/scripts/zones/HandZoneRenderer.ts
- front/src/babylon-editor/src/scripts/zones/FieldZoneRenderer.ts
- front/src/babylon-editor/src/scripts/zones/GraveyardZoneRenderer.ts
- front/src/babylon-editor/src/scripts/animation/AnimationPipeline.ts (from Step 6)
- front/src/babylon-editor/src/scripts/animation/ (all animation classes from Step 6)
- front/src/babylon-editor/src/scripts/GameNetworkManagerComponent.ts (to get dependencies)

Prerequisite — before implementing BoardController, add the `cardsSwapped` event to
GameStateStore (see step_07.md "Prerequisite" section). Add CardsSwappedData interface
and add it to StateChangeEvents. Emit from _handleCardSwapped() after the existing
two cardMoved emissions.

Then implement the BoardController as specified. Key rules:
1. Implements IScript (constructor takes Scene, has onStart/onStop/onUpdate).
2. onStart: guard against null networkManager/stateStore with thrown errors.
   Get dependencies, create AnimationPipeline, create all ZoneRenderers (10 total:
   5 zones × 2 players) with correct constructor signatures per zone type:
   - DeckZoneRenderer(zone, ownerId, anchorNode)
   - HandZoneRenderer(ownerId, anchorNode, isLocalPlayer)
   - FieldZoneRenderer(zone, ownerId, anchorNode, maxSlots, isLocalPlayer) — 3 for SUPPORTING, 2 for ATTACKING
   - GraveyardZoneRenderer(ownerId, anchorNode)
3. Subscribe to: gameStarted, stateReplaced, cardAdded, cardMoved, cardsSwapped,
   attackDeclared, cardHealthChanged, cardDestroyed, phaseChanged, turnChanged, gameOver.
4. handleCardAdded: create entity but do NOT add to a zone renderer — handleCardMoved
   handles placement and animation.
5. handleCardMoved: skip if instanceId is in _swapInProgress set. Otherwise: remove from
   source renderer (no-op if not present), determine animation origin (current mesh position
   if was in a renderer, else source zone's getExitPosition()), enqueue CardMoveAnimation,
   add to dest renderer after animation. For DECK→HAND on local player, also enqueue
   CardFlipAnimation.
6. handleCardsSwapped: add both IDs to _swapInProgress, build ParallelAnimation with two
   CardMoveAnimations, clear _swapInProgress after animation completes.
7. handleAttackDeclared: enqueue AttackAnimation(attacker, target).
8. handleStateReplaced: dispose all entities/renderers, rebuild board from scratch.
   Extract shared setup into _buildBoard() used by both gameStarted and stateReplaced.
9. handleGameStarted: instant (non-animated) setup of the full board.
10. This is the ONLY component subscribing to GameStateStore for 3D board updates.
    HUD (Step 10) subscribes independently for UI overlay updates.
11. Register in scripts.ts after creation.
```
