COMPLETED ✅

# Step 1: Expose Game Domain Types in OpenAPI & Auto-Generate Frontend Models

> **Depends on:** Nothing (first step)  
> **Produces:** Strongly-typed game models in `front/src/lib/api/types.gen.ts` (auto-generated) + `scripts/game/models.ts` (client-only additions)  
> **See also:** [Architecture Overview](./overview.md) — "Layer Descriptions → 1. Game Models"

## Goal

Replace all `dict[str, Any]` / `Record<string, unknown>` usage with concrete types by **exposing the backend's existing Pydantic game models through the OpenAPI spec** and auto-generating TypeScript types via `npm run generate`. No model duplication — reuse the existing classes directly.

## Root Cause

Two things prevent using the existing game models in the WebSocket schemas today:

1. **Enums use `auto()` (integer values)** — Pydantic generates JSON Schema with integer enum values (1, 2, 3...), but `field_serializer` decorators convert them to `.name` strings ("DECK", "HAND"...) at runtime. The OpenAPI spec doesn't match what the frontend receives.

2. **WebSocket schemas use `dict[str, Any]`** — `server.py` erases all type information for game payloads.

## What to Implement

### Part A: Backend — Make existing models OpenAPI-compatible

#### 1. Convert enums to `(str, Enum)` with string values

In `back/app/models/game/enums.py`, change all enums from `auto()` to string values matching their names:

```python
# Before
class Zone(Enum):
    DECK = auto()       # value = 1
    HAND = auto()       # value = 2
    ...

# After
class Zone(str, Enum):
    DECK = "DECK"
    HAND = "HAND"
    SUPPORTING = "SUPPORTING"
    ATTACKING = "ATTACKING"
    GRAVEYARD = "GRAVEYARD"
```

Apply the same pattern to `TurnPhase`, `GameStatus`, `CardStatus`, `DamageType`, and `EffectTiming`.

With `(str, Enum)` and matching name/value, Pydantic v2's `model_dump(mode='json')` serializes as the string value — identical to what the current `field_serializer` decorators produce. The JSON Schema also shows the correct string values.

#### 2. Remove redundant `field_serializer` decorators

Every `field_serializer` that just does `return value.name` is now unnecessary. Remove them from:

- `GameCard.serialize_zone`, `GameCard.serialize_status`
- `GameState.serialize_phase`, `GameState.serialize_status`
- `ZoneState.serialize_zone`
- `AttackDefinition.serialize_type`
- `CardMovedEvent.serialize_from_zone`, `serialize_to_zone`
- `CardAssociatedEvent.serialize_source_zone`
- `DamageDealtEvent.serialize_damage_type`
- `PhaseChangedEvent.serialize_from_phase`, `serialize_to_phase`
- `GameRoom` (in `websocket/models.py`) if it has any enum serializers

Keep non-enum serializers (`serialize_created_at`, `serialize_cards`, `serialize_event_log`, `serialize_deck`).

#### 3. Replace excluded-field serializers with `Field(exclude=True)`

Some `field_serializer` decorators exist only to return `None` (hiding data from the frontend). Replace them with `Field(exclude=True)` so the field is excluded from both serialization **and** the JSON Schema:

```python
# GameState — before:
cards: dict[str, GameCard] = {}
event_log: list[dict[str, Any]] = []

@field_serializer('cards')
def serialize_cards(self, value) -> None:
    return None

@field_serializer('event_log')
def serialize_event_log(self, value) -> None:
    return None

# GameState — after:
cards: dict[str, GameCard] = Field(default_factory=dict, exclude=True)
event_log: list[dict[str, Any]] = Field(default_factory=list, exclude=True)
# Remove both field_serializer methods

# PlayerState — same pattern for deck:
deck: Optional[list[dict]] = Field(default=None, exclude=True)
# Remove serialize_deck method
```

#### 4. Create a discriminated union type for events

The only genuinely new type needed — a union of all event classes for use in the schemas:

**Add to `back/app/models/game/events.py`:**

```python
from typing import Annotated, Union
from pydantic import Field

GameEventUnion = Annotated[
    Union[
        CardDrawnEvent,
        CardMovedEvent,
        CardPlayedEvent,
        CardPromotedEvent,
        CardSwappedEvent,
        CardAssociatedEvent,
        CardEvolvedEvent,
        AttackDeclaredEvent,
        DamageDealtEvent,
        CardDestroyedEvent,
        ElementsConsumedEvent,
        ElementsRestoredEvent,
        TurnStartedEvent,
        TurnEndedEvent,
        PhaseChangedEvent,
        GameStartedEvent,
        GameEndedEvent,
        NoDefenderEvent,
        EffectTriggeredEvent,
        EffectAppliedEvent,
    ],
    Field(discriminator="event_type"),
]
```

