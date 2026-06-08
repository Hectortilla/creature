import { expect, test } from "@playwright/test";

/**
 * Step 1 smoke test (plan: docs/exec-plans/active/e2e-verification-harness.md).
 *
 * Proves the harness boots the production build and drives a real browser. We
 * hit `/login` because it is a public route (NO_AUTH_ROUTES) whose load fires
 * no backend call — hooks.server.ts only reads the auth cookie — so this needs
 * no backend running (backend wiring + data seeding land in Step 3).
 */
test("login page renders its form", async ({ page }) => {
	await page.goto("/login");

	// Public route: we should land on /login, not get bounced by the auth guard.
	await expect(page).toHaveURL(/\/login$/);

	await expect(page.getByRole("heading", { name: "Creature" })).toBeVisible();
	await expect(page.getByLabel("Username")).toBeVisible();
	await expect(page.getByLabel("Password")).toBeVisible();
	// NB: the Sign-In button's accessible name is the slug "sign-in" — the shared
	// Button component runs its text through formatHandle() for the aria-label, so
	// it is not "Sign In". Match the slug here; Step 4 may normalise this.
	await expect(page.getByRole("button", { name: /sign-?in/i })).toBeVisible();
});
