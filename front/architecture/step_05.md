# Step 5: Zone Renderers

> **Depends on:** Step 4 (Card Entity System)  
> **Produces:** `scripts/zones/ZoneRenderer.ts`, `scripts/zones/DeckZoneRenderer.ts`, `scripts/zones/HandZoneRenderer.ts`, `scripts/zones/FieldZoneRenderer.ts`, `scripts/zones/GraveyardZoneRenderer.ts`  
> **See also:** [Architecture Overview](./overview.md) — "Layer Descriptions → 4. Zone Renderers"

## Goal

Create layout classes for each zone type. Each `ZoneRenderer` manages the spatial arrangement of `CardEntity` objects within its zone. Zone renderers are **plain TS classes** (not scene scripts) — they are owned and orchestrated by the `BoardController` (Step 7).

Each renderer receives an **anchor node** from the scene (an empty `TransformNode`) that defines the world-space origin for that zone's layout.

## What to Implement

### File: `scripts/zones/ZoneRenderer.ts` — Interface

```typescript
import type { Vector3 } from "@babylonjs/core/Maths/math.vector";
import type { CardEntity } from "../entities/CardEntity";
import type { Zone } from "../game/models";

interface ZoneRenderer {
  readonly zone: Zone;
  readonly ownerId: string;

  // Add a card entity to this zone's layout
  addCard(entity: CardEntity, animate: boolean): Promise<void>;

  // Remove a card entity from this zone's layout
  removeCard(instanceId: string): void;

  // Reposition all cards (e.g., after add/remove changes spacing)
  repositionAll(animate: boolean): Promise<void>;

  // World-space position where cards should animate TO when entering this zone
  getEntryPosition(index?: number): Vector3;

  // World-space position where cards animate FROM when leaving this zone
  getExitPosition(index?: number): Vector3;

  // Get ordered list of entities currently in this zone
  getEntities(): CardEntity[];

  // Number of cards currently in the zone
  get count(): number;

  // Clean up
  dispose(): void;
}
```

### File: `scripts/zones/DeckZoneRenderer.ts`

Renders a face-down stack of cards.

**Layout:** Cards are stacked vertically (Y-axis offset per card) with slight random Y-rotation jitter. The stack sits at the anchor node's position.

**Behavior:**
- On `addCard`: place at top of stack (highest Y).
- On `removeCard`: remove top card, no repositioning needed.
- `repositionAll`: rebuild stack positions from bottom to top.
- Shows a card count (optional text overlay or the visual stack height implies count).

**Extract from existing `DeckCardsPosManager.ts`:**
- `CARD_STACK_Y_OFFSET = 1.5`
- `MAX_JITTER = 0.08` for rotation
- Blueprint: `"UpsideDownCard_BP"` (but entity creation is now in `CardEntityManager`)

```typescript
class DeckZoneRenderer implements ZoneRenderer {
  constructor(
    zone: Zone.DECK,
    ownerId: string,
    anchorNode: TransformNode  // scene marker node
  );
}
```

### File: `scripts/zones/HandZoneRenderer.ts`

Renders cards in a fan/arc layout. The most complex renderer.

**Layout:** Cards spread in a horizontal arc between left and right bounds, with:
- Horizontal spread proportional to card count
- Vertical arc (parabolic, highest at center)
- Fan rotation (Z-rotation from left to right angle)
- Slight random jitter on rotation axes

**Extract from existing `HandCardsPosManager.ts`:**
- `MAX_HAND_SIZE = 10`
- `HAND_LEFT = -153`, `HAND_RIGHT = 246`
- `ARC_HEIGHT = 80`
- `Z_ROTATION_LEFT = -20°`, `Z_ROTATION_RIGHT = 20°`
- `BASE_ROTATION` quaternion
- `MAX_JITTER = 0.08`

**Behavior:**
- On `addCard`: append to hand, then `repositionAll`.
- On `removeCard`: remove from list, then `repositionAll`.
- `repositionAll`: recalculate all positions using the fan algorithm.

**Perspective handling:**
- For the local player's hand: face-up, angled toward camera.
- For the opponent's hand: face-down, can be a simpler compact layout or even just a count indicator. The `BoardController` will use `faceUp: false` when creating opponent hand entities.

```typescript
class HandZoneRenderer implements ZoneRenderer {
  constructor(
    ownerId: string,
    anchorNode: TransformNode,
    isLocalPlayer: boolean  // affects facing direction and detail level
  );
}
```

### File: `scripts/zones/FieldZoneRenderer.ts`

Renders cards in a row of slots on the game field. Used for **both** SUPPORTING and ATTACKING zones (parameterized by `maxSlots`).

**Layout:** Cards are placed in a horizontal row, evenly spaced, face-up, flat on the table (or slightly tilted toward the camera).

