import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { GameStateStore } from "./GameStateStore";

const ME = "p1";
const OPP = "p2";

function rawState(overrides: Record<string, unknown> = {}): Record<string, unknown> {
	return {
		active_player_id: ME,
		current_phase: "MAIN",
		cards: {
			mine: { instance_id: "mine", card_id: 42, owner_id: ME, zone: "HAND" },
			hidden: { instance_id: "hidden", card_id: 0, owner_id: OPP, zone: "HAND" },
			unknown: { instance_id: "unknown", owner_id: OPP, zone: "DECK" },
		},
		players: {
			[ME]: { zones: { HAND: { card_ids: ["mine"] } } },
			[OPP]: { zones: { HAND: { card_ids: ["hidden"] }, DECK: { card_ids: ["unknown"] } } },
		},
		...overrides,
	};
}

describe("GameStateStore", () => {
	let store: GameStateStore;

	beforeEach(() => {
		GameStateStore.instance?.dispose();
		store = GameStateStore.getOrCreate(ME);
		store.applyServerState(rawState());
	});

	afterEach(() => {
		GameStateStore.instance?.dispose();
	});

	describe("faceUp derivation (hidden-info rule)", () => {
		it("turns a real card face-up and keeps hidden opponent cards face-down", () => {
			expect(store.getCard("mine")!.faceUp).toBe(true);
			expect(store.getCard("hidden")!.faceUp).toBe(false);
		});

		it("never exposes a real card_id for a face-down opponent card", () => {
			const hidden = store.getCard("hidden")!;
			expect(hidden.faceUp).toBe(false);
			expect(hidden.card_id).toBe(0);
		});

		it("treats a missing card_id as face-down (defaults to 0)", () => {
			expect(store.getCard("unknown")!.faceUp).toBe(false);
		});
	});

	describe("zone queries", () => {
		it("reads cards by player and zone", () => {
			expect(store.getCardsInZone(ME, "HAND" as never).map((c) => c.instance_id)).toEqual(["mine"]);
			expect(store.getMyCardsInZone("HAND" as never).map((c) => c.instance_id)).toEqual(["mine"]);
			expect(
				store.getOpponentCardsInZone("HAND" as never).map((c) => c.instance_id),
			).toEqual(["hidden"]);
		});

		it("returns empty for an unknown player or absent zone", () => {
			expect(store.getCardsInZone("ghost", "HAND" as never)).toEqual([]);
			expect(store.getCardsInZone(ME, "GRAVEYARD" as never)).toEqual([]);
		});
	});

	describe("turn + identity", () => {
		it("exposes the opponent id and whose turn it is", () => {
			expect(store.myPlayerId).toBe(ME);
			expect(store.getOpponentId()).toBe(OPP);
			expect(store.isMyTurn).toBe(true);
			expect(store.currentPhase).toBe("MAIN");
		});

		it("knows when it is not my turn", () => {
			store.applyServerState(rawState({ active_player_id: OPP }));
			expect(store.isMyTurn).toBe(false);
		});
	});

	describe("valid actions + lifecycle", () => {
		it("stores and replaces valid actions", () => {
			const actions = [{ action: "pass", player_id: ME }];
			store.updateValidActions(actions as never);
			expect(store.validActions).toBe(actions);
		});

		it("dispose clears state and the singleton", () => {
			store.dispose();
			expect(GameStateStore.instance).toBeNull();
			const fresh = GameStateStore.getOrCreate(OPP);
			expect(fresh.state).toBeNull();
			expect(fresh.currentPhase).toBeNull();
			expect(fresh.getOpponentId()).toBeNull();
			expect(fresh.getOpponentCardsInZone("HAND" as never)).toEqual([]);
		});
	});
});
