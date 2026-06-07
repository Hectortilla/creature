import path from "path";
import { fileURLToPath } from "url";
import { expect, test, type Page } from "@playwright/test";

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
 * Non-gating (D3): the WebGL/two-browser path is the flakier one, so it settles
 * before it can block unrelated PRs. Generous timeouts absorb the swiftshader
 * scene-load cost; retries + trace are enabled in CI (playwright.config.ts).
 */

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const AUTH_DIR = path.join(__dirname, ".auth");

const BOARD_READY = '[data-testid="game-board"][data-scene-ready="true"]';

// Scene init (Babylon + Havok WASM under software WebGL) is the slow part; give
// each board-ready wait plenty of room.
const SCENE_TIMEOUT = 120_000;

/** Pick the seeded deck and wait for the room section to appear. */
async function selectDeck(page: Page, role: "host" | "guest"): Promise<void> {
	const deck = page.getByRole("button", {
		name: new RegExp(`E2E Deck \\(${role}\\)`),
	});
	await expect(deck).toBeEnabled();
	await deck.click();
	await expect(
		page.getByRole("heading", { name: "Select or Create a Room" }),
	).toBeVisible();
}

/** Wait for the in-game view + a ready, non-zero-size board. */
async function assertBoardReady(page: Page): Promise<void> {
	await expect(page.getByRole("heading", { name: "Playing" })).toBeVisible({
		timeout: SCENE_TIMEOUT,
	});
	const board = page.locator(BOARD_READY);
	await expect(board).toBeVisible({ timeout: SCENE_TIMEOUT });

	const canvas = page.getByTestId("game-board-canvas");
	const box = await canvas.boundingBox();
	expect(box, "canvas should have a bounding box").not.toBeNull();
	expect(box!.width).toBeGreaterThan(0);
	expect(box!.height).toBeGreaterThan(0);
}

test.describe("@nongating game start + board render", () => {
	test("host creates a room, guest joins, both boards render", async ({
		browser,
	}) => {
		// One full two-browser game start incl. two software-WebGL scene loads.
		test.setTimeout(SCENE_TIMEOUT * 2 + 60_000);

		const hostContext = await browser.newContext({
			storageState: path.join(AUTH_DIR, "host.json"),
		});
		const guestContext = await browser.newContext({
			storageState: path.join(AUTH_DIR, "guest.json"),
		});
		const hostPage = await hostContext.newPage();
		const guestPage = await guestContext.newPage();

		try {
			// --- host: create a room and play -------------------------------------
			await hostPage.goto("/game");
			await selectDeck(hostPage, "host");
			await hostPage.getByRole("button", { name: /Create New Room/ }).click();
			await hostPage
				.getByRole("button", { name: /Create Room & Play/ })
				.click();
			// Wait until the host board is ready — the room-creating WebSocket only
			// opens once the scene has loaded, so this also guarantees the room is
			// discoverable before the guest starts polling for it.
			await assertBoardReady(hostPage);

			// --- guest: find the host's room and join ------------------------------
			await guestPage.goto("/game");
			await selectDeck(guestPage, "guest");
			// "Join Existing Room" is selected by default; click it to be explicit.
			await guestPage
				.getByRole("button", { name: /Join Existing Room/ })
				.click();

			// Refresh the room list until the host's joinable room shows up, then
			// select it (room discovery through the real UI list — D1 fidelity).
			const joinableRoom = guestPage
				.getByRole("button", { name: /Can Join/ })
				.first();
			await expect(async () => {
				await guestPage.getByRole("button", { name: /Refresh/ }).click();
				await expect(joinableRoom).toBeVisible({ timeout: 3_000 });
			}).toPass({ timeout: 60_000 });
			await joinableRoom.click();

			await guestPage.getByRole("button", { name: /Join Room & Play/ }).click();
			await assertBoardReady(guestPage);

			// Host stays in-game once the second player joins and the game starts.
			await assertBoardReady(hostPage);
		} finally {
			await hostContext.close();
			await guestContext.close();
		}
	});
});
