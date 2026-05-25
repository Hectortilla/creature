# Game Engine

The game engine is an **event-driven, pipeline-based** rules engine for the Creature card game. It is intentionally split into small, single-responsibility modules so that game rules, state mutations, and reactive card effects can evolve independently.

This document is meant for developers who need to **extend** (add an action, event, or skill), **refactor**, or **debug** the engine. If you only need to call into the engine, jump to [Public API](#public-api).

---

## Table of contents

1. [Core ideas](#core-ideas)
2. [The pipeline](#the-pipeline)
3. [Module map](#module-map)
4. [Public API](#public-api)
5. [Domain model (quick tour)](#domain-model-quick-tour)
6. [The event loop in detail](#the-event-loop-in-detail)
7. [Extending the engine](#extending-the-engine)
   - [Adding an Action](#adding-an-action)
   - [Adding an Event](#adding-an-event)
   - [Adding an Effect / Skill](#adding-an-effect--skill)
   - [Adding an Element](#adding-an-element)
8. [Invariants and gotchas](#invariants-and-gotchas)
9. [Testing notes](#testing-notes)

---

## Core ideas

The engine rests on five ideas. If you internalize these, the code reads itself.

1. **Actions describe intent, events describe what happened.**
   The outside world (UI, AI, replays, API) speaks to the engine in `Action`s. The engine speaks back in `GameEvent`s. The event log *is* the game's history — nothing else is canonical.

2. **State changes only happen in the reducer.**
   Every mutation to `GameState` or `PlayerState` is funneled through [reducer.py](reducer.py)'s `apply_event`. If you find yourself mutating state anywhere else, that's a bug.

3. **Actions are self-contained.**
   Each action knows: its valid phases, how to validate itself, how to translate itself into events, and how to enumerate all its currently-valid forms. This makes adding a new action a single-file change.

4. **Effects react to events.**
   Card skills don't run inline with actions. They subscribe to event triggers (`ON_PLAY`, `ON_ATTACK`, …) and emit *new* events that flow back through the pipeline. This is what makes chains and counters expressible.

5. **The engine is stateless.**
   [GameEngine](engine.py) holds no game state. It is a coordinator. Game state lives in `GameState`/`PlayerState` objects passed in and out. This makes the engine trivially safe to share across games/threads/sessions.

---

## The pipeline

```
                  ┌────────────────┐
   client/AI ──▶  │   Action       │  intent
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ RuleValidator  │  common pre-checks (status, turn, phase)
                  └───────┬────────┘  + action.validate(state)
                          │
                          ▼
                  ┌────────────────┐
                  │ action.to_     │  pure: state → list[GameEvent]
                  │   events(state)│
                  └───────┬────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │              EventLoop                  │
        │  while queue not empty:                 │
        │    event = queue.popleft()              │
        │    state = reducer.apply_event(...)     │◀──┐
        │    new = effects.trigger(event, state)  │   │
        │    queue.extend(new)                    │───┘ effects can spawn events
        │  ───────────────────────────────────    │
        │  if no actions in phase → auto-advance  │
        └─────────────────────┬───────────────────┘
                              │
                              ▼
                  ┌───────────────────┐
                  │  ActionResult     │  new state + full event log
                  └───────────────────┘
```

Every action — drawing a card, attacking, conceding, even the initial game start — flows through this exact pipeline.

---

## Module map

| File | Responsibility | Touch when… |
|---|---|---|
| [`__init__.py`](__init__.py) | Package docstring, no runtime code | Updating the high-level summary |
| [`engine.py`](engine.py) | `GameEngine` — orchestrator. `create_game`, `start_game`, `process_action`, `get_valid_actions` | Changing how the pipeline is wired or what `ActionResult` exposes |
| [`validators.py`](validators.py) | `RuleValidator` — common pre-checks before delegating to `action.validate()` | Adding a cross-cutting precondition (e.g. a new global game status) |
| [`event_loop.py`](event_loop.py) | `EventLoop` — drains the event queue, fires effects, auto-advances empty phases | Changing how triggers are routed or how chains resolve |
| [`reducer.py`](reducer.py) | `apply_event` + `_handler`-decorated reducers, one per event type | Adding a new event type (you must register a handler) |
| [`effects.py`](effects.py) | `Effect` base class + built-in effect types + `_EFFECT_INSTANCES` registry + passive-modifier helpers | Adding a new skill type, or new trigger kind |
| [`elements.py`](elements.py) | Element interaction matrix, damage formula | Tuning the type chart, defense math, or attack cost rules |
| [`actions/`](actions/) | One file per action family (placement, promotion, combat, …) | Adding a new player action |
| [`actions/combat.py`](actions/combat.py) | `AttackAction`, `ForceDefendAction`, and `build_combat_events()` — shared combat event generation | Changing how attacks resolve into events |

---

## Public API

Most callers only need three things:

```python
from app.game.engine import get_engine

engine = get_engine(config)              # singleton; pass GameConfiguration on first call

state = engine.create_game(room)         # build initial GameState from a GameRoom
result = engine.start_game(state)        # first-turn setup; returns ActionResult

# Driving a turn:
result = engine.process_action_from_dict(state, player_id, {
    "action_type": "play_card",
    "instance_ids": ["card-uuid"],
})

if result.success:
    state = result.state                 # new authoritative state
    events = result.events               # full ordered event log for this action
    valid = result.valid_actions         # next legal actions, for UI/AI
else:
    error = result.error
```

`ActionResult` is the single return shape from every call. Inspect `success`, `error`, `events`, `state`, `final_players`, `game_over`, `winner_id`, and `valid_actions`.

`get_valid_actions(state)` is also worth knowing — it asks every registered `Action` class for its valid forms in the current phase. UI uses this to populate buttons; AI uses it as a move generator.

---

## Domain model (quick tour)

The engine reads from and writes to types defined in [`app/models/game/`](../models/game/). The pieces that show up everywhere:

- **`GameState`** — top-level state. Owns `cards` (instance_id → `GameCard`), `room` (which owns `players`), `status`, `current_phase`, `active_player_id`, `turn_number`, plus paused-attack bookkeeping (`pending_action`, `pending_defender_id`, `pending_attack`).
- **`PlayerState`** — per-player: `zones` (HAND/DECK/SUPPORTING/ATTACKING/GRAVEYARD), `element_pool`, `turn_count`.
- **`GameCard`** — a card *instance* on the table. Holds runtime fields like `zone`, `current_health`, `turns_in_zone`, `swapped_this_turn`, `status` (READY/SWAPPED/ASSOCIATED), `associations`, plus static fields copied from the catalog card (`attacks`, `element_contribution`, `skill_ids`).
- **`Zone`** — enum: `HAND | DECK | SUPPORTING | ATTACKING | GRAVEYARD`. The two "active" zones — where cards interact with the game — are SUPPORTING and ATTACKING.
- **`TurnPhase`** — enum: `DRAW → PLACEMENT → PROMOTION → SWAP → ASSOCIATION → EVOLUTION → ATTACK`. Each phase has its own action set; `PassPhaseAction` advances through them and rolls to the next player's turn at the end.
- **`GameEvent`** subclasses — `CardDrawnEvent`, `CardPlayedEvent`, `AttackDeclaredEvent`, etc. These are immutable records of what changed.

The big picture: **`GameState` is the *what is*, the event log is the *what happened*.**

---

## The event loop in detail

[event_loop.py](event_loop.py) is the heart of the engine. Read this carefully if you're changing how cards interact.

### Processing one batch of events

`EventLoop.process(state, players, initial_events)`:

1. Push `initial_events` onto a FIFO queue.
2. Pop the next event, call `reducer.apply_event` to mutate state.
3. Determine which `(EffectTrigger, card_id)` pairs the event activates via [`_get_trigger_pairs`](event_loop.py).
4. For each pair, look up the card's skills, find effects that subscribe to that trigger, call `effect.execute(...)`, and append the returned events to the queue.
5. Repeat until the queue is drained.

This is what makes reactive sequences work: an `ON_DESTROY` effect that deals damage queues a `DamageDealtEvent`, which may itself be a `CardDestroyedEvent`, which may trigger another `ON_DESTROY`. The queue absorbs the chain naturally.

### Trigger routing

Most event types map 1:1 to a trigger via `EVENT_TO_TRIGGER` and fire that trigger on **every active card** of both players (the cards' own `should_trigger` filters narrow it down).

Combat events are special because they target specific cards:

| Event | Triggers fired |
|---|---|
| `AttackDeclaredEvent` | `ON_ATTACK` on attacker, `ON_DEFEND` on target |
| `DamageDealtEvent` | `ON_DEAL_DAMAGE` on source, `ON_TAKE_DAMAGE` on target |
| `CardPlayedEvent` | `ON_PLAY` on all active cards (effects filter to self via `should_trigger`) |
| `CardPromotedEvent` | `ON_PROMOTE` on all active cards |
| `CardDestroyedEvent` | `ON_DESTROY` on all active cards |
| `TurnStartedEvent` / `TurnEndedEvent` | `ON_TURN_START` / `ON_TURN_END` on all active cards |

If you add a trigger that should fan out to all cards, just put it in `EVENT_TO_TRIGGER`. If it has to target specific cards (like combat does), special-case it in `_get_trigger_pairs`.

### Auto-advance

After the queue drains, the loop checks whether the current phase has any legal action available to the active player. If not, it auto-pushes a `PassPhaseAction` so the player doesn't get stuck on, say, an Evolution phase with no evolutions in hand. The cap (`max_auto_advance = 14`) prevents pathological infinite loops if game rules change in a way that no phase ever has an action.

### Safety cap

`max_iterations = 1000` is a hard ceiling on events processed per call. If an effect loop genuinely runs away, you'll see truncated output rather than a hang. Bump this only if you're confident the chain is bounded.

---

## Extending the engine

### Adding an Action

Player actions live in [`actions/`](actions/), one file per family (placement, promotion, swap, …). To add a new one:

1. **Create a class** subclassing `Action`. Pick a sensible `action_type` string, set `valid_phases` (or `None` for any-phase), declare any parameters as pydantic fields.

   ```python
   class HealAction(Action):
       action_type: str = "heal"
       valid_phases: list[TurnPhase] | None = [TurnPhase.PLACEMENT]
       target_card_id: str = ""
   ```

2. **Implement `validate(state)`** — return a `ValidationResult` with a stable `error_code`. The common pre-checks (turn, phase, status) are handled by `RuleValidator`; only validate things specific to your action.

3. **Implement `to_events(state)`** — pure function from state to a list of events. Do **not** mutate state here. If your action needs a new event type, add it (see next section).

4. **Implement `get_valid(state, player_id)`** — enumerate every legal form of this action in the current state. Used by `get_valid_actions` for UI/AI and by `EventLoop`'s auto-advance check. If your action takes no parameters (like `PassPhaseAction`), this can be trivial; if it takes a target, iterate the candidates.

5. **Register it** in [`actions/__init__.py`](actions/__init__.py) — add the import and an entry in `ACTION_TYPES`.

The action will now be reachable via `engine.process_action_from_dict(state, player_id, {"action_type": "heal", ...})` and will show up in `get_valid_actions` automatically.

### Adding an Event

Events live in [`app/models/game/events.py`](../models/game/events.py) (outside the engine package — they're part of the wire format).

1. **Define the event** as a pydantic subclass of `GameEvent`. Include all fields needed to fully describe what happened. Events are serialized and sent to clients, so include human-readable fields (`card_name`, `attack_name`) for the UI.

2. **Register a reducer** in [reducer.py](reducer.py):

   ```python
   @_handler(MyNewEvent)
   def _apply_my_new_event(state, players, event):
       # mutate state and/or players in place
       return state, players
   ```

   The reducer is the **only** place state mutates for this event. If you find yourself reaching for mutation elsewhere, stop and add a reducer.

3. **(Optional) Route it to a trigger.** If cards should react to this event:
   - For a generic "fires on every active card" trigger: add a new `EffectTrigger` value in [effects.py](effects.py), then map your event type to it in `EVENT_TO_TRIGGER` in [event_loop.py](event_loop.py).
   - For a targeted trigger (specific source/target cards): special-case it in `EventLoop._get_trigger_pairs`.

4. **(Optional) Element recalculation.** If your event changes which cards are in active zones or their status, the relevant reducer probably needs to call `_recalculate_elements(state, players, player_id)`. Compare with existing reducers — `_apply_card_played`, `_apply_card_destroyed`, etc. all do this.

### Adding an Effect / Skill

Effects implement card skills. They are pre-configured at module load and looked up by `skill_id`.

1. **Subclass `Effect`** in [effects.py](effects.py) (or wherever your effects live):

   ```python
   class OnPlayDrawEffect(Effect):
       def __init__(self, effect_id, name, draw_count):
           super().__init__(effect_id, name, f"Draw {draw_count} on play")
           self.draw_count = draw_count

       @property
       def triggers(self): return [EffectTrigger.ON_PLAY]

       def should_trigger(self, context):
           if not super().should_trigger(context): return False
           return (isinstance(context.trigger_event, CardPlayedEvent)
                   and context.trigger_event.instance_id == context.source_card.instance_id)

       def execute(self, context):
           # Build the events you want to queue
           return EffectResult(events=[...])
   ```

2. **`triggers`** is the list of `EffectTrigger`s this effect responds to. The event loop will only invoke the effect when the event maps to one of these.

3. **`should_trigger(context)`** is your conditional filter. The default checks that the source card is in an active zone — call `super().should_trigger(context)` and add your own conditions. For "this card only" effects, compare `context.trigger_event` to `context.source_card.instance_id`.

4. **`execute(context)`** returns an `EffectResult`. The interesting field is `events` — those are appended to the event queue and processed in turn. Don't mutate state directly here; emit an event and let the reducer do it.

5. **Register instances** at module load. `register_effect(effect_instance)` stores it in `_EFFECT_INSTANCES` keyed by `effect_id`. Card data references skills by `skill_id` (which must equal the registered `effect_id`, as a string).

6. **Passive effects** are a special case: they have a `PASSIVE` trigger but aren't event-driven. They are read by query helpers — `get_passive_stat_modifiers` (used in damage calculation) and `get_passive_element_bonus` (used in `_recalculate_elements`). If you add a new kind of passive, add a helper that walks active cards and sums up the modifier, and call it from wherever the stat is computed.

### Adding an Element

[elements.py](elements.py) is a single matrix table:

1. Add the element to `ElementId` (and to the database — this enum mirrors the catalog).
2. Add a row to `_RELATIONSHIPS` listing what it's strong/weak against. The matrix is regenerated from this dict at import.
3. That's it — `get_element_bonus` and `calculate_damage` will pick it up automatically.

---

## Invariants and gotchas

These are the rules the engine implicitly assumes. Break them and things will get strange.

- **The reducer is the only mutator.** Anywhere else (validate, to_events, get_valid, effects' execute) you must treat state as read-only. If you need to change state, emit an event.
- **`apply_event` mutates in place** but returns `(state, players)` for compatibility with older call sites. Don't be misled — the input objects are modified. If you need an unchanged copy, deepcopy *before* calling.
- **`state.room.players` is kept in sync** with the `players` dict at the end of every `apply_event` and again after the event loop. Mid-reducer, prefer the `players` parameter — `state.room.players` may be stale until the assignment at the bottom of the handler.
- **Effects can return events that destroy their own source card.** That's fine; the loop will continue, but the card will be gone from active zones. Any `should_trigger` filter that requires the card to be active will then correctly skip it. Don't assume the source still exists across recursive triggers.
- **Element pool recalculation preserves consumed state.** `_recalculate_elements` doesn't reset spent elements — it adjusts max and re-applies the diff. If you change how elements are spent or refreshed, look at this function carefully.
- **`PassPhaseAction` is the turn machine.** Ending a phase, ending a turn, drawing for the new turn, and restoring elements all happen inside its `to_events`. Don't replicate this logic elsewhere; reuse `PassPhaseAction` if you need to advance the turn.
- **`force_defend` puts the game in `PAUSED`.** When an attacker has no targets but the defender has supporting cards, the engine pauses and waits for a `ForceDefendAction`. `RuleValidator` allows only `ForceDefendAction` and `ConcedeAction` while paused. If you add an action that should be allowed during pause, update `RuleValidator.validate`.
- **`auto_advance` is bounded.** It will only skip empty phases up to `max_auto_advance = 14`. Don't add a phase whose validity depends on side effects that haven't fired yet.
- **`get_valid_actions` is called frequently** (after every action, for the UI). Keep `get_valid` implementations cheap — don't simulate, just enumerate.
- **`process_action` swallows exceptions** and returns them in `ActionResult.error` as a full traceback. That's intentional — a buggy card effect should not crash the game session. But during development, watch logs for these silent failures.

---

## Testing notes

The engine is pure-function-friendly, which makes it easy to test:

- **Unit-test reducers** by constructing minimal `GameState` / `PlayerState` objects, applying a single event, and asserting on the result.
- **Unit-test actions** by setting up a state, calling `action.validate(state)` and `action.to_events(state)`, and asserting on the validation result and event list.
- **Integration-test the loop** by calling `engine.process_action(state, action)` end-to-end and asserting on `result.events` and `result.state`.
- **Property-test legality** by asserting that every action returned by `get_valid_actions` is `valid` according to `RuleValidator.validate`. If they disagree, that's a bug in either the validator or `get_valid`.

When debugging a weird interaction, the event log (`result.events`) is your friend — print it. Every state change has a corresponding event, in order.
