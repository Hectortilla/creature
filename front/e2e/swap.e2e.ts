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
 * Gameplay flow: `swap` exchanges a SUPPORTING and an ATTACKING card (@gating).
 *
 * Like the play_card / pass specs, this proves WIRING, not rules: a `swap` intent
 * round-trips the WebSocket and the zone exchange reaches BOTH clients' caches, via
 * the build-gated `window.__creature` API. `swap` needs a multi-turn board, which
 * the driver (harness.ts) builds deterministically (GAME_SEED): turn 1 the actor
 * places two cards into SUPPORTING and ends the turn; turn 2 it promotes one to
 * ATTACKING, then swaps the still-SUPPORTING card with it. Asserts the two ids have
 * exchanged zones on the actor's store AND the opponent's snapshot (cross-client
 * cardsSwapped round-trip). Gating: promoted after the §2 green streak.
 */

test.describe("@gating gameplay: swap exchanges SUPPORTING ↔ ATTACKING", () => {
	test("actor swaps a promoted card with a supporting one; both clients see the exchange", async ({
		browser,
	}) => {
		// Two software-WebGL scene loads + a multi-turn build-up.
		test.setTimeout(SCENE_TIMEOUT * 2 + 90_000);

		const { hostPage, guestPage, close } = await startTwoPlayerGame(browser);

		try {
			await waitForGameReady(hostPage);
			await waitForGameReady(guestPage);

			// Seeded first player drives the swap; the other observes the exchange.
			const hostIsActive = await hostPage.evaluate(() =>
				window.__creature!.isMyTurn(),
			);
			const actor = hostIsActive ? hostPage : guestPage;
			const observer = hostIsActive ? guestPage : hostPage;

			expect(await actor.evaluate(() => window.__creature!.phase())).toBe(
				"PLACEMENT",
			);

			// turn 1: actor places two cards into SUPPORTING
			const [promoteId, swapId] = await placeIntoSupporting(actor, 2);
			expect(promoteId).toBeTruthy();
			expect(swapId).toBeTruthy();
			expect(promoteId).not.toBe(swapId);

			// End the actor's turn; the opponent passes their whole turn back.
			await passWholeTurn(actor);
			await waitForMyTurn(observer);
			await passWholeTurn(observer);
			await waitForMyTurn(actor);

			// turn 2: both placed cards are now promotable
			// PROMOTION: promote one card to ATTACKING.
			await promoteToAttacking(actor, promoteId);

			// Precondition for the swap: promoteId in ATTACKING, swapId in SUPPORTING.
			expect(
				await actor.evaluate(() =>
					window.__creature!.cardsInZone("ATTACKING").map((c) => c.instance_id),
				),
			).toContain(promoteId);
			expect(
				await actor.evaluate(() =>
					window
						.__creature!.cardsInZone("SUPPORTING")
						.map((c) => c.instance_id),
				),
			).toContain(swapId);

			// SWAP: exchange the SUPPORTING card with the promoted one (real path); await cardsSwapped.
			await passToPhase(actor, "SWAP");
			await actor.evaluate(
				async ({ supportingId, attackingId }) => {
					const c = window.__creature!;
					await c.waitForState(() =>
						c
							.validActions()
							.some(
								(a) =>
									a.action === "swap" &&
									a.supporting_card_id === supportingId &&
									a.attacking_card_id === attackingId,
							),
					);
					c.swap(supportingId, attackingId);
					await c.waitForState(
						(s) =>
							s
								.getMyCardsInZone("ATTACKING")
								.some((card) => card.instance_id === supportingId) &&
							s
								.getMyCardsInZone("SUPPORTING")
								.some((card) => card.instance_id === attackingId),
					);
				},
				{ supportingId: swapId, attackingId: promoteId },
			);

			// Actor's store: the two ids have exchanged zones.
			expect(
				await actor.evaluate(() =>
					window.__creature!.cardsInZone("ATTACKING").map((c) => c.instance_id),
				),
			).toContain(swapId);
			expect(
				await actor.evaluate(() =>
					window
						.__creature!.cardsInZone("SUPPORTING")
						.map((c) => c.instance_id),
				),
			).toContain(promoteId);

			// Round-trip: the observer's OPPONENT snapshot shows the same exchange (cardsSwapped broadcast).
			await observer.evaluate(
				({ supportingId, attackingId }) =>
					window.__creature!.waitForState(
						(s) =>
							s
								.getOpponentCardsInZone("ATTACKING")
								.some((card) => card.instance_id === supportingId) &&
							s
								.getOpponentCardsInZone("SUPPORTING")
								.some((card) => card.instance_id === attackingId),
					),
				{ supportingId: swapId, attackingId: promoteId },
			);
			expect(
				await observer.evaluate(() =>
					window
						.__creature!.cardsInZone("ATTACKING", "opp")
						.map((c) => c.instance_id),
				),
			).toContain(swapId);
			expect(
				await observer.evaluate(() =>
					window
						.__creature!.cardsInZone("SUPPORTING", "opp")
						.map((c) => c.instance_id),
				),
			).toContain(promoteId);
		} finally {
			await close();
		}
	});
});
