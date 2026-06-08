import { dropDatabase } from "./db";

/**
 * Playwright global-teardown (best-effort): drop the disposable `creature_e2e`
 * database after the suite. Plan §5.8 / Step 3.5.
 *
 * Correctness must NOT depend on this running — the setup-side reset in
 * global-setup.ts is the real isolation guarantee. This just keeps things tidy
 * after a clean run; if it fails (e.g. a connection lingers), the next run's
 * reset drops it anyway.
 */
export default async function globalTeardown(): Promise<void> {
	dropDatabase();
}
