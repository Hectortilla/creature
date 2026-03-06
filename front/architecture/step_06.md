# Step 6: Animation Pipeline

> **Depends on:** Step 4 (Card Entity System), Step 5 (Zone Renderers)  
> **Produces:** `scripts/animation/AnimationPipeline.ts`, `scripts/animation/GameAnimation.ts`, and concrete animation classes  
> **See also:** [Architecture Overview](./overview.md) — "Layer Descriptions → 5. Animation Pipeline"

## Goal

Create a sequential animation queue that plays game event animations one at a time. Backend events arrive in batches (a single `action_result` can contain `[CardDrawnEvent, PhaseChangedEvent, CardPlayedEvent, ...]`), but they must animate sequentially with proper timing and visual clarity.

**Critical principle:** State is already updated in `GameStateStore` before animations play. Animations are purely visual — they show the player what happened, they don't drive state.

## What to Implement

### File: `scripts/animation/GameAnimation.ts` — Interface

```typescript
import type { Scene } from "@babylonjs/core/scene";

interface GameAnimation {
  // Display name for debugging
  readonly name: string;

  // Duration in milliseconds
  readonly duration: number;

  // Execute the animation. Returns a promise that resolves when complete.
  execute(scene: Scene): Promise<void>;

  // Cancel a running animation (snap to end state)
  cancel(): void;
}
```

### File: `scripts/animation/AnimationPipeline.ts`

```typescript
import type { Scene } from "@babylonjs/core/scene";
import type { GameAnimation } from "./GameAnimation";

class AnimationPipeline {
  private _queue: GameAnimation[] = [];
  private _playing = false;
  private _currentAnimation: GameAnimation | null = null;
  private _scene: Scene;

  // Callbacks
  onQueueStarted: (() => void) | null = null;   // first animation begins
  onQueueDrained: (() => void) | null = null;    // last animation finishes

  constructor(scene: Scene);

  get isPlaying(): boolean;
  get queueLength(): number;

  // Add a single animation to the queue. Starts processing if not already playing.
  enqueue(animation: GameAnimation): void;

  // Add a batch of animations. Starts processing if not already playing.
  enqueueBatch(animations: GameAnimation[]): void;

  // Skip all pending animations (snap to end state for current, discard rest)
  skipAll(): void;

  // Process the queue sequentially
  private async processQueue(): Promise<void>;

  dispose(): void;
}
```

**`processQueue` logic:**
```
1. If already playing, return (new items will be processed when current finishes)
2. Set _playing = true, call onQueueStarted()
3. While queue is not empty:
   a. Shift next animation from queue
   b. Set _currentAnimation
   c. await animation.execute(scene)
   d. Clear _currentAnimation
4. Set _playing = false, call onQueueDrained()
```

### Concrete Animation Classes

Create these in `scripts/animation/`:

#### `CardMoveAnimation.ts`

Animates a `CardEntity` moving from one world position to another (inter-zone movement).

```typescript
class CardMoveAnimation implements GameAnimation {
  constructor(
    entity: CardEntity,
    fromPosition: Vector3,
    toPosition: Vector3,
    toRotation?: Quaternion,
    duration?: number  // default 400ms
  );
}
```

Uses BabylonJS `Animation.CreateAndStartAnimation` or manual frame-based interpolation. Moves `entity.mesh.position` along a bezier curve (slight arc for visual polish).

#### `CardFlipAnimation.ts`

Rotates a card 180 degrees to reveal/hide its face.

```typescript
class CardFlipAnimation implements GameAnimation {
  constructor(
    entity: CardEntity,
    faceUp: boolean,
    duration?: number  // default 300ms
  );
}
```

Rotates on X-axis. Optionally swaps material/texture at the midpoint.

#### `AttackAnimation.ts`

Attacker lunges toward the target, holds briefly, returns.

```typescript
class AttackAnimation implements GameAnimation {
  constructor(
    attacker: CardEntity,
    target: CardEntity | Vector3,  // Vector3 for direct attacks with no defender
    duration?: number  // default 600ms
  );
}
```

Three-phase: lunge forward (150ms) → hold at target (100ms) → return to origin (350ms).

#### `DamageAnimation.ts`

Visual impact on a card taking damage — shake, flash red, update health display.

