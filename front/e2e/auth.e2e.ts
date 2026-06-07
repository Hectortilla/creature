import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { expect, test } from "@playwright/test";

/**
 * Flow A — auth smoke (@gating). Plan §5.5 A.
 *
 * Drives the *real* login UI: unauthenticated root bounces to /login, the
 * seeded `host` signs in, lands on home, and the game lobby surfaces their
 * seeded 22-card deck as valid/selectable. This is the cheap, stable path that
 * gives the harness real back-pressure (D3 split gating).
 *
 * Credentials come from `e2e/.auth/seed.json`, written by global-setup.ts
 * (Step 3) — so the backend must be up and migrations applied (plan §6 prereq).
 */

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const seed = JSON.parse(
	fs.readFileSync(path.join(__dirname, ".auth", "seed.json"), "utf-8"),
) as {
	host: { username: string; password: string; deckId: number };
};

// The host's deck is created as `E2E Deck (host)` (global-setup.ts).
const HOST_DECK_NAME = /E2E Deck \(host\)/;

test.describe("@gating auth smoke", () => {
	test("unauthenticated root redirects to /login", async ({ page }) => {
		// Fresh context has no auth cookie, so hooks.server.ts bounces us.
		await page.goto("/");
		await expect(page).toHaveURL(/\/login$/);

		// Fold in Step 1's smoke assertion: the login form renders.
		await expect(page.getByRole("heading", { name: "Creature" })).toBeVisible();
		await expect(page.getByLabel("Username")).toBeVisible();
		await expect(page.getByLabel("Password")).toBeVisible();
		// The Sign-In button's accessible name is the slug "sign-in" (the shared
		// Button component runs its text through formatHandle for the aria-label).
		await expect(page.getByRole("button", { name: /sign-?in/i })).toBeVisible();
	});

	test("login → home → lobby shows the seeded valid deck", async ({ page }) => {
		await page.goto("/login");

		await page.getByLabel("Username").fill(seed.host.username);
		await page.getByLabel("Password").fill(seed.host.password);
		await page.getByRole("button", { name: /sign-?in/i }).click();

		// Successful login redirects to home (`goto('/')`).
		await expect(page).toHaveURL(/:4173\/$/);

		// Navigate to the lobby; the seeded deck must be present and selectable.
		await page.goto("/game");
		await expect(
			page.getByRole("heading", { name: "Game Lobby" }),
		).toBeVisible();

		const deckButton = page.getByRole("button", { name: HOST_DECK_NAME });
		await expect(deckButton).toBeVisible();
		// Valid decks render enabled (invalid ones get `disabled`); selecting one
		// reveals the room section, proving the deck is genuinely selectable.
		await expect(deckButton).toBeEnabled();
		await deckButton.click();
		await expect(
			page.getByRole("heading", { name: "Select or Create a Room" }),
		).toBeVisible();
	});

	test("bad credentials surface an error alert", async ({ page }) => {
		await page.goto("/login");

		await page.getByLabel("Username").fill(seed.host.username);
		await page.getByLabel("Password").fill("wrong-password");
		await page.getByRole("button", { name: /sign-?in/i }).click();

		await expect(page.getByRole("alert")).toBeVisible();
		// We must not have been let through to home.
		await expect(page).toHaveURL(/\/login$/);
	});
});
