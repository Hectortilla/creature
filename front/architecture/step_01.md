# Step 1: Game Models & Types

> **Depends on:** Nothing (first step)  
> **Produces:** `scripts/game/models.ts`  
> **See also:** [Architecture Overview](./overview.md) — "Layer Descriptions → 1. Game Models"

## Goal

Create strongly-typed TypeScript interfaces and enums that mirror the backend domain model. This replaces all `Record<string, unknown>` usage with concrete types and becomes the shared vocabulary for every other layer in the architecture.

## What to Implement

### File: `front/src/babylon-editor/src/scripts/game/models.ts`

Define the following types, matching the backend's Python enums and Pydantic models:

### Enums

```typescript
enum Zone {
  DECK = "DECK",
  HAND = "HAND",
  SUPPORTING = "SUPPORTING",
  ATTACKING = "ATTACKING",
  GRAVEYARD = "GRAVEYARD",
}

enum TurnPhase {
  DRAW = "DRAW",
  PLACEMENT = "PLACEMENT",
  PROMOTION = "PROMOTION",
  SWAP = "SWAP",
  ASSOCIATION = "ASSOCIATION",
  EVOLUTION = "EVOLUTION",
  ATTACK = "ATTACK",
}

enum GameStatus {
  WAITING = "WAITING",
  STARTING = "STARTING",
  IN_PROGRESS = "IN_PROGRESS",
  PAUSED = "PAUSED",
  FINISHED = "FINISHED",
}

enum CardStatus {
  READY = "READY",
  SWAPPED = "SWAPPED",
  EXHAUSTED = "EXHAUSTED",
  ASSOCIATED = "ASSOCIATED",
}

enum DamageType {
  PHYSICAL = "PHYSICAL",
  MAGICAL = "MAGICAL",
}
```

Use string enums (not numeric) because the backend serializes enums as their `.name` string.

### Card-related interfaces

```typescript
interface ElementContribution {
  element_id: number;
  amount: number;
}

interface ElementPool {
  elements: Record<number, number>;      // element_id → available amount
  max_elements: Record<number, number>;  // element_id → max amount
}

interface AttackCost {
  element_id: number;
  amount: number;
}

interface AttackDefinition {
  attack_id: number;
  name: string;
  damage: number;
  type: DamageType;
  element_id: number;
  necessary_force: AttackCost[];
  effect: string | null;
  dice_rolls: number | null;
}

interface ClientCard {
  instanceId: string;
  cardId: number;
  ownerId: string;
  name: string;
  health: number;           // max health
  currentHealth: number;
  physicalDefence: number;
  magicDefence: number;
  elementIds: number[];
  elementContribution: ElementContribution[];
  attacks: AttackDefinition[];
  skillIds: number[];
  associationIds: number[];
  zone: Zone;
  status: CardStatus;
  turnsInZone: number;
  associations: string[];   // instance IDs of associated cards
  isEvolution: boolean;
  evolvesFromId: number | null;
  hasAttackedThisTurn: boolean;
  swappedThisTurn: boolean;

  // Computed (derive on client from the above)
  isAlive: boolean;
  canAttack: boolean;
  canPromote: boolean;
  canEvolve: boolean;
}
```

### Player & Game State interfaces

```typescript
interface ZoneState {
  zone: Zone;
  ownerId: string;
  cardIds: string[];        // instance IDs, ordered
  maxCapacity: number | null;
}

interface ClientPlayerState {
  playerId: string;
  name: string;
  turnCount: number;
  elementPool: ElementPool;
  zones: Record<Zone, ZoneState>;
}

interface GameConfig {
  deckSize: number;
  initialDraw: number;
  normalDraw: number;
  supportingZoneSize: number;
  attackingZoneSize: number;
}

interface ClientGameState {
  gameId: string;
  status: GameStatus;
  activePlayerId: string | null;
  currentPhase: TurnPhase;
  turnNumber: number;
  pendingAction: string | null;
  winnerId: string | null;
  config: GameConfig;
  myPlayer: ClientPlayerState;
  opponent: ClientPlayerState;
  cards: Map<string, ClientCard>;
}
```

### Event type discriminators