> **Note:** For `Field(discriminator="event_type")` to work, each event's `event_type` computed field must return a `Literal` rather than a dynamic `self.__class__.__name__`. This means changing the base class `event_type` from a `computed_field` to a `ClassVar` or `Literal`-typed field on each subclass. Example:
>
> ```python
> class CardDrawnEvent(GameEvent):
>     event_type: Literal["CardDrawnEvent"] = "CardDrawnEvent"
>     ...
> ```
>
> Evaluate whether the discriminated union approach or a simpler `list[GameEvent]` (without discriminator) works better with the OpenAPI generator. If the discriminator adds too much complexity, a non-discriminated `list[GameEvent]` with all fields optional on the base class is an acceptable alternative — the frontend already switches on `event_type` at runtime.

#### 5. Extend `ActionData` for the valid action response

`Action.to_dict()` produces a dict that contains all the same fields the client sends (`ActionData`) plus enrichment fields (`player_id`, `action`, `description`, display names). Rather than re-declaring every field, extend the existing `ActionData`:

**File: `back/app/models/schemas/websocket/game_schemas.py`**

```python
from typing import Optional
from app.models.schemas.websocket.client import ActionData


class ValidActionSchema(ActionData):
    """Action.to_dict() output = ActionData fields + server enrichments."""
    player_id: str
    action: str
    description: str
    # Display names resolved by to_dict() overrides on each Action subclass
    card_name: Optional[str] = None
    attack_name: Optional[str] = None
    target_name: Optional[str] = None
    attacker_name: Optional[str] = None
    supporting_card_name: Optional[str] = None
    attacking_card_name: Optional[str] = None
    association_card_name: Optional[str] = None
    target_card_name: Optional[str] = None
    evolution_card_name: Optional[str] = None
    cards: Optional[list[dict]] = None
```

All action parameter fields (`instance_id`, `attacker_id`, `attack_id`, `swaps`, etc.) are inherited from `ActionData` — zero duplication.

#### 6. Update server WebSocket schemas

Replace `dict[str, Any]` with the actual model types in `back/app/models/schemas/websocket/server.py`:

```python
from app.models.game.state import GameState
from app.models.game.events import GameEventUnion  # or GameEvent if no discriminator
from app.models.schemas.websocket.game_schemas import ValidActionSchema


class GameStartedData(BaseModel):
    success: bool
    game_state: GameState
    events: list[GameEventUnion]
    valid_actions: list[ValidActionSchema] = Field(default_factory=list)


class GameStateData(BaseModel):
    state: Optional[GameState] = None


class ActionResultData(BaseModel):
    success: bool
    error: Optional[str] = None
    events: list[GameEventUnion]
    game_over: bool
    winner_id: Optional[str] = None
    game_state: Optional[GameState] = None
    valid_actions: list[ValidActionSchema] = Field(default_factory=list)


class ValidActionsData(BaseModel):
    actions: list[ValidActionSchema]
```

`GameState`, `GameCard`, `PlayerState`, `ZoneState`, `ElementPool`, `AttackDefinition`, `ElementContribution` — all used directly, zero duplication.

#### 7. Re-generate frontend types

```bash
cd front && npm run generate
```

The generated `types.gen.ts` now contains `GameState`, `GameCard`, `Zone`, `TurnPhase`, all event types, `ValidActionSchema`, etc. — all derived from the existing backend models.

### Part B: Frontend — Client-only type additions

After auto-generation, only a small `models.ts` is needed for types that don't exist on the backend.

**File: `front/src/babylon-editor/src/scripts/game/models.ts`**

```typescript
/**
 * Client-only types that supplement the auto-generated backend types.
 * All backend domain types come from `$lib/api/types.gen.ts` via `npm run generate`.
 */

// Re-export generated types for convenience within the BabylonJS scripts
export type {
  Zone,
  TurnPhase,
  GameStatus,
  CardStatus,
  DamageType,
  GameCard,
  PlayerState,
  GameState,
  GameConfiguration,
  ZoneState,
  ElementContribution,
  ElementPool,
  AttackDefinition,
  ValidActionSchema,
  // Events (names may vary based on what openapi-ts generates)
  CardDrawnEvent,
  CardPlayedEvent,
  CardPromotedEvent,
  // ... etc
} from "$lib/api/types.gen";

/** Visual state for card entities in the 3D scene (purely frontend). */
export enum CardVisualState {
  IDLE = "IDLE",
  HOVERED = "HOVERED",
  SELECTED = "SELECTED",
  DRAGGING = "DRAGGING",
  ANIMATING = "ANIMATING",
  DISABLED = "DISABLED",
}
```

