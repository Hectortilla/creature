# Creature Card Game — BabylonJS Client Architecture

## Context

This document describes the frontend architecture for the **Creature** card game built with BabylonJS Editor scripts. The backend uses an event-driven, stateless game engine with a unidirectional pipeline:

```
Action → Validator → EventGenerator → EventLoop → Reducer → New State
```

The frontend communicates via WebSocket. The server sends batches of typed game events (`CardDrawnEvent`, `CardPlayedEvent`, `PhaseChangedEvent`, etc.) and the client must render them as an interactive 3D card game.

---

## Problem Statement

The initial approach divided work into per-zone "position managers" (`HandCardsPosManager`, `DeckCardsPosManager`). While dividing by zone is the right instinct — each zone has distinct layout, interaction, and visual rules — the current scripts are too narrow: they are purely visual spawners with no shared infrastructure. Specifically:

1. **No client-side game state** — each manager works in isolation, listening directly to raw events with no shared source of truth.
2. **No card entity binding** — cards are just `Mesh[]` arrays with no game data attached; impossible to answer "which game card is this mesh?"
3. **No animation sequencing** — events arrive in batches but must animate sequentially.
4. **No interaction system** — no way to select, highlight, or drag cards.
5. **No opponent representation** — only the local player's zones are rendered.
6. **No phase/turn awareness** — nothing ties `valid_actions` to interactive affordances on the 3D board.

---

