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

interface ClickableCard {
	instanceId: string;
	x: number;
	y: number;
}

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

			// Find a playable hand card whose projected centre scene.pick resolves back to a
			// (still) playable card. Polling/toPass absorbs the post-deal fan-in animation.
			let clickable: ClickableCard | null = null;
			await expect(async () => {
				clickable = await actor.evaluate(() => {
					const c = window.__creature!;
					const playable = new Set(
						c
							.validActions()
							.filter((a) => a.action === "play_card" && a.instance_ids)
							.map((a) => a.instance_ids![0]),
					);
					for (const id of playable) {
						const p = c.screenPositionOf(id);
						const picked = c.cardAtScreenPoint(p.x, p.y);
						if (picked && playable.has(picked)) {
							return { instanceId: picked, x: p.x, y: p.y };
						}
					}
					return null;
				});
				expect(
					clickable,
					"a playable hand card should project to a pickable on-screen point",
				).not.toBeNull();
			}).toPass({ timeout: 20_000, intervals: [500] });

			const target = clickable!;

			// Precondition: the resolved card starts in HAND, not yet SUPPORTING.
			const handBefore = await actor.evaluate(() =>
				window.__creature!.cardsInZone("HAND").map((c) => c.instance_id),
			);
			expect(handBefore).toContain(target.instanceId);

			// THE real interaction: a genuine canvas click → scene.pick → InteractionManager
			// selects the card → since play_card is instant, dispatches ActionBuilder.execute.
			await actor.mouse.click(target.x, target.y);

			// Same outcome as Step 5: HAND → SUPPORTING on the actor's store.
			await actor.evaluate(
				(id) =>
					window.__creature!.waitForState((s) =>
						s.getMyCardsInZone("SUPPORTING").some((c) => c.instance_id === id),
					),
				target.instanceId,
			);
			const actorSupporting = await actor.evaluate(() =>
				window.__creature!.cardsInZone("SUPPORTING").map((c) => c.instance_id),
			);
			expect(
				actorSupporting,
				"clicked hand card should now be in the actor's SUPPORTING zone",
			).toContain(target.instanceId);
			const actorHandAfter = await actor.evaluate(() =>
				window.__creature!.cardsInZone("HAND").map((c) => c.instance_id),
			);
			expect(actorHandAfter).not.toContain(target.instanceId);

			// Round-trip sanity: the observer sees it in its OPPONENT's SUPPORTING.
			await observer.evaluate(
				(id) =>
					window.__creature!.waitForState((s) =>
						s
							.getOpponentCardsInZone("SUPPORTING")
							.some((c) => c.instance_id === id),
					),
				target.instanceId,
			);
			const observerView = await observer.evaluate(() =>
				window
					.__creature!.cardsInZone("SUPPORTING", "opp")
					.map((c) => c.instance_id),
			);
			expect(observerView).toContain(target.instanceId);
		} finally {
			await close();
		}
	});
});
