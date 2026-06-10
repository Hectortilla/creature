import { expect, test } from "@playwright/test";

import { SCENE_TIMEOUT, startTwoPlayerGame } from "./game-setup";

/**
 * Flow B — game start + board render (@nongating). Plan §5.5 B.
 *
 * Two real browser contexts driven from the seeded `storageState` (host/guest,
 * written by global-setup.ts): the host creates a room and the guest joins it
 * through the UI room list, which is what auto-starts the game (a room needs
 * ≥2 players — see back/app/models/game/room.py game_ready_to_start). Both
 * contexts must then reach the in-game "Playing" view and the BabylonJS board
 * must report ready via the deterministic
 * [data-testid="game-board"][data-scene-ready="true"] hook (Step 2).
 *
 * The shared host/guest setup lives in game-setup.ts (reused by the gameplay
 * specs, Steps 5–7).
 *
 * Non-gating (D3): the WebGL/two-browser path is the flakier one, so it settles
 * before it can block unrelated PRs. Generous timeouts absorb the swiftshader
 * scene-load cost; retries + trace are enabled in CI (playwright.config.ts).
 */

test.describe("@nongating game start + board render", () => {
	test("host creates a room, guest joins, both boards render", async ({
		browser,
	}) => {
		// One full two-browser game start incl. two software-WebGL scene loads.
		test.setTimeout(SCENE_TIMEOUT * 2 + 60_000);

		const { hostPage, close } = await startTwoPlayerGame(browser);

		try {
			// Optional, non-gating visual baseline of the 3D board (plan §5.5 (5),
			// §5.7). Software-WebGL output varies across GPU/OS, so this is tolerant
			// (maxDiffPixelRatio) and masks the dynamic DOM HUD overlays layered over
			// the canvas. The screenshot is non-gating in CI, so environment drift
			// surfaces as a non-blocking diff rather than a blocked merge — regenerate
			// the baseline with `npm run test:e2e:update-snapshots`.
			await expect(hostPage.getByTestId("game-board-canvas")).toHaveScreenshot(
				"board.png",
				{
					maxDiffPixelRatio: 0.1,
					mask: [
						hostPage.locator(".hovered-card-overlay"),
						hostPage.locator(".element-pools-overlay"),
					],
				},
			);
		} finally {
			await close();
		}
	});
});
