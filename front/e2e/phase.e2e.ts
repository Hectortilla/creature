import { expect, test } from "@playwright/test";

import { SCENE_TIMEOUT, startTwoPlayerGame } from "./game-setup";
import { waitForGameReady } from "./harness";

/**
 * Gameplay flow: `pass` drives the phase/turn state machine (@nongating).
 *
 * Like gameplay.e2e.ts, this proves WIRING, not rules: a `pass` round-trips the
 * WebSocket and the phase/turn transition reaches BOTH clients' caches, via the
 * build-gated `window.__creature` API. Deterministic (GAME_SEED-stable) assertions:
 * the seeded first player starts in PLACEMENT; passing only moves FORWARD through
 * the canonical phase order (turn one auto-skips phases whose preconditions aren't
 * met); then the turn flips to the opponent, who begins in PLACEMENT — observed on
 * the OTHER client (the cross-client turnChanged + phaseChanged round-trip). A
 * richer multi-phase sequence needs multi-turn setup — that's Step 6b. Non-gating:
 * shares the flaky two-browser/WebGL path.
 */

/** Canonical forward phase order within a turn (back/app/models/game/enums.py). */
const PHASE_ORDER = [
	"DRAW",
	"PLACEMENT",
	"PROMOTION",
	"SWAP",
	"ASSOCIATION",
	"EVOLUTION",
	"ATTACK",
];

test.describe("@nongating gameplay: pass advances the phase/turn machine", () => {
	test("passing moves the turn forward and hands PLACEMENT to the opponent for both clients", async ({
		browser,
	}) => {
		// One full two-browser game start (two software-WebGL scene loads) + passes.
		test.setTimeout(SCENE_TIMEOUT * 2 + 60_000);

		const { hostPage, guestPage, close } = await startTwoPlayerGame(browser);

		try {
			await waitForGameReady(hostPage);
			await waitForGameReady(guestPage);

			// Seeded first player = whoever's turn it is; the other client observes the flip.
			const hostIsActive = await hostPage.evaluate(() =>
				window.__creature!.isMyTurn(),
			);
			const actor = hostIsActive ? hostPage : guestPage;
			const observer = hostIsActive ? guestPage : hostPage;

			// Seeded first player starts in PLACEMENT; the observer agrees it's not their turn.
			expect(await actor.evaluate(() => window.__creature!.phase())).toBe(
				"PLACEMENT",
			);
			expect(await observer.evaluate(() => window.__creature!.isMyTurn())).toBe(
				false,
			);

			// Pass repeatedly until the turn flips, recording each phase occupied. Each
			// pass awaits a real state change (no sleeps); the loop is bounded to fail fast.
			const phasesSeen: string[] = await actor.evaluate(async (order) => {
				const c = window.__creature!;
				const seen: string[] = [];
				for (let i = 0; i < order.length + 2 && c.isMyTurn(); i++) {
					const before = c.phase();
					if (before) seen.push(before);
					c.pass();
					await c.waitForState(() => !c.isMyTurn() || c.phase() !== before);
				}
				return seen;
			}, PHASE_ORDER);

			// Sanity: started where expected, and every visited phase is real.
			expect(phasesSeen[0]).toBe("PLACEMENT");
			for (const p of phasesSeen) expect(PHASE_ORDER).toContain(p);

			// Forward-only: the phase index never decreases (passing never loops back).
			const indices = phasesSeen.map((p) => PHASE_ORDER.indexOf(p));
			expect(indices).toEqual([...indices].sort((a, b) => a - b));

			// The actor's turn has ended.
			expect(await actor.evaluate(() => window.__creature!.isMyTurn())).toBe(
				false,
			);

			// Cross-client round-trip: the observer now sees it's THEIR turn, in PLACEMENT
			// (after the auto-DRAW) — proving turnChanged + phaseChanged crossed the WebSocket.
			await observer.evaluate(() =>
				window.__creature!.waitForState(() => window.__creature!.isMyTurn()),
			);
			expect(await observer.evaluate(() => window.__creature!.isMyTurn())).toBe(
				true,
			);
			expect(await observer.evaluate(() => window.__creature!.phase())).toBe(
				"PLACEMENT",
			);
		} finally {
			await close();
		}
	});
});