## Layer Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    HUD / UI Layer                        │  Phase indicator, action buttons,
│                  (BabylonJS GUI / HTML)                   │  health bars, element pool display
├──────────────────────────────────────────────────────────┤
│                 Interaction Manager                       │  Ray picking, card selection,
│                  (Scene Script)                           │  valid-target highlighting
├──────────────────────────────────────────────────────────┤
│                Animation Pipeline                        │  Sequential event→animation queue,
│                 (Plain TS class)                          │  tween engine adapter
├──────────────────────────────────────────────────────────┤
│               Board Controller                           │  Owns all ZoneRenderers,
│                (Scene Script)                             │  routes state changes to zones
├──────────────┬──────────┬──────────┬─────────────────────┤
│  DeckZone    │ HandZone │FieldZone │ GraveyardZone       │  Zone-specific layout +
│  Renderer    │ Renderer │ Renderer │ Renderer            │  spawn/remove/reposition
├──────────────┴──────────┴──────────┴─────────────────────┤
│              Card Entity Manager                         │  CardEntity = Mesh + GameCardData,
│                (Plain TS class)                           │  factory, registry, lifecycle
├──────────────────────────────────────────────────────────┤
│              Game State Store                            │  Single source of truth,
│               (Plain TS class)                           │  mirrors backend state, typed events
├──────────────────────────────────────────────────────────┤
│        GameNetworkManager → GameConnection               │  WebSocket transport
│               (Scene Script)                             │  (keep as-is, mostly)
└──────────────────────────────────────────────────────────┘
```

---

## Layer Descriptions

### 1. Game Models (`scripts/game/models.ts`)

Strongly-typed TypeScript interfaces mirroring the backend domain model. Replaces all `Record<string, unknown>` with concrete types.

**Key types:** `Zone`, `TurnPhase`, `GameStatus`, `CardStatus`, `DamageType`, `ClientCard`, `ClientPlayerState`, `ClientGameState`, `AttackDefinition`, `ElementContribution`, `ElementPool`, `GameConfig`.

### 2. Game State Store (`scripts/state/GameStateStore.ts`)

Singleton plain-TS class. The single authoritative client-side model. All other systems read from it. Card definition lookups are handled by `CardDefinitionCache`, which fetches definitions by database ID.

**Responsibilities:**
- Processes backend events immediately to update state (before any animation).
- Emits typed change events: `onCardMoved(instanceId, fromZone, toZone)`, `onPhaseChanged(from, to)`, `onCardHealthChanged(instanceId, old, new)`, etc.
- Provides query methods: `getCardsInZone(playerId, zone)`, `getCard(instanceId)`, `isMyTurn()`.
- Stores current `validActions` list from the backend.

### 3. Card Entity System (`scripts/entities/`)

Binds game data to 3D meshes. Every card in the game is a `CardEntity`.

- **`CardEntity`** — holds `instanceId`, `mesh: Mesh`, `cardData: ClientCard`, `visualState: CardVisualState`.
- **`CardEntityManager`** — singleton factory + registry. Creates entities from blueprints, provides bidirectional lookup (instanceId ↔ mesh).

### 4. Zone Renderers (`scripts/zones/`)

One renderer per zone type. Plain TS classes (not scene scripts) owned by the `BoardController`. Each handles layout for one zone type for one player.

| Zone | Renderer | Layout |
|------|----------|--------|
| DECK | `DeckZoneRenderer` | Stacked pile, face-down, Y-offset per card, count overlay |
| HAND | `HandZoneRenderer` | Fan arc layout (extracted from current `HandCardsPosManager`) |
| SUPPORTING | `FieldZoneRenderer` | Row of up to 3 slots, face-up flat on table |
| ATTACKING | `FieldZoneRenderer` | Row of up to 2 slots, face-up, slightly forward |
| GRAVEYARD | `GraveyardZoneRenderer` | Offset pile, decorative |

**Interface:**
```typescript
interface ZoneRenderer {
  readonly zone: Zone;
  readonly ownerId: string;
  addCard(entity: CardEntity, animate: boolean): Promise<void>;
  removeCard(instanceId: string): void;
  repositionAll(animate: boolean): Promise<void>;
  getEntryPosition(index?: number): Vector3;
  getExitPosition(index?: number): Vector3;
  getEntities(): CardEntity[];
  get count(): number;
  dispose(): void;
}
```

The scene contains **empty marker nodes** (e.g., `My_Hand_Anchor`, `Opp_Attacking_Anchor`) that zone renderers use for world-space positioning.

### 5. Animation Pipeline (`scripts/animation/`)

Events arrive in batches from `action_result`. They must animate sequentially with proper timing.

- **`AnimationPipeline`** — sequential queue. Disables interaction while playing, re-enables on drain.
- **`GameAnimation`** interface — `duration` + `execute(scene): Promise<void>`.
- **Concrete animations:** `CardMoveAnimation`, `CardFlipAnimation`, `AttackAnimation`, `DamageAnimation`, `DestroyAnimation`.

| Event | Animation |
|-------|-----------|
| `CardDrawnEvent` | Card flies from deck → hand, flips face-up |
| `CardPlayedEvent` | Card slides from hand → supporting slot |
| `CardPromotedEvent` | Card slides forward from supporting → attacking |
| `CardSwappedEvent` | Two cards cross paths |
| `AttackDeclaredEvent` | Attacker lunges toward target |
| `DamageDealtEvent` | Impact VFX, health number change |
| `CardDestroyedEvent` | Death animation, card to graveyard |
| `PhaseChangedEvent` | Phase banner transition |
| `TurnStartedEvent` | Camera shift, "Your Turn" / "Opponent's Turn" |

### 6. Board Controller (`scripts/BoardController.ts`)

Single orchestrator scene script. Bridges game state to the 3D world.

**Responsibilities:**
- Initializes all zone renderers using scene anchor nodes.
- Subscribes to `GameStateStore` change events.
- Routes card movements to the correct zone renderers.
- Feeds events into the `AnimationPipeline`.
- Manages the two-player perspective (my board vs opponent board).

### 7. Action Builder (`scripts/state/ActionBuilder.ts`)

Translates the backend's `valid_actions` list into card-level affordances.

- `getActionsForCard(instanceId)` — what can the player do with this card?
- `getInteractableCardIds()` — which cards should glow/highlight this phase?
- `execute(action)` — sends the action through `GameConnection`.

### 8. Interaction Manager (`scripts/interaction/InteractionManager.ts`)

Scene script handling all player input on the 3D board.

- Ray picking under pointer every frame.
- Hover highlighting (glow, outline).
- Click-to-select, click-to-target flow.
- Uses `ActionBuilder` to determine what's interactive.
- Disabled while `AnimationPipeline` is playing.

### 9. HUD Layer (`scripts/hud/`)

BabylonJS `AdvancedDynamicTexture` or HTML overlay for UI elements:

- Phase indicator (current phase, active during your turn).
- Pass / Concede buttons.
- Element pool display.
- Turn banner ("Your Turn" / "Opponent's Turn").
- Card detail panel (on hover/selection).
- Floating health bars above field cards.

---

## Data Flow Example

**Player plays a card from hand to supporting zone:**

```
1. InteractionManager: player clicks a glowing hand card
2. ActionBuilder: finds PlayCardAction in valid_actions for this card
3. GameConnection.sendAction({ action_type: "play_card", instance_id: "abc" })
4. Backend processes → returns action_result with events + new valid_actions
5. GameNetworkManager receives message, forwards to GameStateStore
6. GameStateStore: processes CardPlayedEvent
   → updates card.zone from HAND to SUPPORTING
   → updates myPlayer.zones.HAND (remove instance_id) and myPlayer.zones.SUPPORTING (add instance_id)
   → emits onCardMoved("abc", HAND, SUPPORTING)
7. BoardController: receives onCardMoved
   → tells HandZoneRenderer.removeCard("abc")
   → enqueues CardMoveAnimation into AnimationPipeline
   → after animation: FieldZoneRenderer.addCard(entity)
