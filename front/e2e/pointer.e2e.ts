import { expect, test } from "@playwright/test";

import { SCENE_TIMEOUT, startTwoPlayerGame } from "./game-setup";
import { waitForGameReady } from "./harness";

/**
 * Flow G — real-pointer fidelity smoke (@nongating).
 *
 * Every other gameplay spec drives via `window.__creature` → `ActionBuilder.execute`,
 * proving the action→WS→store wiring but SKIPPING the `scene.pick → InteractionManager`
 * chain that turns a real click into that same call. This spec closes the gap with ONE
 * genuine pointer interaction: it projects a seeded hand card's mesh to page coords
 * (`screenPositionOf`), `page.mouse.click`s it, and asserts the same play_card →
 * SUPPORTING outcome as Step 5. Hand cards fan and overlap, so rather than predict the
 * hit we ask the renderer (`cardAtScreenPoint`) which playable card the click resolves
 * to, then assert THAT card moves (polling absorbs the post-deal fan-in). Kept to one
 * interaction: projection is the brittle layer; the drive API carries action breadth.
 * Non-gating: shares the flaky two-browser/WebGL path.
 */

test.describe("@nongating gameplay: real-pointer play_card → SUPPORTING", () => {
	test("clicking a hand card's projected mesh plays it through scene.pick → InteractionManager", async ({
		browser,
	}) => {
		test.setTimeout(SCENE_TIMEOUT * 2 + 60_000);

		const { hostPage, guestPage, close } = await startTwoPlayerGame(browser);

		try {
			await waitForGameReady(hostPage);
			await waitForGameReady(guestPage);

			// The seeded first player is the actor; the other client only observes.
			const hostIsActive = await hostPage.evaluate(() =>
				window.__creature!.isMyTurn(),
			);
			const actor = hostIsActive ? hostPage : guestPage;
			const observer = hostIsActive ? guestPage : hostPage;

			expect(await actor.evaluate(() => window.__creature!.phase())).toBe(
				"PLACEMENT",
			);

			const handBefore = await actor.evaluate(() =>
				window.__creature!.cardsInZone("HAND").map((c) => c.instance_id),
			);

			// Fan-in-race-proof real click: re-project + re-pick + click + short outcome-wait per
			// retry, so a click that misses the still-animating mesh re-projects and clicks again.
			const clicked: string[] = [];
			let landed: string | null = null;
			await expect(async () => {
				landed = await actor.evaluate((ids) => {
					const supporting = new Set(
						window
							.__creature!.cardsInZone("SUPPORTING")
							.map((c) => c.instance_id),
					);
					return ids.find((id) => supporting.has(id)) ?? null;
				}, clicked);
				if (landed) return;

				// Pick a playable card whose projected centre resolves back to itself, so the click point is unambiguous while cards overlap mid-fan.
				const candidate = await actor.evaluate(() => {
					const c = window.__creature!;
					const playable = new Set(
						c
							.validActions()
							.filter((a) => a.action === "play_card" && a.instance_ids)
							.map((a) => a.instance_ids![0]),
					);
					for (const id of playable) {
						const p = c.screenPositionOf(id);
						if (c.cardAtScreenPoint(p.x, p.y) === id) {
							return { instanceId: id, x: p.x, y: p.y };
						}
					}
					return null;
				});
				expect(
					candidate,
					"a playable hand card should project to a self-pickable point",
				).not.toBeNull();

				await actor.mouse.click(candidate!.x, candidate!.y);
				clicked.push(candidate!.instanceId);

				// `.then(…, …)` turns the wait's timeout into a re-project retry, not a throw.
				landed = await actor.evaluate(
					(id) =>
						window
							.__creature!.waitForState(
								(s) =>
									s
										.getMyCardsInZone("SUPPORTING")
										.some((c) => c.instance_id === id),
								5_000,
							)
							.then(
								() => id,
								() => null,
							),
					candidate!.instanceId,
				);
				expect(landed, "clicked card should reach SUPPORTING").not.toBeNull();
			}).toPass({ timeout: 45_000, intervals: [250] });

			const targetId = landed!;
			expect(handBefore).toContain(targetId);

			// Same outcome as Step 5: HAND → SUPPORTING on the actor's store.
			const actorSupporting = await actor.evaluate(() =>
				window.__creature!.cardsInZone("SUPPORTING").map((c) => c.instance_id),
			);
			expect(
				actorSupporting,
				"clicked hand card should now be in the actor's SUPPORTING zone",
			).toContain(targetId);
			const actorHandAfter = await actor.evaluate(() =>
				window.__creature!.cardsInZone("HAND").map((c) => c.instance_id),
			);
			expect(actorHandAfter).not.toContain(targetId);

			// Round-trip sanity: the observer sees it in its OPPONENT's SUPPORTING.
			await observer.evaluate(
				(id) =>
					window.__creature!.waitForState((s) =>
						s
							.getOpponentCardsInZone("SUPPORTING")
							.some((c) => c.instance_id === id),
					),
				targetId,
			);
			const observerView = await observer.evaluate(() =>
				window
					.__creature!.cardsInZone("SUPPORTING", "opp")
					.map((c) => c.instance_id),
			);
			expect(observerView).toContain(targetId);
		} finally {
			await close();
		}
	});
});
