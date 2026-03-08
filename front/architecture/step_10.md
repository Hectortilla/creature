COMPLETED ✅

# Step 10: HUD Layer

> **Depends on:** Step 2 (GameStateStore), Step 4 (CardEntityManager), Step 8 (ActionBuilder)  
> **Produces:** `scripts/hud/HudController.ts` and sub-components  
> **See also:** [Architecture Overview](./overview.md) — "Layer Descriptions → 9. HUD Layer"

## Goal

Create the 2D UI overlay that shows game information: current phase, turn indicator, element pool, action buttons (Pass/Concede), card detail panel on hover, and health bars floating above field cards.

The HUD reads from `GameStateStore` and renders using BabylonJS GUI (`AdvancedDynamicTexture`). This keeps all rendering inside the BabylonJS canvas, supports anchoring UI to 3D positions (health bars above cards), and avoids DOM/canvas synchronisation issues.

## What to Implement

### File: `scripts/hud/HudController.ts` — Orchestrator

```typescript
import type { Scene } from "@babylonjs/core/scene";
import type { IScript } from "babylonjs-editor-tools";
import { AdvancedDynamicTexture } from "@babylonjs/gui/2D/advancedDynamicTexture";

class HudController implements IScript {
  private _scene: Scene;
  private _guiTexture: AdvancedDynamicTexture;
  private _stateStore: GameStateStore;
  private _actionBuilder: ActionBuilder;

  // Sub-components
  private _phaseIndicator: PhaseIndicator;
  private _turnBanner: TurnBanner;
  private _elementPoolDisplay: ElementPoolDisplay;
  private _cardDetailPanel: CardDetailPanel;
  private _healthBars: HealthBarManager;
  private _actionButtons: ActionButtonPanel;

  constructor(scene: Scene);

  // onStart: get dependencies via GameNetworkManagerComponent.instance
  // (getStateStore, getConnection), CardEntityManager.instance,
  // InteractionManager (for hoveredEntity), then create ActionBuilder.
  public onStart(): void;
  public onUpdate(): void;
  public onStop(): void;
}
```

### Sub-Components

#### `scripts/hud/PhaseIndicator.ts`

Displays the 7 turn phases as a horizontal bar, highlighting the current phase.

```
  [ DRAW | PLACEMENT | PROMOTION | SWAP | ASSOCIATION | EVOLUTION | ATTACK ]
                        ^^^^^ (highlighted)
```

- Subscribes to `stateStore.on("phaseChanged", ...)`.
- Shows all 7 phases as labeled boxes.
- Highlights the current phase with a different color/glow.
- Dims phases that have already passed in this turn.
- Shows "Your Turn" / "Opponent's Turn" label next to the phase bar.
- Position: top-center of screen.

#### `scripts/hud/TurnBanner.ts`

Full-screen momentary banner that appears when turns change.

- Subscribes to `stateStore.on("turnChanged", ...)`.
- Shows "YOUR TURN" (green) or "OPPONENT'S TURN" (red) in large text.
- Fades in, holds for ~1 second, fades out.
- Position: center of screen, overlaid.

#### `scripts/hud/ElementPoolDisplay.ts`

Shows the local player's available elements for attacks.

- Subscribes to state changes that affect element pool.
- Displays element icons with available/max counts.
- Position: near the player's field area (bottom-left or bottom-right).

#### `scripts/hud/CardDetailPanel.ts`

Shows detailed card info when hovering over a card.

- Reads `InteractionManager.hoveredEntity` (public getter) each frame to determine which card is under the pointer.
- Displays: card name, health (current/max), attack/defense stats, element types, attacks list, status.
- Position: side panel (right side) or floating tooltip near the card.
- Hides when no card is hovered.

> **Note:** Step 9's `InteractionManager` needs a public `get hoveredEntity(): CardEntity | null` getter added. `HudController.onStart` should grab the `InteractionManager` instance and pass it to `CardDetailPanel`.

#### `scripts/hud/HealthBar.ts` / `HealthBarManager`

Floating health bars above field cards (SUPPORTING and ATTACKING zones).

- Uses BabylonJS GUI with `linkWithMesh` to anchor UI to 3D card positions.
- Shows current health / max health as a colored bar (green → yellow → red).
- Updates on `cardHealthChanged` events.
- Created/destroyed when cards enter/leave field zones.

The `HealthBarManager` tracks which cards have health bars and manages their lifecycle.

#### `scripts/hud/ActionButtonPanel.ts`

Fixed buttons for non-card actions.