Update `front/src/babylon-editor/src/scripts/game/index.ts` to re-export from `models.ts`.

## Summary of Changes

| File | Change | Duplication? |
|------|--------|-------------|
| `enums.py` | `auto()` → `"STRING"` values, add `str` mixin | No — modifying in place |
| `card.py`, `state.py`, `zone.py`, `attack.py`, `events.py` | Remove redundant enum `field_serializer` decorators | No — deleting code |
| `state.py`, `player.py` | `field_serializer` returning `None` → `Field(exclude=True)` | No — simplifying |
| `events.py` | Add `GameEventUnion` discriminated union type | No — new type composing existing classes |
| `game_schemas.py` | `ValidActionSchema(ActionData)` — extends existing class | No — only adds `to_dict()` enrichment fields |
| `server.py` | Replace `dict[str, Any]` with actual model types | No — removing indirection |
| `models.ts` | Re-exports + `CardVisualState` | No — frontend-only enum |

## Constraints

- Backend runtime behavior is unchanged — `model_dump(mode='json')` produces the same JSON as before.
- Verify existing tests pass after the enum conversion (any code comparing `Zone.DECK.value` to `1` will break and must be updated).
- The `TurnPhase.get_order()` and `next_phase()` methods continue to work — `(str, Enum)` preserves declaration order.
- After the backend changes, run `npm run generate` and verify the new types appear in `types.gen.ts`.

## Backend Reference

Files modified (not duplicated):
- `back/app/models/game/enums.py` — convert to `(str, Enum)`
- `back/app/models/game/card.py` — remove enum serializers
- `back/app/models/game/state.py` — remove enum serializers, `Field(exclude=True)`
- `back/app/models/game/player.py` — `Field(exclude=True)` for deck
- `back/app/models/game/zone.py` — remove enum serializer
- `back/app/models/game/attack.py` — remove enum serializer
- `back/app/models/game/events.py` — remove enum serializers, add `GameEventUnion`
- `back/app/models/schemas/websocket/server.py` — replace `dict[str, Any]`

Files created (minimal):
- `back/app/models/schemas/websocket/game_schemas.py` — `ValidActionSchema(ActionData)` only

## Agent Prompt

```
Implement Step 1 of the frontend architecture: expose backend game domain types through the OpenAPI spec
so they are auto-generated in the frontend. Reuse existing models — do NOT duplicate field definitions.

Read the following backend files first:
- back/app/models/game/enums.py
- back/app/models/game/card.py
- back/app/models/game/state.py
- back/app/models/game/player.py
- back/app/models/game/zone.py
- back/app/models/game/events.py
- back/app/models/game/element.py
- back/app/models/game/attack.py
- back/app/game/actions.py
- back/app/models/schemas/websocket/server.py

Steps:
1. Convert all enums in enums.py from `auto()` to `(str, Enum)` with string values matching
   their names (e.g., `DECK = "DECK"`). This makes JSON Schema match serialized output.
2. Remove all `field_serializer` decorators across game models that just do `return value.name`
   for enum fields — they are now redundant.
3. In state.py and player.py, replace `field_serializer` returning None with `Field(exclude=True)`
   for cards, event_log, and deck.
4. In events.py, add a `GameEventUnion` discriminated union type. Each event subclass needs
   `event_type` as a Literal field (not computed_field) for the discriminator to work.
5. Create `back/app/models/schemas/websocket/game_schemas.py` with `ValidActionSchema` that
   EXTENDS `ActionData` from client.py — only add the to_dict() enrichment fields (player_id,
   action, description, display name fields). Do NOT re-declare action parameter fields.
6. Update server.py to replace all `dict[str, Any]` with the actual model types (GameState,
   GameEventUnion, ValidActionSchema).
7. Run `cd front && npm run generate` to regenerate types.gen.ts.
8. Create `front/src/babylon-editor/src/scripts/game/models.ts` with re-exports of generated
   types + CardVisualState enum (frontend-only).
9. Update front/src/babylon-editor/src/scripts/game/index.ts to re-export from models.ts.
10. Run existing backend tests to verify the enum conversion doesn't break anything.
```
