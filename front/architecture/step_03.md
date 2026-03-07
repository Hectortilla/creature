COMPLETED ✅

# Step 3: Refactor GameNetworkManagerComponent

> **Depends on:** Step 2 (Game State Store)  
> **Modifies:** `scripts/GameNetworkManagerComponent.ts`  
> **See also:** [Architecture Overview](./overview.md) — "Existing Code Disposition"

## Goal

Simplify `GameNetworkManagerComponent` so it acts purely as a **transport bridge**: it connects the WebSocket (`GameConnection`) to the `GameStateStore`. It should no longer be the place where other scripts subscribe to game events — that role moves to `GameStateStore`.

The existing `on()`/`off()` and `onGameEvent()`/`offGameEvent()` APIs remain for backward compatibility during the transition, but all state-relevant events are now forwarded to `GameStateStore` first.

## What to Change

### Current flow (before)

```
GameConnection → GameNetworkManager.callbacks → emit("gameStarted") → DeckCardsPosManager
                                               → emitGameEvent("CardDrawnEvent") → HandCardsPosManager
```

### New flow (after)

```
GameConnection → GameNetworkManager.callbacks → GameStateStore.processXxx()
                                               → still emit() for backward compat
BoardController (later) subscribes to GameStateStore, not to GameNetworkManager
```

### Modifications to `GameNetworkManagerComponent.ts`

1. **Import and initialize `GameStateStore`** in `onStart()`:
   ```typescript
   import { GameStateStore } from "./state/GameStateStore";

   // In onStart():
   this._stateStore = GameStateStore.getOrCreate(this.playerId);
   ```

2. **Forward events to the store** in the `callbacks` object passed to `GameConnection`:
   ```typescript
   callbacks: {
     onGameStarted: (data) => {
       this._stateStore?.processGameStarted(data);
       this.emit("gameStarted", data);  // backward compat
     },
    onGameEvents: (events) => {
      this._stateStore?.processGameEvents(events);
      // Still emit individual game events + register cards for backward compat
      for (const event of events) {
        this.registerCardFromEvent(event);
        const eventType = event.event_type as string;
        if (eventType) this.emitGameEvent(eventType, event);
      }
    },
     onGameStateChange: (state) => {
       if (state) this._stateStore?.processGameState(state);
       this.emit("gameStateChange", state);
     },
     onValidActionsChange: (actions) => {
       this._stateStore?.updateValidActions(actions);
       this.emit("validActionsChange", actions);
     },
     // onMessage, onConnectionChange, onError remain unchanged
   }
   ```

3. **Expose the store** via a getter:
   ```typescript
   public getStateStore(): GameStateStore | null {
     return this._stateStore;
   }
   ```

4. **Dispose the store** in `onStop()`:
   ```typescript
   this._stateStore?.dispose();
   this._stateStore = null;
   ```

## What NOT to Change

- Keep `GameConnection` as-is.
- Keep `on()`/`off()` and `onGameEvent()`/`offGameEvent()` APIs — they'll be removed in the final integration step (Step 11) after all consumers are migrated.
- Keep all `@visibleAs*` editor properties.
- Keep the singleton `instance` pattern.

## Constraints

- This is a modification to an existing file, not a new file.
- The existing `DeckCardsPosManager` and `HandCardsPosManager` must continue to work (they still use the old event APIs). They'll be replaced in Step 5.

## Agent Prompt

```
Modify `front/src/babylon-editor/src/scripts/GameNetworkManagerComponent.ts` to forward
game events to the new GameStateStore.

Read these files for context:
- front/architecture/step_03.md (this step's spec)
- front/src/babylon-editor/src/scripts/GameNetworkManagerComponent.ts (current file)
- front/src/babylon-editor/src/scripts/state/GameStateStore.ts (the store from Step 2)
- front/src/babylon-editor/src/scripts/game/types.ts (ValidAction, GameConnectionCallbacks)

Changes:
1. Import GameStateStore from "./state/GameStateStore".
2. Add a private _stateStore field.
3. In onStart(), after setting the singleton, create the store: this._stateStore = GameStateStore.getOrCreate(this.playerId).
4. In initializeConnection(), update the callbacks to forward events to the store BEFORE emitting to legacy listeners.
5. Keep registerCardFromEvent() in the onGameEvents loop — the store handles registration internally for CardDrawn/CardEvolved, but keeping it here is a safety net for any event carrying instance_id/card_id during the transition.
6. Add a public getStateStore() getter.
7. In onStop(), dispose and null out the store.
8. Keep ALL existing APIs (on/off/onGameEvent/offGameEvent/emit/emitGameEvent) for backward compatibility.
9. Do NOT modify GameConnection.ts or any other file.
```