```typescript
class DamageAnimation implements GameAnimation {
  constructor(
    target: CardEntity,
    damage: number,
    remainingHealth: number,
    duration?: number  // default 400ms
  );
}
```

Shake the mesh side-to-side, flash material emissive color red, then fade back.

#### `DestroyAnimation.ts`

Card death animation — shrink, fade out, move to graveyard position.

```typescript
class DestroyAnimation implements GameAnimation {
  constructor(
    entity: CardEntity,
    graveyardPosition: Vector3,
    duration?: number  // default 500ms
  );
}
```

Scale down + fade opacity + move toward graveyard.

#### `DelayAnimation.ts`

A no-op pause. Useful for pacing between events.

```typescript
class DelayAnimation implements GameAnimation {
  constructor(duration: number);
}
```

## Event → Animation Mapping

The `BoardController` (Step 7) will map backend events to animation sequences. Here's the reference mapping:

| Backend Event | Animation Sequence |
|---|---|
| `CardDrawnEvent` | `CardMoveAnimation(deck → hand)` + `CardFlipAnimation(faceUp)` |
| `CardPlayedEvent` | `CardMoveAnimation(hand → supporting slot)` |
| `CardPromotedEvent` | `CardMoveAnimation(supporting → attacking slot)` |
| `CardSwappedEvent` | `CardMoveAnimation(A → B)` + `CardMoveAnimation(B → A)` (could run simultaneously or use parallel wrapper) |
| `AttackDeclaredEvent` | `AttackAnimation(attacker, target)` |
| `DamageDealtEvent` | `DamageAnimation(target, damage, remainingHealth)` |
| `CardDestroyedEvent` | `DestroyAnimation(entity, graveyardPos)` |
| `PhaseChangedEvent` | `DelayAnimation(200)` (HUD handles the visual) |
| `TurnStartedEvent` | `DelayAnimation(500)` (HUD shows turn banner) |

This mapping lives in the `BoardController`, not in the animation pipeline. The pipeline just plays whatever it's given.

## Interaction During Animation

When the pipeline starts playing (`onQueueStarted`), the `InteractionManager` should disable all card interaction. When it finishes (`onQueueDrained`), interaction re-enables.

This is wired up in the `BoardController` (Step 7), not inside the pipeline itself.

## Constraints

- Each animation must resolve its promise when complete, enabling sequential execution.
- Animations should gracefully handle disposed entities (if a card was destroyed mid-animation).
- `cancel()` should snap the entity to the animation's end state, not revert to start.
- Use BabylonJS `Animation` system or `scene.onBeforeRenderObservable` for frame-by-frame updates.
- Do NOT import or depend on `GameStateStore` — animations are purely visual.

## Agent Prompt

```
Create the animation pipeline system for the card game:

1. front/src/babylon-editor/src/scripts/animation/GameAnimation.ts (interface)
2. front/src/babylon-editor/src/scripts/animation/AnimationPipeline.ts (sequential queue)
3. front/src/babylon-editor/src/scripts/animation/CardMoveAnimation.ts
4. front/src/babylon-editor/src/scripts/animation/CardFlipAnimation.ts
5. front/src/babylon-editor/src/scripts/animation/AttackAnimation.ts
6. front/src/babylon-editor/src/scripts/animation/DamageAnimation.ts
7. front/src/babylon-editor/src/scripts/animation/DestroyAnimation.ts
8. front/src/babylon-editor/src/scripts/animation/DelayAnimation.ts

Read these files for context:
- front/architecture/step_06.md (this step's spec)
- front/architecture/overview.md (full architecture)
- front/src/babylon-editor/src/scripts/entities/CardEntity.ts (CardEntity from Step 4)

Key rules:
1. AnimationPipeline processes animations sequentially (await each before starting next).
2. Each animation returns a Promise<void> that resolves on completion.
3. Use BabylonJS Animation class or scene.onBeforeRenderObservable for frame updates.
4. CardMoveAnimation should use a slight bezier arc, not a straight line.
5. Animations must handle disposed entities gracefully (resolve immediately if mesh is gone).
6. cancel() snaps to end state, doesn't revert.
7. onQueueStarted/onQueueDrained callbacks for interaction gating.
8. No state store dependency — animations are purely visual.
```
