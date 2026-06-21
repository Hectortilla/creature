import { beforeEach, describe, expect, it, vi } from "vitest";
import { ActionBuilder } from "./ActionBuilder";
import type GameConnection from "../game/GameConnection";
import type { ValidAction } from "../game/types";

function makeAction(extra: Record<string, unknown>): ValidAction {
	return { action: "attack", player_id: "p1", ...extra } as ValidAction;
}

describe("ActionBuilder", () => {
	let sent: unknown[];
	let connection: GameConnection;
	let builder: ActionBuilder;

	beforeEach(() => {
		sent = [];
		connection = { sendAction: vi.fn((d: unknown) => sent.push(d)) } as never;
		builder = new ActionBuilder(connection);
	});

	describe("target highlight set", () => {
		it("collects distinct valid targets for an attacker and flags allowsNoDefender", () => {
			const attack = makeAction({ attacker_id: "A", attack_id: 1, target_card_id: "D1" });
			builder.setValidActions([
				attack,
				makeAction({ attacker_id: "A", attack_id: 1, target_card_id: "D2" }),
				makeAction({ attacker_id: "A", attack_id: 1, target_card_id: "" }), // no-defender variant
				makeAction({ attacker_id: "B", attack_id: 1, target_card_id: "D3" }), // different attacker
			]);

			const { targets, allowsNoDefender } = builder.getValidTargets(attack);
			expect(targets.sort()).toEqual(["D1", "D2"]);
			expect(allowsNoDefender).toBe(true);
			expect(builder.getValidTargetIds(attack).sort()).toEqual(["D1", "D2"]);
		});

		it("returns no targets and no no-defender flag when source id is missing or not two-step", () => {
			expect(builder.getValidTargets(makeAction({ attacker_id: "" }))).toEqual({
				targets: [],
				allowsNoDefender: false,
			});
			expect(
				builder.getValidTargets(makeAction({ action: "pass" })),
			).toEqual({ targets: [], allowsNoDefender: false });
		});

		it("does not flag allowsNoDefender for a non-attack two-step action", () => {
			const swap = makeAction({ action: "swap", supporting_card_id: "S", attacking_card_id: "" });
			builder.setValidActions([swap]);
			expect(builder.getValidTargets(swap).allowsNoDefender).toBe(false);
		});
	});

	describe("card-level queries", () => {
		it("reports which cards an action references, ignoring non-card actions", () => {
			const attack = makeAction({ attacker_id: "A", target_card_id: "D1" });
			const swap = makeAction({ action: "swap", swaps: [["S", "T"]] });
			const associate = makeAction({ action: "associate", instance_ids: ["I1", "I2"] });
			builder.setValidActions([attack, swap, associate, makeAction({ action: "pass" })]);

			expect(builder.isCardInteractable("A")).toBe(true);
			expect(builder.isCardInteractable("S")).toBe(true);
			expect(builder.isCardInteractable("I2")).toBe(true);
			expect(builder.isCardInteractable("unknown")).toBe(false);
			expect(builder.getActionsForCard("A")).toEqual([attack]);
		});

		it("collects every interactable source id across attack/swap/associate", () => {
			builder.setValidActions([
				makeAction({ attacker_id: "A" }),
				makeAction({ action: "swap", supporting_card_id: "S", swaps: [["S", "T"]] }),
				makeAction({ action: "associate", association_card_id: "C", instance_ids: ["I1"] }),
				makeAction({ action: "pass" }), // contributes nothing
			]);
			expect(builder.getInteractableCardIds().sort()).toEqual(["A", "C", "I1", "S", "T"]);
		});
	});

	describe("attack lookups", () => {
		beforeEach(() => {
			builder.setValidActions([
				makeAction({ attacker_id: "A", attack_id: 1, target_card_id: "D1" }),
				makeAction({ attacker_id: "A", attack_id: 2, target_card_id: "" }),
			]);
		});

		it("lists distinct attack ids for an attacker", () => {
			expect(builder.getAttackIdsForAttacker("A").sort()).toEqual([1, 2]);
			expect(builder.getAttackIdsForAttacker("B")).toEqual([]);
		});

		it("finds an attack by attacker/attack_id/target, including the no-defender case", () => {
			expect(builder.findAttackAction("A", 1, "D1")?.attack_id).toBe(1);
			expect(builder.findAttackAction("A", 2, "")?.attack_id).toBe(2);
			expect(builder.findAttackAction("A", 1, "nope")).toBeUndefined();
		});
	});

	describe("action categories", () => {
		it("detects pass/concede availability and the two-step actions", () => {
			const pass = makeAction({ action: "pass" });
			const concede = makeAction({ action: "concede" });
			builder.setValidActions([pass, concede]);

			expect(builder.canPass()).toBe(true);
			expect(builder.canConcede()).toBe(true);
			expect(builder.getPassAction()).toBe(pass);
			expect(builder.getConcedeAction()).toBe(concede);
			expect(builder.isTwoStepAction(makeAction({ action: "attack" }))).toBe(true);
			expect(builder.isTwoStepAction(pass)).toBe(false);
		});

		it("reports pass/concede unavailable when absent", () => {
			builder.setValidActions([makeAction({ attacker_id: "A" })]);
			expect(builder.canPass()).toBe(false);
			expect(builder.canConcede()).toBe(false);
		});
	});

	describe("execute → wire payload", () => {
		it("strips display/meta fields and tags the action_type", () => {
			builder.execute(
				makeAction({
					attacker_id: "A",
					attack_id: 1,
					target_card_id: "D1",
					description: "Attack!",
					card_name: "Dragon",
					attack_name: "Fireball",
					valid_phases: ["MAIN"],
				}),
			);

			expect(sent).toEqual([
				{ action_type: "attack", attacker_id: "A", attack_id: 1, target_card_id: "D1" },
			]);
			const payload = sent[0] as Record<string, unknown>;
			expect(payload.player_id).toBeUndefined();
			expect(payload.description).toBeUndefined();
			expect(payload.card_name).toBeUndefined();
		});
	});
});