- **Pass Phase** button — always visible during your turn, calls `ActionBuilder.execute(passAction)`.
- **Concede** button — always visible, shows confirmation dialog before executing.
- Disabled during opponent's turn or during animations.
- Position: bottom-center or bottom-right.

## GUI Technology Choice

Use **BabylonJS GUI** (`@babylonjs/gui`) for all HUD elements:

```typescript
import { AdvancedDynamicTexture } from "@babylonjs/gui/2D/advancedDynamicTexture";
import { TextBlock } from "@babylonjs/gui/2D/controls/textBlock";
import { Rectangle } from "@babylonjs/gui/2D/controls/rectangle";
import { StackPanel } from "@babylonjs/gui/2D/controls/stackPanel";
import { Button } from "@babylonjs/gui/2D/controls/button";
import { Image } from "@babylonjs/gui/2D/controls/image";
```

Create a fullscreen UI texture:
```typescript
this._guiTexture = AdvancedDynamicTexture.CreateFullscreenUI("GameHUD", true, this._scene);
```

### Health Bar Anchoring

For health bars that float above cards in 3D space:
```typescript
const healthRect = new Rectangle("health_" + instanceId);
// ... configure size, color, text
this._guiTexture.addControl(healthRect);
healthRect.linkWithMesh(cardEntity.mesh);
healthRect.linkOffsetY = -50;  // above the card
```

## Visual Style Guide

- **Phase bar:** Dark semi-transparent background, current phase in bright accent color.
- **Turn banner:** Large bold text, semi-transparent backdrop, smooth fade animation.
- **Buttons:** Rounded rectangles with hover effects, disabled state (greyed out).
- **Health bars:** Small, compact, colored gradient (green → red), white text.
- **Card detail panel:** Dark panel with card illustration area (future), stat rows, compact layout.
- **General:** Use a consistent color palette. Suggest dark blue/purple tones for background, gold for highlights, white text.

## Constraints

- `HudController` is an `IScript` scene script — attach to a scene node.
- Sub-components are plain TS classes, owned by `HudController`.
- All HUD elements read from `GameStateStore` — they never modify game state.
- Health bars must be created/destroyed in sync with field card entities.
- The HUD should not block ray picking for the `InteractionManager` — use `isPointerBlocker = false` for non-interactive elements.
- Pass/Concede buttons ARE pointer blockers (they consume clicks).

## Agent Prompt

```
Create the HUD layer for the card game:

1. front/src/babylon-editor/src/scripts/hud/HudController.ts (orchestrator, IScript)
2. front/src/babylon-editor/src/scripts/hud/PhaseIndicator.ts
3. front/src/babylon-editor/src/scripts/hud/TurnBanner.ts
4. front/src/babylon-editor/src/scripts/hud/ElementPoolDisplay.ts
5. front/src/babylon-editor/src/scripts/hud/CardDetailPanel.ts
6. front/src/babylon-editor/src/scripts/hud/HealthBar.ts (includes HealthBarManager)
7. front/src/babylon-editor/src/scripts/hud/ActionButtonPanel.ts

Read these files for context:
- front/architecture/step_10.md (this step's spec)
- front/architecture/overview.md (full architecture)
- front/src/babylon-editor/src/scripts/state/GameStateStore.ts (state store)
- front/src/babylon-editor/src/scripts/state/ActionBuilder.ts (for action buttons)
- front/src/babylon-editor/src/scripts/entities/CardEntity.ts
- front/src/babylon-editor/src/scripts/entities/CardEntityManager.ts (for health bar lifecycle)
- front/src/babylon-editor/src/scripts/interaction/InteractionManager.ts (hoveredEntity for CardDetailPanel)
- front/src/babylon-editor/src/scripts/game/models.ts (TurnPhase, Zone types)
- front/src/babylon-editor/src/scripts/GameNetworkManagerComponent.ts (dependency access pattern)

Key rules:
1. Use BabylonJS GUI (AdvancedDynamicTexture, TextBlock, Rectangle, Button, etc.).
2. HudController is an IScript that creates a fullscreen GUI texture and initializes sub-components.
3. PhaseIndicator shows all 7 phases, highlights the current one.
4. TurnBanner shows "YOUR TURN" / "OPPONENT'S TURN" with fade animation.
5. HealthBar uses linkWithMesh to float above field cards.
6. ActionButtonPanel has Pass Phase and Concede buttons.
7. Non-interactive elements set isPointerBlocker = false to not interfere with card picking.
8. All components subscribe to GameStateStore for data — they never modify state.
9. Register HudController in scripts.ts after creation.
```
