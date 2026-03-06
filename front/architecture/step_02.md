# Step 2: Game State Store

> **Depends on:** Step 1 (Game Models)  
> **Produces:** `scripts/state/GameStateStore.ts`  
> **See also:** [Architecture Overview](./overview.md) — "Layer Descriptions → 2. Game State Store"

## Goal

Create the central client-side game state singleton. This is the **single source of truth** for all game data. Every other system (zones, animations, interaction, HUD) reads from it. It processes raw backend events to build and maintain a `ClientGameState`.

## What to Implement

### File: `front/src/babylon-editor/src/scripts/state/GameStateStore.ts`

### Core Design

```typescript
type StateChangeCallback<T> = (data: T) => void;

interface CardMovedData {
  instanceId: string;
  ownerId: string;
  fromZone: Zone;
  toZone: Zone;
}

interface CardHealthChangedData {
  instanceId: string;
  oldHealth: number;
  newHealth: number;
  maxHealth: number;
}

interface PhaseChangedData {
  fromPhase: TurnPhase;
  toPhase: TurnPhase;
  playerId: string;
}

interface TurnChangedData {
  playerId: string;
  turnNumber: number;
  isFirstTurn: boolean;
}

interface CardDestroyedData {
  instanceId: string;
  ownerId: string;
  cardName: string;
}

interface GameOverData {
  winnerId: string;
  loserId: string;
  reason: string;
}

// Typed change event map
interface StateChangeEvents {
  cardAdded: ClientCard;
  cardMoved: CardMovedData;
  cardHealthChanged: CardHealthChangedData;
  cardDestroyed: CardDestroyedData;
  phaseChanged: PhaseChangedData;
  turnChanged: TurnChangedData;
  gameStarted: ClientGameState;
  gameOver: GameOverData;
  validActionsChanged: ValidAction[];
  stateReplaced: ClientGameState;  // full state sync
}
```

### Singleton class

```typescript
class GameStateStore {
  static instance: GameStateStore | null = null;

  private _state: ClientGameState | null = null;
  private _myPlayerId: string = "";
  private _validActions: ValidAction[] = [];
  private _listeners = new Map<keyof StateChangeEvents, Set<StateChangeCallback<any>>>();

  static getOrCreate(myPlayerId: string): GameStateStore;

  // --- Queries ---
  get state(): ClientGameState | null;
  get myPlayerId(): string;
  get validActions(): ValidAction[];
  get isMyTurn(): boolean;
  get currentPhase(): TurnPhase | null;
  getCard(instanceId: string): ClientCard | undefined;
  getCardsInZone(playerId: string, zone: Zone): ClientCard[];
  getMyCardsInZone(zone: Zone): ClientCard[];
  getOpponentCardsInZone(zone: Zone): ClientCard[];

  // --- Event Processing ---
  // Called by GameNetworkManagerComponent when backend events arrive
  processGameStarted(data: Record<string, unknown>): void;
  processGameEvents(events: Record<string, unknown>[]): void;
  processGameState(rawState: Record<string, unknown>): void;
  updateValidActions(actions: ValidAction[]): void;

  // --- Change Subscriptions ---
  on<K extends keyof StateChangeEvents>(event: K, cb: StateChangeCallback<StateChangeEvents[K]>): void;
  off<K extends keyof StateChangeEvents>(event: K, cb: StateChangeCallback<StateChangeEvents[K]>): void;

  // --- Cleanup ---
  dispose(): void;
}
```

### Event Processing Logic

Each backend event type modifies state and emits the corresponding typed change event:

| Backend Event | State Mutation | Change Event Emitted |
|---|---|---|
| `GameStartedEvent` | Initialize full `ClientGameState` from `game_state` payload | `gameStarted` |
| `CardDrawnEvent` | Move card_id from DECK → HAND in player's zones, add card data to `cards` map | `cardAdded` + `cardMoved` |
| `CardPlayedEvent` | Move card_id from HAND → SUPPORTING | `cardMoved` |
| `CardPromotedEvent` | Move card_id from SUPPORTING → ATTACKING | `cardMoved` |
| `CardSwappedEvent` | Swap positions of supporting_card_id and attacking_card_id | `cardMoved` (×2) |
| `DamageDealtEvent` | Update target card's `currentHealth` | `cardHealthChanged` |
| `CardDestroyedEvent` | Move card to GRAVEYARD, mark not alive | `cardDestroyed` + `cardMoved` |
| `PhaseChangedEvent` | Update `currentPhase` | `phaseChanged` |
| `TurnStartedEvent` | Update `activePlayerId`, `turnNumber` | `turnChanged` |
| `GameEndedEvent` | Set `status = FINISHED`, `winnerId` | `gameOver` |

### Key Principles

1. **State updates are synchronous and immediate.** No async, no waiting for animations.
2. **The store does NOT know about meshes, animations, or BabylonJS.** Pure data only.
3. **The store emits events AFTER mutating state**, so listeners always see the new state.
4. **Card data population:** When `CardDrawnEvent` arrives and the event includes card data, the store adds it to `state.cards`. If no card data is in the event, the store creates a minimal entry with just the `instanceId` and marks it as needing data.

### Important: Handling Opponent vs Self

The store must distinguish between "my" events and opponent events. The `myPlayerId` field determines perspective:
- `myPlayer` = the player matching `myPlayerId`
- `opponent` = the other player

When processing a `CardDrawnEvent` for the opponent, the card is added face-down (no card details revealed).

## Constraints

- Pure TypeScript singleton — no BabylonJS imports, no scene dependencies.
- Import types only from `game/models.ts` and `game/types.ts`.
- Must be usable from both scene scripts and plain TS classes.

## Agent Prompt

```
Create the file `front/src/babylon-editor/src/scripts/state/GameStateStore.ts`.

This is the central game state singleton described in front/architecture/step_02.md.

Read these files for context:
- front/architecture/overview.md (full architecture)
- front/architecture/step_02.md (this step's spec)
- front/src/babylon-editor/src/scripts/game/models.ts (types from Step 1)
- front/src/babylon-editor/src/scripts/game/types.ts (ValidAction, GameMessage types)
- back/app/models/game/events.py (backend event definitions)

Implement the GameStateStore class as specified. Key rules:
1. Pure TypeScript singleton, no BabylonJS imports.
2. Processes raw backend event objects (Record<string, unknown>) and updates typed ClientGameState.
3. Emits typed change events (cardMoved, phaseChanged, etc.) after each state mutation.
4. Uses parseCardFromServer from models.ts for card data deserialization.
5. Provides query methods (getCard, getCardsInZone, isMyTurn, etc.).
6. Handles both "my" events and opponent events using the myPlayerId field.
7. State updates are synchronous — no async, no animation awareness.
```
