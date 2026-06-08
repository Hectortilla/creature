import { execFileSync } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

import { E2E_DATABASE_URL, E2E_REDIS_URL } from "./config";

/**
 * Lifecycle for the disposable E2E database + Redis logical DB (plan §5.8 /
 * Step 3.5). The whole point: E2E runs against a throwaway `creature_e2e`,
 * freshly migrated and seeded each run, and NEVER touches the dev `creature` DB.
 *
 * Resetting at *setup* (not just teardown) is the real guarantee — a crashed run
 * still leaves the next run a clean slate (D6). Teardown is best-effort only.
 *
 * Shells out to `psql` (drop/create the DB), `uv run alembic` (migrate +
 * reseed the reference cards), and `redis-cli` (flush). All three are present
 * both locally (Homebrew) and on GitHub's Ubuntu runners (Step 7 CI).
 */

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BACK_DIR = path.resolve(__dirname, "../../back");

/** Parsed once: the disposable DB's name and a maintenance URL (the `postgres`
 *  DB) from which we can DROP/CREATE it. */
function parseDbUrl(): { dbName: string; maintenanceUrl: string } {
	const url = new URL(E2E_DATABASE_URL);
	const dbName = url.pathname.replace(/^\//, "");
	url.pathname = "/postgres";
	return { dbName, maintenanceUrl: url.toString() };
}

/**
 * Refuse to operate on anything that isn't an obviously-disposable DB. This is
 * the last line of defence in front of `DROP DATABASE` — if the target name
 * doesn't end in `_e2e`, we abort loudly rather than risk a real database.
 */
function assertDisposableDb(dbName: string): void {
	if (!/_e2e$/.test(dbName)) {
		throw new Error(
			`Refusing to reset/drop database "${dbName}": E2E only operates on ` +
				`names ending in "_e2e" (got E2E_DATABASE_URL=${E2E_DATABASE_URL}). ` +
				`This guard exists so the harness can never touch the dev DB.`,
		);
	}
}

function psql(maintenanceUrl: string, statements: string[]): void {
	const args = [maintenanceUrl, "-v", "ON_ERROR_STOP=1"];
	for (const sql of statements) args.push("-c", sql);
	execFileSync("psql", args, { stdio: "inherit" });
}

/** Drop + recreate the disposable DB from scratch (run before seeding). */
export function resetDatabase(): void {
	const { dbName, maintenanceUrl } = parseDbUrl();
	assertDisposableDb(dbName);
	console.log(`[e2e:db] resetting disposable database "${dbName}"`);
	psql(maintenanceUrl, [
		// Kick off any lingering connections so DROP can proceed cleanly.
		`SELECT pg_terminate_backend(pid) FROM pg_stat_activity ` +
			`WHERE datname = '${dbName}' AND pid <> pg_backend_pid();`,
		`DROP DATABASE IF EXISTS ${dbName};`,
		`CREATE DATABASE ${dbName};`,
	]);
}

/** `alembic upgrade head` against the fresh DB — builds the schema and reseeds
 *  the reference cards (IDs the deck-builder needs). */
export function migrateDatabase(): void {
	console.log("[e2e:db] alembic upgrade head");
	execFileSync("uv", ["run", "alembic", "upgrade", "head"], {
		cwd: BACK_DIR,
		env: { ...process.env, DATABASE_URL: E2E_DATABASE_URL },
		stdio: "inherit",
	});
}

/** Flush the e2e Redis logical DB so room/session state can't leak between runs.
 *  Best-effort: the gating auth flow doesn't use Redis, so a missing `redis-cli`
 *  must not break the suite. */
export function flushRedis(): void {
	try {
		execFileSync("redis-cli", ["-u", E2E_REDIS_URL, "FLUSHDB"], {
			stdio: "inherit",
		});
		console.log("[e2e:db] flushed e2e Redis logical DB");
	} catch (err) {
		console.warn(`[e2e:db] redis flush skipped (non-fatal): ${String(err)}`);
	}
}

/** Best-effort teardown: drop the disposable DB. Correctness must NOT depend on
 *  this running — setup-side reset is the real guarantee. */
export function dropDatabase(): void {
	try {
		const { dbName, maintenanceUrl } = parseDbUrl();
		assertDisposableDb(dbName);
		psql(maintenanceUrl, [
			`SELECT pg_terminate_backend(pid) FROM pg_stat_activity ` +
				`WHERE datname = '${dbName}' AND pid <> pg_backend_pid();`,
			`DROP DATABASE IF EXISTS ${dbName};`,
		]);
		console.log(`[e2e:db] dropped disposable database "${dbName}"`);
	} catch (err) {
		console.warn(`[e2e:db] teardown drop skipped (non-fatal): ${String(err)}`);
	}
}
