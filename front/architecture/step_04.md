COMPLETED ✅

# Step 4: Card Entity System

> **Depends on:** Step 1 (Game Models)  
> **Produces:** `scripts/entities/CardEntity.ts`, `scripts/entities/CardEntityManager.ts`  
> **See also:** [Architecture Overview](./overview.md) — "Layer Descriptions → 3. Card Entity System"

## Goal

Create the bidirectional binding between game card data (`ClientCard`) and 3D meshes (`Mesh`). Every card in the game becomes a `CardEntity` — a thin wrapper that holds both the mesh reference and the game data, plus a visual state for interaction feedback.

This solves the core problem: currently cards are just `Mesh[]` arrays with no way to answer "which game card is this mesh?" or "find the mesh for card instance X".

## What to Implement

### File: `front/src/babylon-editor/src/scripts/entities/CardEntity.ts`

```typescript
import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import { CardVisualState, type ClientCard, type Zone } from "../game/models";

class CardEntity {
  readonly instanceId: string;
  private _mesh: Mesh;
  private _cardData: ClientCard;
  private _visualState: CardVisualState = CardVisualState.IDLE;

  constructor(instanceId: string, mesh: Mesh, cardData: ClientCard);

  get mesh(): Mesh;
  get cardData(): ClientCard;
  get visualState(): CardVisualState;
  get ownerId(): string;
  get zone(): Zone;
  get isAlive(): boolean;

  // Update game data (called when GameStateStore processes events)
  updateCardData(data: Partial<ClientCard>): void;

  // Update visual state (called by InteractionManager)
  setVisualState(state: CardVisualState): void;

  // Apply visual effects based on state (glow, outline, opacity)
  applyVisualState(): void;

  // Clean up mesh and references
  dispose(): void;
}
```

### File: `front/src/babylon-editor/src/scripts/entities/CardEntityManager.ts`

```typescript
import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import type { Scene } from "@babylonjs/core/scene";
import { CardEntity } from "./CardEntity";
import type { ClientCard, Zone } from "../game/models";

class CardEntityManager {
  static instance: CardEntityManager | null = null;

  private _entities = new Map<string, CardEntity>();       // instanceId → entity
  private _meshToEntity = new Map<Mesh, CardEntity>();     // mesh → entity (for ray picking)
  private _scene: Scene;

  // Blueprints keyed by purpose
  private _faceUpBlueprint: Mesh | null = null;
  private _faceDownBlueprint: Mesh | null = null;

  constructor(scene: Scene);

  static getOrCreate(scene: Scene): CardEntityManager;

  // --- Blueprint Management ---
  // Find and cache blueprint meshes from the scene by name
  initBlueprints(faceUpName: string, faceDownName: string): void;

  // --- Entity Lifecycle ---
  // Create a new CardEntity by cloning the appropriate blueprint
  createEntity(cardData: ClientCard, faceUp: boolean): CardEntity;

  // Destroy an entity and its mesh
  destroyEntity(instanceId: string): void;

  // --- Lookups ---
  getByInstanceId(instanceId: string): CardEntity | undefined;
  getByMesh(mesh: Mesh): CardEntity | undefined;
  getEntitiesInZone(ownerId: string, zone: Zone): CardEntity[];
  getAllEntities(): CardEntity[];

  // --- Cleanup ---
  dispose(): void;
}
```

### Key Design Decisions

1. **`createEntity` uses `cloneMeshWithScripts`** from the existing utility to clone blueprint meshes. The blueprint name determines face-up vs face-down appearance.

2. **`_meshToEntity` map** enables O(1) lookup from a picked mesh to its CardEntity — critical for the InteractionManager (Step 9).

3. **`updateCardData`** does NOT trigger visual updates directly. Visual updates flow through: `GameStateStore` event → `BoardController` → zone renderer repositioning. The entity just holds the data.

4. **`applyVisualState`** applies BabylonJS visual effects based on the current `CardVisualState`:
   - `IDLE` — default appearance
   - `HOVERED` — slight glow or outline
   - `SELECTED` — stronger glow, raised position
   - `DISABLED` — reduced opacity
   - `DRAGGING` — slightly transparent, follows pointer offset
   - `ANIMATING` — no interaction effects applied

5. **Entities for opponent cards** — opponent's deck and hand cards are created with `faceUp: false`. Field cards for both players are `faceUp: true`. The mesh material/texture determines the visual.

## Blueprint Meshes

The scene must contain two blueprint meshes (already partially in place):
- `"UpsideUpCard_BP"` — face-up card mesh (currently used by `HandCardsPosManager`)
- `"UpsideDownCard_BP"` — face-down card mesh (currently used by `DeckCardsPosManager`)

These are cloned by `CardEntityManager.createEntity()`.

## Constraints

- Import `cloneMeshWithScripts` from the existing `cloneWithScripts.ts` for mesh cloning.
- `CardEntity` should NOT subscribe to any events — it's a passive data holder. The `BoardController` (Step 7) manages entity lifecycle.
- The manager is a singleton because there's one global card registry per game.

## Agent Prompt

```
Create two files for the Card Entity System:
1. front/src/babylon-editor/src/scripts/entities/CardEntity.ts
2. front/src/babylon-editor/src/scripts/entities/CardEntityManager.ts

Read these files for context:
- front/architecture/step_04.md (this step's spec)
- front/architecture/overview.md (full architecture)
- front/src/babylon-editor/src/scripts/game/models.ts (ClientCard, Zone, CardVisualState types)
- front/src/babylon-editor/src/scripts/cloneWithScripts.ts (mesh cloning utility)

Implement as specified in the step doc. Key rules:
1. CardEntity binds a Mesh to a ClientCard with a CardVisualState.
2. Import Zone alongside ClientCard and CardVisualState from "../game/models" in CardEntity.ts.
3. CardEntityManager is a singleton with bidirectional lookups (instanceId↔entity, mesh↔entity).
4. Use cloneMeshWithScripts for creating card meshes from blueprints.
5. applyVisualState() should use BabylonJS features like renderOutline, outlineColor, 
   outlineWidth for HOVERED/SELECTED states, visibility for DISABLED, and reduced opacity for DRAGGING.
6. Entities are passive — they don't subscribe to events or trigger animations.
7. Export both classes.
```
