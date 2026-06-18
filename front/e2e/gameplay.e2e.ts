import { expect, test, type Page } from "@playwright/test";

import { SCENE_TIMEOUT, startTwoPlayerGame } from "./game-setup";
import { waitForGameReady } from "./harness";

/**
 * Flow C — first gameplay flow: play_card → SUPPORTING (@gating).
 *
 * The first spec to drive ACTUAL gameplay past board-ready. It doesn't re-test
 * game rules (the engine's pytest suites own that) — it proves the *wiring*: an
 * intent builds the right action, round-trips the WebSocket, and the server
 * snapshot reaches BOTH clients' caches, all through the real production path
 * (the build-gated `window.__creature` API, never a side channel). The GAME_SEED
 * deal makes the target stable. Gating: promoted after the §2 green streak.
 */

/**
 * Await the seeded `play_card` the server offers the active player; return its
 * target instance id. `valid_actions` can arrive slightly after the state
 * snapshot, so wait on the store's event bus (no sleeps).
 */
async function awaitPlayableHandCard(page: Page): Promise<string | null> {
	return page.evaluate(async () => {
		const c = window.__creature!;
		await c.waitForState(() =>
			c.validActions().some((a) => a.action === "play_card"),
		);
		const action = c.validActions().find((a) => a.action === "play_card");
		return action?.instance_ids?.[0] ?? null;
	});
}

test.describe("@gating gameplay: play_card → SUPPORTING", () => {
	test("active player plays a hand card; it lands in SUPPORTING for both clients", async ({
		browser,
	}) => {
		// One full two-browser game start (two software-WebGL scene loads) + play.
		test.setTimeout(SCENE_TIMEOUT * 2 + 60_000);

		const { hostPage, guestPage, close } = await startTwoPlayerGame(browser);

		try {
			// Both clients must have the harness AND the opening snapshot applied.
			await waitForGameReady(hostPage);
			await waitForGameReady(guestPage);

			// Seeded first player = whoever's turn it is; the other client observes.
			const hostIsActive = await hostPage.evaluate(() =>
				window.__creature!.isMyTurn(),
			);
			const actor = hostIsActive ? hostPage : guestPage;
			const observer = hostIsActive ? guestPage : hostPage;

			// engine.start_game leaves the first player in PLACEMENT with a drawn hand.
			expect(await actor.evaluate(() => window.__creature!.phase())).toBe(
				"PLACEMENT",
			);

			// Pick a hand card the server offered a play_card for (seeded ⇒ deterministic).
			const instanceId = await awaitPlayableHandCard(actor);
			expect(
				instanceId,
				"active player should have a play_card valid action in PLACEMENT",
			).not.toBeNull();

			// Precondition: the target starts in HAND, not yet SUPPORTING.
			const handBefore = await actor.evaluate(() =>
				window.__creature!.cardsInZone("HAND").map((c) => c.instance_id),
			);
			expect(handBefore).toContain(instanceId);

			// Drive the intent through the REAL path (ActionBuilder → GameConnection).
			await actor.evaluate((id) => {
				window.__creature!.playCard(id);
			}, instanceId!);

			// Actor's store: HAND → SUPPORTING (await the transition, no sleeps).
			await actor.evaluate(
				(id) =>
					window.__creature!.waitForState((s) =>
						s.getMyCardsInZone("SUPPORTING").some((c) => c.instance_id === id),
					),
				instanceId!,
			);
			const actorSupporting = await actor.evaluate(() =>
				window.__creature!.cardsInZone("SUPPORTING").map((c) => c.instance_id),
			);
			expect(actorSupporting).toContain(instanceId);
			const actorHandAfter = await actor.evaluate(() =>
				window.__creature!.cardsInZone("HAND").map((c) => c.instance_id),
			);
			expect(actorHandAfter).not.toContain(instanceId);

			// Round-trip: the observer sees the instance in its OPPONENT's SUPPORTING zone (WS broadcast).
			await observer.evaluate(
				(id) =>
					window.__creature!.waitForState((s) =>
						s
							.getOpponentCardsInZone("SUPPORTING")
							.some((c) => c.instance_id === id),
					),
				instanceId!,
			);
			const observerView = await observer.evaluate(() =>
				window
					.__creature!.cardsInZone("SUPPORTING", "opp")
					.map((c) => c.instance_id),
			);
			expect(observerView).toContain(instanceId);
		} finally {
			await close();
		}
	});
});