8. AnimationPipeline: plays slide animation from hand → supporting slot
9. HandZoneRenderer.repositionAll(animate=true) — remaining hand cards fan out
10. InteractionManager: re-reads valid_actions, updates highlights
```

---

## File Structure

```
scripts/
├── game/
│   ├── GameConnection.ts          # Keep as-is
│   ├── CardDefinitionCache.ts     # Fetches card definitions by database ID
│   ├── types.ts                   # Expand with typed game models
│   ├── index.ts                   # Re-exports
│   └── models.ts                  # NEW: ClientCard, ClientPlayerState, enums, etc.
│
├── state/
│   ├── GameStateStore.ts          # NEW: Central state + typed change events
│   └── ActionBuilder.ts           # NEW: valid_actions → card affordances
│
├── entities/
│   ├── CardEntity.ts              # NEW: Mesh + game data binding
│   └── CardEntityManager.ts       # NEW: Factory + registry
│
├── zones/
│   ├── ZoneRenderer.ts            # NEW: Interface
│   ├── DeckZoneRenderer.ts        # NEW (refactored from DeckCardsPosManager)
│   ├── HandZoneRenderer.ts        # NEW (refactored from HandCardsPosManager)
│   ├── FieldZoneRenderer.ts       # NEW: For SUPPORTING and ATTACKING
│   └── GraveyardZoneRenderer.ts   # NEW
│
├── animation/
│   ├── AnimationPipeline.ts       # NEW: Sequential queue
│   ├── GameAnimation.ts           # NEW: Interface
│   ├── CardMoveAnimation.ts       # NEW
│   ├── CardFlipAnimation.ts       # NEW
│   ├── AttackAnimation.ts         # NEW
│   ├── DamageAnimation.ts         # NEW
│   ├── DestroyAnimation.ts        # NEW
│   ├── DelayAnimation.ts          # NEW
│   └── ParallelAnimation.ts       # NEW: Runs multiple animations concurrently
│
├── interaction/
│   └── InteractionManager.ts      # NEW: Ray picking, selection, highlights
│
├── hud/
│   ├── HudController.ts           # NEW: Orchestrates HUD elements
│   ├── PhaseIndicator.ts          # NEW
│   ├── TurnBanner.ts              # NEW
│   ├── ElementPoolDisplay.ts      # NEW
│   ├── CardDetailPanel.ts         # NEW
│   └── HealthBar.ts               # NEW
│
├── BoardController.ts             # NEW: Main orchestrator scene script
├── GameNetworkManagerComponent.ts # MODIFY: Simplify, forward to GameStateStore
└── cloneWithScripts.ts            # Keep as-is
```

---

## Existing Code Disposition

| Current File | Action |
|---|---|
| `GameNetworkManagerComponent.ts` | **Modify** — keep as scene-script entry point for networking, auto-register instance→card mappings from incoming events, forward raw events to `GameStateStore`. |
| `GameConnection.ts` | **Keep as-is** — well designed, framework-agnostic. |
| `HandCardsPosManager.ts` | **Delete after refactoring** — extract fan-layout math into `HandZoneRenderer`. Remove event subscription and mesh tracking (now in `CardEntityManager` + `BoardController`). |
| `DeckCardsPosManager.ts` | **Delete after refactoring** — extract stack layout into `DeckZoneRenderer`. |
| `cloneWithScripts.ts` | **Keep** — evolve to create `CardEntity` objects instead of raw meshes. |
| `types.ts` | **Expand** — add strongly-typed game models. |

---

## Architectural Principles

1. **State before visuals** — `GameStateStore` updates instantly on event receipt. Animations are a visual echo of already-committed state. This prevents sync bugs.
2. **One orchestrator** — `BoardController` is the only script that listens to state changes and routes them to zones/animations. Zone renderers never subscribe to network events directly.
3. **Cards are entities, not meshes** — every interaction goes through `CardEntity` → `instanceId` → `GameStateStore`. Never reason about raw meshes for game logic.
4. **Valid actions drive interactivity** — the backend already computes what's legal. The frontend never re-implements game rules. `ActionBuilder` translates `valid_actions` into visual affordances.
5. **Animation pipeline serializes visual updates** — events arrive in batches but animate one-by-one. Interaction is disabled while the queue is draining.

---

## Backend Prerequisite

Events use `instance_id: str` (UUID) and `card_id: int` (database ID) to identify cards. Per-player event filtering is implemented in `serialize_events_for_player()` so each client receives only events it is allowed to see.

The frontend uses `CardDefinitionCache` (not a Svelte store) to fetch card definitions by database ID. `GameNetworkManagerComponent` auto-registers instance→card mappings from incoming events, so the client builds its card map incrementally as events arrive.

---

## Implementation Order

The steps are designed to be implemented sequentially. Each builds on the previous:

| Step | Name | Description |
|------|------|-------------|
| 1 | Game Models | Typed TS interfaces mirroring the backend domain |
| 2 | Game State Store | Central client-side state with typed change events |
| 3 | Refactor Network Manager | Forward events to GameStateStore instead of processing inline |
| 4 | Card Entity System | CardEntity + CardEntityManager binding meshes to game data |
| 5 | Zone Renderers | Layout classes for each zone type |
| 6 | Animation Pipeline | Sequential animation queue + core animations |
| 7 | Board Controller | Main orchestrator wiring state → zones → animations |
| 8 | Action Builder | Translates valid_actions into card-level affordances |
| 9 | Interaction Manager | Ray picking, selection, highlighting |
| 10 | HUD Layer | Phase indicator, turn banner, health bars, etc. |
| 11 | Integration & Wiring | Final hookup, scene updates, cleanup of old scripts |

Each step has its own detailed document: `step_01.md` through `step_11.md`.
