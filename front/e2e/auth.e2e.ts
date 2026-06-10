import { expect, test } from "@playwright/test";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

/**
 * Flow A — auth smoke (@gating). Plan §5.5 A:
 * docs/exec-plans/active/e2e-verification-harness.md
 *
 * Real UI login with a seeded player → home → the game lobby surfaces that
 * player's seeded 22-card deck as valid and selectable. This is the cheap,
 * stable path that GATES the merge (plan D3). It needs the full stack up
 * (Playwright's webServer starts the backend + preview) and the global-setup
 * seed at e2e/.auth/seed.json (two players, each with a valid 22-card deck).
 *
 * This subsumes (and retires) the Step 1 smoke test: filling and submitting the
 * login form here covers "the login page renders its form".
 */

const AUTH_DIR = path.join(
	path.dirname(fileURLToPath(import.meta.url)),
	".auth",
);

interface SeedPlayer {
	username: string;
	password: string;
	deckId: number;
}

interface Seed {
	runId: string;
	host: SeedPlayer;
	guest: SeedPlayer;
}

// seed.json is written by global-setup *before* tests run, so read it in
// beforeAll (run time), not at module load (collection time, when the file may
// not exist yet — e.g. a clean CI checkout).
let host: SeedPlayer;

test.beforeAll(() => {
	const seed = JSON.parse(
		fs.readFileSync(path.join(AUTH_DIR, "seed.json"), "utf-8"),
	) as Seed;
	host = seed.host;
});

test.describe("auth smoke", { tag: "@gating" }, () => {
	test("login → home → lobby surfaces the seeded valid deck", async ({
		page,
	}) => {
		// A fresh context carries no auth cookie, so the server guard
		// (hooks.server.ts) bounces "/" to /login.
		await page.goto("/");
		await expect(page).toHaveURL(/\/login$/);

		// Real UI login with the seeded host credentials, queried by label.
		await page.getByLabel("Username").fill(host.username);
		await page.getByLabel("Password").fill(host.password);
		// The Sign-In button's accessible name is the slug "sign-in" (the shared
		// Button component runs its text through formatHandle for the aria-label),
		// so match the slug, not "Sign In" (plan §9).
		await page.getByRole("button", { name: /sign-?in/i }).click();

		// The guard now lets us through to home.
		await expect(page).toHaveURL(/localhost:4173\/$/);

		// The lobby renders and the seeded deck is present and selectable.
		await page.goto("/game");
		await expect(
			page.getByRole("heading", { name: "Game Lobby" }),
		).toBeVisible();

		// global-setup names the host deck "E2E Deck (host)". A valid deck renders
		// an enabled button; selecting it reveals the room step, which proves it
		// is genuinely selectable. LobbySelector keeps deck buttons disabled until
		// hydration attaches onclick, so enabled ⇔ clickable — one click suffices.
		// Generous timeout: hydration competes with attack.e2e's teardown CPU
		// load in full-suite runs.
		const deck = page.getByRole("button", { name: /E2E Deck \(host\)/ });
		await expect(deck).toBeVisible();
		await expect(deck).toBeEnabled({ timeout: 15_000 });
		await deck.click();
		await expect(
			page.getByRole("heading", { name: "Select or Create a Room" }),
		).toBeVisible();
	});

	// Regression guard for the in-suite deck-click flake: deck buttons are
	// server-rendered, so they paint before hydration attaches their onclick —
	// a click in that window used to be a silent no-op (LobbySelector now keeps
	// them disabled until hydrated). Stalling the JS module chunks holds the
	// page in exactly that painted-but-unhydrated window, deterministically.
	test("deck buttons stay disabled until hydration attaches their handlers", async ({
		browser,
	}) => {
		const context = await browser.newContext({
			storageState: path.join(AUTH_DIR, "host.json"),
		});
		const page = await context.newPage();
		await page.route("**/_app/immutable/**/*.js", async (route) => {
			await new Promise((r) => setTimeout(r, 4_000));
			await route.continue();
		});
		await page.goto("/game", { waitUntil: "commit" });

		const deck = page.getByRole("button", { name: /E2E Deck \(host\)/ });
		await expect(deck).toBeVisible({ timeout: 15_000 });
		await expect(deck).toBeDisabled();
		await expect(deck).toBeEnabled({ timeout: 30_000 });
		await deck.click();
		await expect(
			page.getByRole("heading", { name: "Select or Create a Room" }),
		).toBeVisible();
		await context.close();
	});

	test("invalid credentials surface an inline alert", async ({ page }) => {
		await page.goto("/login");
		await page.getByLabel("Username").fill("e2e_no_such_user");
		await page.getByLabel("Password").fill("definitely-wrong");
		await page.getByRole("button", { name: /sign-?in/i }).click();

		// role="alert" was wired onto .error-message in Step 2; the failed login
		// leaves us on /login (loginApi throws — /auth/token is excluded from the
		// 401 redirect interceptor).
		await expect(page.getByRole("alert")).toBeVisible();
		await expect(page).toHaveURL(/\/login$/);
	});
});