```typescript
// All possible backend event type strings
type GameEventType =
  | "CardDrawnEvent"
  | "CardMovedEvent"
  | "CardPlayedEvent"
  | "CardPromotedEvent"
  | "CardSwappedEvent"
  | "CardAssociatedEvent"
  | "CardEvolvedEvent"
  | "AttackDeclaredEvent"
  | "DamageDealtEvent"
  | "CardDestroyedEvent"
  | "ElementsConsumedEvent"
  | "ElementsRestoredEvent"
  | "TurnStartedEvent"
  | "TurnEndedEvent"
  | "PhaseChangedEvent"
  | "GameStartedEvent"
  | "GameEndedEvent"
  | "NoDefenderEvent"
  | "EffectTriggeredEvent"
  | "EffectAppliedEvent";

// Typed event payloads for the most critical events
interface CardDrawnEventData {
  event_type: "CardDrawnEvent";
  player_id: string;
  card_id: string;
  cards_remaining: number;
}

interface CardPlayedEventData {
  event_type: "CardPlayedEvent";
  player_id: string;
  card_id: string;
  card_name: string;
}

interface CardPromotedEventData {
  event_type: "CardPromotedEvent";
  player_id: string;
  card_id: string;
  card_name: string;
}

interface CardSwappedEventData {
  event_type: "CardSwappedEvent";
  player_id: string;
  supporting_card_id: string;
  attacking_card_id: string;
}

interface AttackDeclaredEventData {
  event_type: "AttackDeclaredEvent";
  attacker_owner_id: string;
  attacker_id: string;
  target_id: string;
  attack_id: number;
  attack_name: string;
}

interface DamageDealtEventData {
  event_type: "DamageDealtEvent";
  source_id: string;
  target_id: string;
  damage_type: string;
  base_damage: number;
  element_bonus: number;
  defense_reduction: number;
  final_damage: number;
  remaining_health: number;
}

interface CardDestroyedEventData {
  event_type: "CardDestroyedEvent";
  card_id: string;
  owner_id: string;
  card_name: string;
  destroyed_by: string;
}

interface PhaseChangedEventData {
  event_type: "PhaseChangedEvent";
  player_id: string;
  from_phase: string;
  to_phase: string;
}

interface TurnStartedEventData {
  event_type: "TurnStartedEvent";
  player_id: string;
  turn_number: number;
  is_first_turn: boolean;
}

interface GameEndedEventData {
  event_type: "GameEndedEvent";
  winner_id: string;
  loser_id: string;
  reason: string;
}

// Union of all typed event payloads
type GameEventData =
  | CardDrawnEventData
  | CardPlayedEventData
  | CardPromotedEventData
  | CardSwappedEventData
  | AttackDeclaredEventData
  | DamageDealtEventData
  | CardDestroyedEventData
  | PhaseChangedEventData
  | TurnStartedEventData
  | GameEndedEventData;
```

### Visual state enum (for the entity system later)

```typescript
enum CardVisualState {
  IDLE = "IDLE",
  HOVERED = "HOVERED",
  SELECTED = "SELECTED",
  DRAGGING = "DRAGGING",
  ANIMATING = "ANIMATING",
  DISABLED = "DISABLED",
}
```

### Utility: parse backend snake_case to camelCase

Add a helper function `parseCardFromServer(raw: Record<string, unknown>): ClientCard` that maps the backend's snake_case field names to the camelCase TypeScript interfaces. This will be used by `GameStateStore` when processing events that include card data.

## Constraints

- Use string enums (not numeric `auto()`) so they match the backend's serialized `.name` values.
- All interfaces should be exported.
- Re-export everything from `scripts/game/index.ts`.
- Do NOT modify existing files in this step, only add `models.ts` and update `index.ts` exports.

## Backend Reference

The source-of-truth definitions live in:
- `back/app/models/game/enums.py` — all enums
- `back/app/models/game/card.py` — `GameCard` model
- `back/app/models/game/state.py` — `GameState`, `GameConfiguration`
- `back/app/models/game/player.py` — `PlayerState`
- `back/app/models/game/zone.py` — `ZoneState`
- `back/app/models/game/events.py` — all event classes
- `back/app/models/game/element.py` — `ElementContribution`, `ElementPool`
- `back/app/models/game/attack.py` — `AttackDefinition`

## Agent Prompt

```
Create the file `front/src/babylon-editor/src/scripts/game/models.ts` with strongly-typed TypeScript
enums and interfaces that mirror the backend game domain model.

Read the following backend files to understand the exact field names, types, and serialization:
- back/app/models/game/enums.py
- back/app/models/game/card.py
- back/app/models/game/state.py
- back/app/models/game/player.py
- back/app/models/game/zone.py
- back/app/models/game/events.py
- back/app/models/game/element.py
- back/app/models/game/attack.py

Implement the types described in front/architecture/step_01.md. Key rules:
1. Use string enums (e.g., DECK = "DECK") because the backend serializes enum values as their .name string.
2. Use camelCase for TS interface fields but keep backend field names in event data interfaces (since those arrive as JSON from the server).
3. Add a parseCardFromServer(raw) utility that converts snake_case server card data to the camelCase ClientCard interface.
4. Export everything. Update front/src/babylon-editor/src/scripts/game/index.ts to re-export from models.ts.
5. Do NOT modify any other existing files.
```
