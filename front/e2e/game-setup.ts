import path from "path";
import { fileURLToPath } from "url";
import {
	expect,
	type Browser,
	type BrowserContext,
	type Page,
} from "@playwright/test";

/**
 * Shared two-browser game-start helpers, extracted from game.e2e.ts so the
 * gameplay specs (Steps 5–7) reuse the exact host/guest setup instead of
 * duplicating it. Host creates a room; guest joins via the real room-list UI
 * (which auto-starts at ≥2 players); both reach the in-game board, ready via
 * [data-testid="game-board"][data-scene-ready="true"].
 */

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const AUTH_DIR = path.join(__dirname, ".auth");

const BOARD_READY = '[data-testid="game-board"][data-scene-ready="true"]';

/** Scene init (Babylon + Havok WASM under software WebGL) is slow — give board-ready waits room. */
export const SCENE_TIMEOUT = 120_000;

/** Pick the seeded deck and wait for the room section to appear. */
export async function selectDeck(
	page: Page,
	role: "host" | "guest",
): Promise<void> {
	const deck = page.getByRole("button", {
		name: new RegExp(`E2E Deck \\(${role}\\)`),
	});
	await expect(deck).toBeEnabled();
	// Deck buttons are server-rendered, so a click can land before hydration
	// attaches their onclick — a silent no-op (see auth.e2e.ts). Selecting is
	// idempotent, so retry the click + assertion together.
	await expect(async () => {
		await deck.click();
		await expect(
			page.getByRole("heading", { name: "Select or Create a Room" }),
		).toBeVisible({ timeout: 2_000 });
	}).toPass({ timeout: 15_000 });
}

/** Wait for the in-game view + a ready, non-zero-size board. */
export async function assertBoardReady(page: Page): Promise<void> {
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

/** A started two-player game: both pages in-game with a ready board. */
export interface TwoPlayerGame {
	hostContext: BrowserContext;
	guestContext: BrowserContext;
	hostPage: Page;
	guestPage: Page;
	/** Close both contexts (call from a `finally`). */
	close: () => Promise<void>;
}

/**
 * Drive host create-room → guest join-room through the real UI until both boards
 * are ready; hand back both pages (caller owns teardown via `close()`).
 */
export async function startTwoPlayerGame(
	browser: Browser,
): Promise<TwoPlayerGame> {
	const hostContext = await browser.newContext({
		storageState: path.join(AUTH_DIR, "host.json"),
	});
	const guestContext = await browser.newContext({
		storageState: path.join(AUTH_DIR, "guest.json"),
	});
	const hostPage = await hostContext.newPage();
	const guestPage = await guestContext.newPage();

	const close = async (): Promise<void> => {
		await hostContext.close();
		await guestContext.close();
	};

	try {
		// host: create a room
		await hostPage.goto("/game");
		await selectDeck(hostPage, "host");
		await hostPage.getByRole("button", { name: /Create New Room/ }).click();
		await hostPage.getByRole("button", { name: /Create Room & Play/ }).click();
		// Host board ready also guarantees the room is discoverable: the room-creating
		// WebSocket only opens once the scene has loaded.
		await assertBoardReady(hostPage);

		// guest: find and join the host's room
		await guestPage.goto("/game");
		await selectDeck(guestPage, "guest");
		// "Join Existing Room" is selected by default; click it to be explicit.
		await guestPage.getByRole("button", { name: /Join Existing Room/ }).click();

		// Refresh until the host's joinable room appears, then select it (real UI discovery).
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
	} catch (err) {
		await close();
		throw err;
	}

	return { hostContext, guestContext, hostPage, guestPage, close };
}
