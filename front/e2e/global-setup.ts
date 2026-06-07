import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

/**
 * Playwright global-setup: provision two E2E players, each with a valid
 * 22-card deck, via the public REST API. Writes per-player credentials and
 * Playwright storageState to `e2e/.auth/` so the auth and game smoke flows
 * can use them.
 *
 * Plan: docs/exec-plans/active/e2e-verification-harness.md §5.3
 *
 * Prerequisites (not owned here): Postgres + Redis up, Alembic migrations
 * applied. Locally: `make up` then `cd back && uv run alembic upgrade head`.
 */

const BASE_URL = process.env.PUBLIC_API_URL ?? "http://localhost:8000";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const AUTH_DIR = path.join(__dirname, ".auth");

// Cards seeded by the initial migration: IDs 1–11 and 13–30 (ID 12 is absent —
// gap in the migration data). We pick 22 consecutive available IDs: 1–11, 13–23.
const CARD_IDS = [
	...Array.from({ length: 11 }, (_, i) => i + 1),
	...Array.from({ length: 11 }, (_, i) => i + 13),
];

interface SeedPlayer {
	username: string;
	password: string;
	deckId: number;
}

async function pollUntilReady(url: string, timeoutMs = 30_000): Promise<void> {
	const deadline = Date.now() + timeoutMs;
	while (Date.now() < deadline) {
		try {
			const res = await fetch(url);
			if (res.ok) return;
		} catch {
			// not up yet — keep polling
		}
		await new Promise((r) => setTimeout(r, 500));
	}
	throw new Error(`Backend not reachable at ${url} after ${timeoutMs}ms`);
}

async function registerUser(username: string, password: string): Promise<void> {
	const res = await fetch(`${BASE_URL}/auth/register`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ username, password }),
	});
	if (!res.ok) {
		const body = await res.text();
		throw new Error(`register ${username} failed ${res.status}: ${body}`);
	}
}

async function getToken(username: string, password: string): Promise<string> {
	const res = await fetch(`${BASE_URL}/auth/token`, {
		method: "POST",
		headers: { "Content-Type": "application/x-www-form-urlencoded" },
		body: new URLSearchParams({ username, password }),
	});
	if (!res.ok) {
		const body = await res.text();
		throw new Error(`token ${username} failed ${res.status}: ${body}`);
	}
	const data = (await res.json()) as { access_token: string };
	return data.access_token;
}

async function createDeck(token: string, name: string): Promise<number> {
	const res = await fetch(`${BASE_URL}/decks`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${token}`,
		},
		body: JSON.stringify({ name }),
	});
	if (!res.ok) {
		const body = await res.text();
		throw new Error(`createDeck failed ${res.status}: ${body}`);
	}
	const data = (await res.json()) as { id: number };
	return data.id;
}

async function addCard(
	token: string,
	deckId: number,
	cardId: number,
): Promise<void> {
	const res = await fetch(`${BASE_URL}/decks/${deckId}/cards/${cardId}`, {
		method: "POST",
		headers: { Authorization: `Bearer ${token}` },
	});
	if (!res.ok) {
		const body = await res.text();
		throw new Error(
			`addCard deck=${deckId} card=${cardId} failed ${res.status}: ${body}`,
		);
	}
}

async function assertDeckValid(token: string, deckId: number): Promise<void> {
	const res = await fetch(`${BASE_URL}/decks/${deckId}`, {
		headers: { Authorization: `Bearer ${token}` },
	});
	if (!res.ok) {
		throw new Error(`getDeck ${deckId} failed ${res.status}`);
	}
	const data = (await res.json()) as { is_valid_for_playing: boolean };
	if (!data.is_valid_for_playing) {
		throw new Error(`Deck ${deckId} is not valid for playing after seeding`);
	}
}

async function seedPlayer(
	role: "host" | "guest",
	runId: string,
): Promise<SeedPlayer> {
	const username = `e2e_${role}_${runId}`;
	const password = `e2e_pw_${runId}`;

	console.log(`  [global-setup] seeding ${role}: ${username}`);

	await registerUser(username, password);
	const token = await getToken(username, password);
	const deckId = await createDeck(token, `E2E Deck (${role})`);

	for (const cardId of CARD_IDS) {
		await addCard(token, deckId, cardId);
	}
	await assertDeckValid(token, deckId);

	// Persist a Playwright storageState so flows can skip the UI login.
	// Auth state: localStorage["auth_token"] + localStorage["auth_user"] +
	// a session cookie "auth_token" (see front/src/lib/stores/auth.svelte.ts).
	const meRes = await fetch(`${BASE_URL}/auth/me`, {
		headers: { Authorization: `Bearer ${token}` },
	});
	const userJson = await meRes.text();

	const storageState = {
		cookies: [
			{
				name: "auth_token",
				value: token,
				domain: "localhost",
				path: "/",
				expires: Math.floor(Date.now() / 1000) + 7 * 24 * 3600,
				httpOnly: false,
				secure: false,
				sameSite: "Lax" as const,
			},
		],
		origins: [
			{
				origin: "http://localhost:4173",
				localStorage: [
					{ name: "auth_token", value: token },
					{ name: "auth_user", value: userJson },
				],
			},
		],
	};

	fs.writeFileSync(
		path.join(AUTH_DIR, `${role}.json`),
		JSON.stringify(storageState, null, 2),
	);

	return { username, password, deckId };
}

export default async function globalSetup(): Promise<void> {
	console.log("[global-setup] waiting for backend…");
	await pollUntilReady(`${BASE_URL}/`);
	console.log("[global-setup] backend ready — seeding test data");

	fs.mkdirSync(AUTH_DIR, { recursive: true });

	const runId = Date.now().toString(36);
	const host = await seedPlayer("host", runId);
	const guest = await seedPlayer("guest", runId);

	const seed = { runId, host, guest };
	fs.writeFileSync(
		path.join(AUTH_DIR, "seed.json"),
		JSON.stringify(seed, null, 2),
	);

	console.log(
		`[global-setup] done — host=${host.username} guest=${guest.username} deck=${host.deckId}/${guest.deckId}`,
	);
}