**Parameters:**
- `maxSlots`: 3 for SUPPORTING, 2 for ATTACKING
- `slotSpacing`: horizontal distance between card centers
- `zone`: which zone this renders

**Behavior:**
- On `addCard`: place in first empty slot, or append.
- On `removeCard`: remove from slot, optionally close gaps.
- `repositionAll`: center the row based on current card count.
- Cards should be face-up and flat (rotation facing the camera).

**Perspective handling:**
- Local player's field: closer to camera, cards readable.
- Opponent's field: farther from camera, mirrored position.

```typescript
class FieldZoneRenderer implements ZoneRenderer {
  constructor(
    zone: Zone.SUPPORTING | Zone.ATTACKING,
    ownerId: string,
    anchorNode: TransformNode,
    maxSlots: number,
    isLocalPlayer: boolean
  );
}
```

### File: `scripts/zones/GraveyardZoneRenderer.ts`

Renders destroyed cards in an offset pile. Mostly decorative.

**Layout:** Cards stacked with slight offset (both X and Y) so edges are visible. Face-up.

```typescript
class GraveyardZoneRenderer implements ZoneRenderer {
  constructor(
    ownerId: string,
    anchorNode: TransformNode
  );
}
```

## Scene Setup Requirements

The BabylonJS scene (e.g., `Battle.scene`) must contain empty `TransformNode` markers for each zone:

**Local player (10 anchors):**
- `My_Deck_Anchor`
- `My_Hand_Anchor`
- `My_Supporting_Anchor`
- `My_Attacking_Anchor`
- `My_Graveyard_Anchor`

**Opponent (10 anchors):**
- `Opp_Deck_Anchor`
- `Opp_Hand_Anchor`
- `Opp_Supporting_Anchor`
- `Opp_Attacking_Anchor`
- `Opp_Graveyard_Anchor`

These anchor nodes just need position and rotation — the renderers use them as the origin point for layout calculations.

**Note:** The anchors don't need to exist yet — the `BoardController` will look them up by name and fall back to hardcoded positions if not found. The renderers should be designed to work with either approach.

## Animation in Renderers

When `animate: boolean` is `true`:
- `addCard` should smoothly move the entity to its target position (using BabylonJS `Animation` or direct position interpolation).
- `repositionAll` should smoothly slide all cards to their new positions.

When `animate: false`:
- Instant position snap (for initial setup or state sync).

The renderers handle **intra-zone** animation (repositioning within the zone). **Inter-zone** animation (flying between zones) is handled by the `AnimationPipeline` (Step 6) and coordinated by the `BoardController` (Step 7).

## Constraints

- Plain TS classes, NOT scene scripts (no `IScript` interface).
- Import from BabylonJS core only (Mesh, Vector3, Quaternion, TransformNode, Animation).
- Each renderer must implement the `ZoneRenderer` interface.
- Do NOT subscribe to any events — renderers are told what to do by the `BoardController`.
- Do NOT create or destroy entities — that's `CardEntityManager`'s job. Renderers only position and track entities.

## Agent Prompt

```
Create the zone renderer system for the card game:

1. front/src/babylon-editor/src/scripts/zones/ZoneRenderer.ts (interface)
2. front/src/babylon-editor/src/scripts/zones/DeckZoneRenderer.ts
3. front/src/babylon-editor/src/scripts/zones/HandZoneRenderer.ts
4. front/src/babylon-editor/src/scripts/zones/FieldZoneRenderer.ts
5. front/src/babylon-editor/src/scripts/zones/GraveyardZoneRenderer.ts

Read these files for context:
- front/architecture/step_05.md (this step's spec)
- front/architecture/overview.md (full architecture)
- front/src/babylon-editor/src/scripts/HandCardsPosManager.ts (extract fan layout math from here)
- front/src/babylon-editor/src/scripts/DeckCardsPosManager.ts (extract stack layout from here)
- front/src/babylon-editor/src/scripts/entities/CardEntity.ts (CardEntity from Step 4)
- front/src/babylon-editor/src/scripts/game/models.ts (Zone enum)

Key rules:
1. All renderers implement the ZoneRenderer interface.
2. Plain TS classes, NOT scene scripts. No IScript, no event subscriptions.
3. Renderers receive a TransformNode anchor for world-space positioning.
4. HandZoneRenderer extracts the fan/arc layout algorithm from the existing HandCardsPosManager.
5. FieldZoneRenderer is parameterized (maxSlots, zone type) for reuse on SUPPORTING and ATTACKING.
6. When animate=true, use BabylonJS Animation class for smooth transitions.
7. When animate=false, snap positions instantly.
8. Renderers do NOT create/destroy CardEntities — they only position them.
```
