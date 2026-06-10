import { expect, test } from "@playwright/test";

import { SCENE_TIMEOUT, startTwoPlayerGame } from "./game-setup";
import {
	passToPhase,
	passWholeTurn,
	placeIntoSupporting,
	promoteToAttacking,
	waitForGameReady,
	waitForMyTurn,
} from "./harness";

/**
 * Gameplay flow: `attack` damages an opponent's ATTACKING card (@nongating).
 *
 * Like the other gameplay specs, this proves WIRING, not rules: an `attack` intent
 * round-trips the WebSocket, combat resolves server-side, and the health drop reaches
 * BOTH clients' caches via the build-gated `window.__creature` API.
 *
 * It needs the most setup: by turn 3 BOTH players field an ATTACKING card and the
 * attacker can AFFORD an attack (else the ATTACK phase is empty and auto-skipped). The
 * driver builds that over three turns (GAME_SEED); the attacker and attack are DERIVED
 * from the seeded deal, not hard-coded. Asserts the target's `current_health` dropped
 * (or it was destroyed) on the actor's store AND the opponent's snapshot. Non-gating.
 */

/** SUPPORTING zone cap — the most cards (hence elements) the actor can field. */
const SUPPORTING_CAP = 3;

test.describe("@nongating gameplay: attack damages an opponent's card", () => {
	test("actor attacks a defending card; both clients see the health drop", async ({
		browser,
	}) => {
		// Two software-WebGL scene loads + a three-turn build-up.
		test.setTimeout(SCENE_TIMEOUT * 2 + 120_000);

		const { hostPage, guestPage, close } = await startTwoPlayerGame(browser);

		try {
			await waitForGameReady(hostPage);
			await waitForGameReady(guestPage);

			// Seeded first player drives the attack; the other owns the target and sees the damage.
			const hostIsActive = await hostPage.evaluate(() =>
				window.__creature!.isMyTurn(),
			);
			const actor = hostIsActive ? hostPage : guestPage;
			const observer = hostIsActive ? guestPage : hostPage;

			expect(await actor.evaluate(() => window.__creature!.phase())).toBe(
				"PLACEMENT",
			);

			// turn 1: actor fills SUPPORTING; opponent fields one card
			await placeIntoSupporting(actor, SUPPORTING_CAP);

			// Derive the attacker from the seeded deal: a placed card whose attack cost is
			// covered by the actor's total element pool. Promoting an unaffordable attacker
			// would leave the ATTACK phase empty and auto-skipped.
			const attackerId = await actor.evaluate(() => {
				const c = window.__creature!;
				const cards = c.cardsInZone("SUPPORTING", "my");
				const pool: Record<number, number> = {};
				for (const card of cards) {
					for (const e of card.element_contribution ?? []) {
						pool[e.element_id] = (pool[e.element_id] ?? 0) + e.amount;
					}
				}
				const affordable = cards.find((card) =>
					(card.attacks ?? []).some((atk) =>
						(atk.necessary_force ?? []).every(
							(f) => (pool[f.element_id] ?? 0) >= f.amount,
						),
					),
				);
				if (!affordable) {
					throw new Error("attack: no affordable attacker in the seeded deal");
				}
				return affordable.instance_id;
			});

			await passWholeTurn(actor);

			await waitForMyTurn(observer);
			const [targetSeedId] = await placeIntoSupporting(observer, 1);
			await passWholeTurn(observer);

			// turn 2: actor promotes the attacker; opponent promotes the target
			await waitForMyTurn(actor);
			await promoteToAttacking(actor, attackerId);
			// Opponent has no ATTACKING card yet, so the actor can't hit a real target — just end the turn.
			await passWholeTurn(actor);

			await waitForMyTurn(observer);
			await promoteToAttacking(observer, targetSeedId);
			await passWholeTurn(observer);

			// turn 3: both boards populated + an affordable attack → ATTACK
			await waitForMyTurn(actor);
			await passToPhase(actor, "ATTACK");

			// Derive the attack from the server's offer (real defender + affordable cost); capture target health.
			const {
				attackerId: aId,
				targetId,
				beforeHealth,
			} = await actor.evaluate(() => {
				const c = window.__creature!;
				const atk = c
					.validActions()
					.find((a) => a.action === "attack" && !!a.target_card_id);
				if (!atk) {
					throw new Error(
						"attack: no targeted attack offered in ATTACK phase " +
							`(validActions: ${JSON.stringify(c.validActions().map((a) => a.action))})`,
					);
				}
				const target = c
					.cardsInZone("ATTACKING", "opp")
					.find((card) => card.instance_id === atk.target_card_id);
				return {
					attackerId: atk.attacker_id!,
					targetId: atk.target_card_id!,
					beforeHealth: target?.current_health ?? target?.health ?? null,
				};
			});
			expect(
				beforeHealth,
				"target health readable before attack",
			).not.toBeNull();

			// Attack through the REAL path; await the damage landing (off the event bus, no sleeps).
			await actor.evaluate(
				async ({ attackerId, targetId, beforeHealth }) => {
					const c = window.__creature!;
					c.attack(attackerId, targetId);
					await c.waitForState((s) => {
						const t = s
							.getOpponentCardsInZone("ATTACKING")
							.find((card) => card.instance_id === targetId);
						return (
							t === undefined ||
							(t.current_health ?? t.health ?? 0) < beforeHealth!
						);
					});
				},
				{ attackerId: aId, targetId, beforeHealth },
			);

			// Actor's store: the target took damage (lower health) or was destroyed.
			const actorAfter = await actor.evaluate((targetId) => {
				const t = window
					.__creature!.cardsInZone("ATTACKING", "opp")
					.find((card) => card.instance_id === targetId);
				return t ? (t.current_health ?? t.health ?? null) : null;
			}, targetId);
			expect(
				actorAfter === null || actorAfter < beforeHealth!,
				"actor sees target damaged or destroyed",
			).toBeTruthy();

			// Round-trip: the target's OWNER (observer) sees the same drop on its snapshot (broadcast).
			await observer.evaluate(
				({ targetId, beforeHealth }) =>
					window.__creature!.waitForState((s) => {
						const t = s
							.getMyCardsInZone("ATTACKING")
							.find((card) => card.instance_id === targetId);
						return (
							t === undefined ||
							(t.current_health ?? t.health ?? 0) < beforeHealth!
						);
					}),
				{ targetId, beforeHealth },
			);
			const observerAfter = await observer.evaluate((targetId) => {
				const t = window
					.__creature!.cardsInZone("ATTACKING", "my")
					.find((card) => card.instance_id === targetId);
				return t ? (t.current_health ?? t.health ?? null) : null;
			}, targetId);
			expect(
				observerAfter === null || observerAfter < beforeHealth!,
				"target owner sees its card damaged or destroyed",
			).toBeTruthy();
		} finally {
			await close();
		}
	});
});
