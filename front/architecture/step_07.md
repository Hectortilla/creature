# Step 7: Board Controller

> **Depends on:** Step 2 (GameStateStore), Step 4 (CardEntityManager), Step 5 (Zone Renderers), Step 6 (AnimationPipeline)  
> **Produces:** `scripts/BoardController.ts`  
> **See also:** [Architecture Overview](./overview.md) — "Layer Descriptions → 6. Board Controller"

## Goal

Create the **single orchestrator** scene script that bridges the game state to the 3D world. The `BoardController` is the only component that subscribes to `GameStateStore` change events and translates them into entity creation/destruction, zone renderer updates, and animation pipeline commands.

This is the central nervous system of the visual game — no other script should listen to state changes or manage card visuals directly.

## What to Implement

### File: `front/src/babylon-editor/src/scripts/BoardController.ts`

```typescript
import type { Scene } from "@babylonjs/core/scene";
import type { IScript } from "babylonjs-editor-tools";

class BoardController implements IScript {
  // Dependencies (initialized in onStart)
  private _stateStore: GameStateStore;
  private _cardManager: CardEntityManager;
  private _animationPipeline: AnimationPipeline;

  // Zone renderers — keyed by "{my|opp}_{ZONE}"
  private _zones = new Map<string, ZoneRenderer>();

  constructor(private _scene: Scene);

  public onStart(): void;
  public onUpdate(): void;  // may be needed for per-frame updates
  public onStop(): void;
}
```

### Initialization (`onStart`)

1. **Get dependencies:**
   ```typescript
   const networkManager = GameNetworkManagerComponent.instance;
   this._stateStore = networkManager.getStateStore();
   this._cardManager = CardEntityManager.getOrCreate(this._scene);
   this._animationPipeline = new AnimationPipeline(this._scene);
   ```

2. **Initialize blueprints:**
   ```typescript
   this._cardManager.initBlueprints("UpsideUpCard_BP", "UpsideDownCard_BP");
   ```

3. **Create zone renderers** using scene anchor nodes:
   ```typescript
   // For each zone × each player, create a renderer
   // Local player
   this.createZoneRenderer("my", Zone.DECK, "My_Deck_Anchor", true);
   this.createZoneRenderer("my", Zone.HAND, "My_Hand_Anchor", true);
   this.createZoneRenderer("my", Zone.SUPPORTING, "My_Supporting_Anchor", true);
   this.createZoneRenderer("my", Zone.ATTACKING, "My_Attacking_Anchor", true);
   this.createZoneRenderer("my", Zone.GRAVEYARD, "My_Graveyard_Anchor", true);

   // Opponent
   this.createZoneRenderer("opp", Zone.DECK, "Opp_Deck_Anchor", false);
   this.createZoneRenderer("opp", Zone.HAND, "Opp_Hand_Anchor", false);
   this.createZoneRenderer("opp", Zone.SUPPORTING, "Opp_Supporting_Anchor", false);
   this.createZoneRenderer("opp", Zone.ATTACKING, "Opp_Attacking_Anchor", false);
   this.createZoneRenderer("opp", Zone.GRAVEYARD, "Opp_Graveyard_Anchor", false);
   ```

4. **Subscribe to state store events:**
   ```typescript
   this._stateStore.on("gameStarted", this.handleGameStarted);
   this._stateStore.on("cardAdded", this.handleCardAdded);
   this._stateStore.on("cardMoved", this.handleCardMoved);
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

1. Create `CardEntity` for each card in each zone (deck cards face-down, hand cards face-up for local player).
2. Add each entity to the appropriate zone renderer with `animate: false`.
3. This is the "instant setup" of the board after the game_started message.

#### `handleCardAdded(card: ClientCard)`

A new card has appeared (e.g., drawn from deck):

1. Create a `CardEntity` via `CardEntityManager.createEntity()`.
2. The entity's initial position should be at the source zone's location.
3. (The subsequent `cardMoved` event handles the animation to the destination.)

#### `handleCardMoved(data: CardMovedData)`

A card moved between zones. This is the most common handler:

1. Get the `CardEntity` by `instanceId`.
2. Determine source zone renderer key (e.g., `"my_DECK"`) and dest zone renderer key (e.g., `"my_HAND"`).
3. Remove entity from source zone renderer.
4. Enqueue a `CardMoveAnimation` from source position to destination entry position.
5. After animation: add entity to destination zone renderer.
6. Trigger source zone `repositionAll(animate: true)`.

#### `handleCardHealthChanged(data: CardHealthChangedData)`

Enqueue a `DamageAnimation` on the target card.

#### `handleCardDestroyed(data: CardDestroyedData)`

1. Get the entity.
2. Remove from its current zone renderer.
3. Enqueue `DestroyAnimation` toward graveyard position.
4. After animation: add to graveyard zone renderer (or destroy the entity if graveyard is decorative-only).

#### `handlePhaseChanged(data: PhaseChangedData)`

Enqueue a `DelayAnimation` for pacing. The HUD (Step 10) handles the visual phase transition independently by also subscribing to the state store.

#### `handleTurnChanged(data: TurnChangedData)`

Enqueue a `DelayAnimation(800)` for the turn transition. HUD handles "Your Turn" banner.

#### `handleGameOver(data: GameOverData)`

Stop the animation pipeline, show end-game state.

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

- This is the ONLY component that subscribes to `GameStateStore` change events for visual updates.
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

Implement the BoardController as specified. Key rules:
1. Implements IScript (constructor takes Scene, has onStart/onStop/onUpdate).
2. onStart: get GameStateStore and CardEntityManager singletons, create AnimationPipeline,
   create all ZoneRenderers (10 total: 5 zones × 2 players), subscribe to state store events.
3. Event handlers create/move/destroy CardEntities and enqueue animations.
4. handleCardMoved: remove from source zone renderer, enqueue CardMoveAnimation, add to dest zone renderer.
5. handleGameStarted: instant (non-animated) setup of the full board.
6. Zone renderers are looked up from scene anchor TransformNodes by name.
7. This is the ONLY component subscribing to GameStateStore for visual updates.
8. Register in scripts.ts after creation.
```
