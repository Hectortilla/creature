# Make the backend HTTP/auth/service/websocket layers trustworthy

The pure game engine is heavily fortified (mutation gate, snapshot tests, strict
mypy), but the **trust boundary** — the HTTP routers, the auth/JWT layer, the
service layer, and the websocket message-routing/dispatch logic — is near
zero-tested, and the single global coverage floor (`fail_under = 62`) is
satisfied *entirely by the engine*. An agent can today add an unauthenticated
endpoint, drop an authz check, or mis-route a websocket message and stay green.
This plan builds a real test layer over those boundaries (happy **and**
security/negative paths), makes the coverage floor **honest** with a per-package
CI gate that ratchets, and re-enables strict mypy on `app.services.*` then
`app.websocket.*` — the one item explicitly deferred from
[`harness-overnight-trust`](../completed/harness-overnight-trust.md).

This plan retires two follow-up rungs in
[`docs/harness.md`](../../harness.md#follow-up-rungs-toward-h3): the **Backend
type coverage** rung (drop `ignore_errors` on `services`/`websocket`) and the
implicit "make the coverage floor mean something" gap behind it.

---

## 0. Context & invariants (read first)

**Why this plan exists.** The harness measures the engine and almost nothing
else. The dangerous gap is the *boundary*: code that authenticates users,
enforces per-user data isolation, validates external input, and routes live
websocket frames. These are exactly the surfaces where a regression is a
security incident, not a gameplay bug — and exactly the surfaces with no tests
and no real coverage floor.

**Trust-boundary framing.** Fail-fast (see `.claude/rules/general-style.md`)
applies to *internal, trusted* code. The code this plan tests lives at the
**edges** — API/user input, JWT tokens, cross-user access, malformed websocket
messages. At the edges we validate, and we test that the validation holds. Every
step here must assert at least one **negative/security** path, not just a happy
path.

**Invariants that must stay true after this plan:**
- The engine's existing gates (mutation gate, behaviour snapshots, strict
  `app.game.*` mypy) are untouched and stay green.
- The global `fail_under` floor never *drops*; the new per-package floors are
  **additive** (a separate CI gate) and only ratchet **up**.
- No production code is loosened to make a test pass. Tests adapt to the code's
  real contract (e.g. assert the status code the dependency actually returns —
  do not change production code to match a test's expectation).
- New tests are **warning-clean**: `pytest` runs with `filterwarnings =
  ["error"]` (pyproject.toml), so a deprecation warning from TestClient/Pydantic
  fails the run. Fix the warning at its source; never add a blanket ignore.
- Per-step: the gate named under **Gate** is green before the PR merges (one PR
  per step; the ralph loop does exactly one step per iteration).

### Unit vs. integration — the core tension (resolved correctly)

This is the load-bearing fact the plan is built on; it was verified against the
CI config, not assumed:

- **`make check` runs unit-only, with NO database.** `make check` →
  `test-cov` → `uv run pytest -m "not integration" --cov=app
  --cov-report=term-missing` (back/Makefile). The CI `backend` job that runs
  `make check` provisions **only Redis** (`REDIS_URL` set), **no Postgres and no
  `DATABASE_URL`** (ci.yml). The `db_session`/`session` fixtures **skip** when
  `DATABASE_URL` is unset (conftest.py). **Therefore a DB-backed test cannot
  lift the `make check` `fail_under` floor — it skips in the exact job that
  measures it.** Only genuinely DB-free tests move `fail_under`.
- **Integration tests run in a separate job.** `backend-integration` (ci.yml)
  provisions `postgres:14` + `redis:7`, runs `uv run alembic upgrade head`, then
  `uv run pytest -m integration`. This is the only CI job with a database.
- **Decision — mark by what the test needs, not by where we wish it counted:**
  - **DB-free → `unit`** (lifts `make check`): the pure JWT/password primitives
    (`create_access_token`/`decode_access_token`/`verify_password`), and the
    websocket routing/dispatch tests built on the in-memory
    `FakeRegistry`/`FakeConnections`/`FakeWebSocket` + `asyncio.run()` pattern
    (`tests/unit/test_websocket_cleanup.py`) — **no live Redis**.
  - **Needs Postgres → `integration`** (runs in `backend-integration`): every
    router test (`TestClient(app)` + a `get_db_session` override over the
    rollback `session`), the auth *dependency* HTTP tests (they go through the
    app and the user lookup), and every service test (services take a live
    `Session`).
- **The honest per-package floor is a CI-only gate (Steps 8–9), modelled on the
  mutation gate — not on `make check`.** Because `make check` has no DB, it can
  never see boundary coverage; trying to make it would make `fail_under` behave
  differently locally (DB up vs down) and is fragile. Instead, mirror
  `scripts/mutation_gate.py`: a gate that runs in **one infra-equipped CI job**
  (the `backend-integration` job, which already has Postgres + Redis +
  migrations), runs the **full suite** (`unit` **and** `integration`) once with
  `--cov-report=json`, and scores **per-package** coverage from that single
  comprehensive `cov.json`. No `coverage combine`, no cross-job artifact passing
  (the two-job split is on separate runners and cannot share a `.coverage`
  file). `make check`'s global `fail_under` stays exactly as it is.

### Harness-protected paths (from `.github/workflows/harness-guard.yml`)

Edits to any of these make `harness-guard` **red until a human applies the
`harness-change` label** — that red is the tripwire working, not a bug. Relevant
to this plan (verified against the exact regex list):
- `back/pyproject.toml` — **PROTECTED** (coverage/mypy config).
- `back/Makefile` and the repo-root `Makefile` — **PROTECTED**.
- `.github/workflows/**` — **PROTECTED** (CI wiring).
- New files under **`back/scripts/`** and **`back/coverage-baseline.json`** —
  **NOT protected** (the guard only pins the repo-root `scripts/ralph_loop.py`;
  `back/scripts/*` and `back/coverage-baseline.json` match no pattern). The gate
  *script* and *baseline* are label-free; only **wiring them into CI** needs the
  label.
- New files under `back/tests/unit/` and `back/tests/integration/` and edits to
  `back/tests/conftest.py` — **NOT protected** (only
  `back/tests/behaviour/__snapshots__/*.ambr` is). **Every pure test-adding step
  is label-free.**

---

## 1. Scope

**In scope.**
- (A) Real test layer over: `app/routers/{auth,decks,cards,attacks,crud}.py`,
  `app/auth/{security,dependencies}.py`, `app/services/*`, and the websocket
  routing/dispatch (`app/websocket/{message_router,game_runner,lobby,
  serialization,session}.py`) — happy **and** negative/security paths.
- (B) An honest, ratcheting **per-package coverage gate** (CI-only):
  `back/scripts/coverage_gate.py` + `back/coverage-baseline.json` mirroring
  `scripts/mutation_gate.py` + `mutation-baseline.json`, with real floors for
  `app.routers`, `app.auth`, `app.services`, `app.websocket`, set at post-(A)
  levels, scored from the full-suite `cov.json` in the `backend-integration` job.
- (C) Re-enable strict mypy: drop `ignore_errors` for `app.services.*` (first),
  then `app.websocket.*`, fixing the surfaced type errors.

**Non-goals (see Follow-up).** Activating `claude-review.yml`; negative-path /
cross-browser e2e; the HUD→Svelte migration; touching the engine's gates;
clearing `app.settings.*` mypy.

---

## 2. Decisions (locked)

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | One shared fixtures module (`tests/conftest.py` additions) is built first: a **rollback** DB `session`, a `client` (TestClient + `get_db_session` override, **no** auth override), an `auth_token`/`make_user` helper, and an `auth_client` (happy-path convenience with `get_current_active_user` overridden). | Foundational; unblocks every router/service step. Two client flavours are required (see D3). |
| D2 | DB-backed router/auth-HTTP/service tests are marked **`integration`** — they need real Postgres and run in the `backend-integration` CI job. They do **not** lift the `make check` floor (which has no DB); their coverage is locked by the per-package CI gate (Steps 8–9). | Verified: the `backend` job that runs `make check` has no Postgres/`DATABASE_URL`, so DB tests skip there. Don't pretend otherwise. |
| D3 | Negative-path auth tests use the plain **`client`** (no auth override) so the real `oauth2_scheme` → `get_current_user` chain runs and 403/401/400 are reachable. Cross-user isolation builds a **real per-user token** (`create_access_token({"sub": user.username})`) against `client`. `auth_client` (override to a fixed user) is for happy-path convenience only. | A global `get_current_active_user` override makes every negative auth path unreachable; the override is happy-path sugar, not the auth test vehicle. |
| D4 | Pure tests run as **`unit`** and lift `make check`: JWT/password primitives, and websocket routing/dispatch via the in-memory `FakeRegistry`/`FakeConnections`/`FakeWebSocket` + `asyncio.run()` pattern — **no live Redis**. | JWT is pure; routing is pure logic. Matches `test_websocket_cleanup.py`. |
| D5 | The honest boundary floor is a **CI-only per-package gate** mirroring `mutation_gate.py` (read JSON, compare per-package floors to a baseline file, write a GitHub-summary table, exit non-zero on regression, `+1e-9` tolerance). It runs in the `backend-integration` job over the **full suite** (`unit` + `integration`) and scores one `cov.json`. `make check`'s `fail_under` is untouched. | The DB-free `make check` cannot see boundary coverage; a full-infra CI gate can, consistently — exactly how the mutation gate works. |
| D6 | The coverage gate consumes a **single** `cov.json` from one full-suite run (`uv run pytest --cov=app --cov-report=json:cov.json` in the `backend-integration` job, which already migrates a live DB). **No `coverage combine`, no cross-job artifact** — the gate runs where all the infra already is. | The unit and integration jobs are separate runners with no shared filesystem; combining across them is needless complexity. One infra-equipped job runs everything. |
| D7 | mypy is re-enabled **services first, then websocket**, in two separate steps, each with the matching test layer already in place as a behaviour safety net. | Smaller diffs; websocket types lean on service types; avoids one giant `ignore_errors`-removal PR. |
| D8 | Order: shared fixtures → auth → routers → services → websocket → coverage-gate script → wire-gate-into-CI → mypy services → mypy websocket. The gate lands **after** the test layer so its initial floors sit at honest post-(A) levels. | Foundational/unblocking first; a floor can't be set before the coverage it measures exists. |

---

## 3. How to execute

Drive with `/ralph-iteration backend-api-trust.md`: pick the most important
unblocked step, implement and verify **only** that step, tick its box, commit,
stop. Each step is one PR ending gate-green. Branch naming:
`spec/backend-api-trust/step-N/<slug>`. Integration-marked steps require services
up (`make up`) and `DATABASE_URL`/`REDIS_URL` set locally to run their gate; in
CI they run in the `backend-integration` job. When all steps are done, move this
file to `../completed/`.

**Status legend:** `- [ ]` not started · `- [x] ✅ done` · `🚧 in progress` ·
`⛔ blocked` (note why). Each completing agent fills the **Status** line with the
date, branch, commit, and PR, and leaves a **Notes for next agent** bullet.
Steps touching a harness-protected path are flagged **LABEL REQUIRED** — expect
`harness-guard` red until a human applies `harness-change`; that is the tripwire,
not a failure.

---

## 4. Steps

### Step 1 — Shared test fixtures: rollback DB session + two TestClient flavours
- [x] **Status:** ✅ done — 2026-06-27 — rollback `session` (SAVEPOINT + `after_transaction_end`), un-overridden `client`, `make_user`/`auth_token` helpers, happy-path `auth_client`, and DB-backed smoke tests proving no row leak + real auth chain — branch `spec/backend-api-trust/step-1/shared-fixtures` — PR https://app.graphite.com/github/pr/Hectortilla/creature/25
- **Notes for next agent:**
  - **The real no-auth code on a protected endpoint is `401`, not `403`.** `OAuth2PasswordBearer(auto_error=True)` raises `401 Unauthorized` when the `Authorization` header is missing (verified live against `GET /auth/me`). The plan's Step 2/3 text saying "→ 403" was wrong and has been corrected to 401 — assert 401 for the missing-header case. (A *malformed/expired/wrong-sig* bearer also yields 401 via `get_current_user`'s `credentials_exception`; a *disabled* user yields 400.)
  - The `session` rollback is proven **inline** without depending on teardown order: the fixture's writes live in an uncommitted outer transaction, so a fresh `Session(engine)` (separate connection) never sees them even after an in-request `.commit()` — that's the leak assertion in `test_fixtures.py`.
  - `auth_client` seeds a `happy-path-user` and overrides `get_current_active_user`; `client` clears all `app.dependency_overrides` on teardown, so the override never leaks across tests.
- **Why / failure mode closed:** every later step otherwise reinvents DB setup
  and auth, and leaks rows into real Postgres (today's `db_session` has **no
  rollback** — committed rows persist). One canonical, transactional harness
  makes the whole HTTP/service surface cheaply testable.
- **Do:**
  - In `back/tests/conftest.py` add a **transactional `session`** fixture that
    actually rolls back even though routers call `.commit()`. Use the standard
    SQLAlchemy "join a Session into an external transaction" recipe: open a
    `connection = engine.connect()` (reuse `app.database.engine`), `trans =
    connection.begin()`, bind `Session(bind=connection)`, start a SAVEPOINT with
    `connection.begin_nested()`, and register an `after_transaction_end` event
    listener that restarts the SAVEPOINT whenever the in-request `.commit()` ends
    it; on teardown `trans.rollback()` + close. **Skip unless `DATABASE_URL` is
    set and reachable** (mirror the existing `db_session` guard). Keep the legacy
    `db_session` fixture for existing integration tests.
  - Add a **`client`** fixture: `TestClient(app)` (`app` from `app.main`) with
    `app.dependency_overrides[get_db_session] = lambda: session` (the rollback
    session; `get_db_session` from `app.database`), **no auth override**, cleared
    on teardown. This is the vehicle for negative-path auth tests (the real
    `oauth2_scheme` chain runs) and real-token cross-user tests.
  - Add a **`make_user`** factory (insert a `User` via `get_password_hash` from
    `app.auth.security`) and an **`auth_token(user)`** helper returning an
    `Authorization: Bearer <create_access_token({"sub": user.username})>` header.
  - Add an **`auth_client`** fixture: `client` plus
    `app.dependency_overrides[get_current_active_user]` (from
    `app.auth.dependencies`) set to a known seeded user — **happy-path
    convenience only** (do not use it for 403/401 tests).
  - Confirm the exact dependency/symbol names against `app/auth/dependencies.py`,
    `app/auth/security.py`, and `app/database.py` before wiring overrides.
  - Add smoke tests in `tests/integration/test_fixtures.py` (DB-backed →
    `integration`): a row added via `session` is **not** visible from a fresh
    `Session(engine)` after teardown (rollback proven, including after an
    in-request commit); `auth_client` reaches a protected endpoint; bare `client`
    on a protected endpoint without a header → the real 403/401.
  - **New files / fixtures only — no production code, no config.**
- **Gate:** `cd back && make check` green (no regressions); with services up
  (`make up`, `DATABASE_URL` set) `cd back && uv run pytest -m integration` green
  and the rollback smoke test proves no row leaks.
- **Depends on:** none.
- **Label:** none (test files only).

### Step 2 — Auth-layer tests: pure security primitives (unit) + dependency negatives (integration)
- [x] **Status:** ✅ done — 2026-06-27 — `tests/unit/test_auth_security.py` (6 pure JWT/password tests, lifts `app.auth`) + `tests/integration/test_auth_dependencies.py` (6 HTTP-chain negatives: missing/malformed/expired/wrong-sig → 401, disabled → 400, unknown user → 401) — branch `spec/backend-api-trust/step-2/auth-tests` — PR https://app.graphite.com/github/pr/Hectortilla/creature/26
- **Notes for next agent:**
  - **Local integration run:** `make up` (brew Postgres 14 + Redis already start), then `export DATABASE_URL="postgresql://hectorsoriavillalva@localhost:5432/creature" REDIS_URL="redis://localhost:6379/0"`, `uv run alembic upgrade head`, `uv run pytest -m integration`. The default `database_url` (`postgres:postgres@…`) does NOT auth against local brew Postgres — pass the username-only URL above. All `uv run`/`make` need the sandbox OFF.
  - `decode_access_token` returns `None` (never raises) for expired/malformed/wrong-sig; a token missing `sub` decodes to a dict **without** a `sub` key (the `sub` check lives in `_validate_token`, not `decode_access_token`).
  - Confirmed live: missing header / bad-or-unknown bearer → **401**, disabled user → **400** (the Step 1 note holds).
- **Why / failure mode closed:** an agent weakens JWT validation (accepts
  expired/wrong-signature tokens), drops the `disabled`-user check, or lets a
  valid-signature token for a non-existent user through — and stays green. The
  single highest-leverage security surface.
- **Do:**
  - New `tests/unit/test_auth_security.py` — **`pytestmark = pytest.mark.unit`**,
    pure, no DB (lifts `make check`): round-trip `create_access_token` /
    `decode_access_token`; `verify_password`/`get_password_hash` accept the right
    password and reject the wrong one; **expired** token (negative
    `expires_delta`) is rejected by `decode_access_token`; **malformed**
    (`"not.a.jwt"`) rejected; **wrong-signature** (encode with a different secret,
    decode with the real one) rejected; **missing `sub`** handled. Assert the
    real behaviour of `decode_access_token` (e.g. returns `None` / raises — match
    the code).
  - New `tests/integration/test_auth_dependencies.py` —
    **`pytestmark = pytest.mark.integration`**, uses `client`/`make_user`/
    `auth_token`: protected endpoint **without** `Authorization` → **401** (via
    `oauth2_scheme`, `auto_error=True`; verified in Step 1, not 403);
    **malformed/expired/wrong-sig** bearer → **401**; valid
    token for a **disabled** user → **400**; valid token for a
    **deleted/non-existent** user → **401**. Assert the codes the code actually
    returns (do not change production code).
  - Together these cover `app.auth.security` (unit) and `app.auth.dependencies`
    (via the HTTP path).
- **Gate:** `cd back && make check` green (the pure primitives lift `app.auth`
  coverage in the unit run); with services up, `cd back && uv run pytest -m
  integration` green for the dependency negatives.
- **Depends on:** Step 1.
- **Label:** none (test files only).

### Step 3 — Router tests: `auth.py` + the cross-user authz-isolation pattern
- [x] **Status:** ✅ done — 2026-06-27 — `tests/integration/test_router_auth.py` (9 tests): register happy/dup-username 400/dup-email 400, token good→bearer / bad-pass 401 / unknown 401, `/auth/me` real bearer → caller, no-auth → 401, plus the two-user token-isolation pattern — branch `spec/backend-api-trust/step-3/router-auth` — PR https://app.graphite.com/github/pr/Hectortilla/creature/27
- **Notes for next agent:**
  - **Authz-isolation pattern to reuse in Steps 4–5:** seed users via `make_user`, build a real per-user header with `auth_token(user)`, drive the un-overridden `client`, and assert each token only ever sees its own data. See `test_me_isolates_users_by_token`.
  - **Register error codes are 400, not 403/409:** duplicate username → `400 "Username already registered"`, duplicate email → `400 "Email already registered"` (the router raises `HTTP_400_BAD_REQUEST`). Register success is **201** with a `UserRead` (no `password`/`hashed_password` field).
  - `POST /auth/token` is form-encoded (`data=`, OAuth2PasswordRequestForm), not JSON; bad password and unknown user both → 401.
- **Why / failure mode closed:** registration/login regressions (duplicate
  username/email silently accepted, wrong status codes) and — critically —
  **cross-user data leakage** at the HTTP layer go unnoticed.
- **Do:**
  - New `tests/integration/test_router_auth.py` —
    **`pytestmark = pytest.mark.integration`** (uses `client`, `session`,
    `make_user`, `auth_token`): `POST /auth/register` happy path → its real
    success code + read model; duplicate username and duplicate email → the error
    the router raises; `POST /auth/token` with good creds → `Token`; bad password
    and unknown user → 401; `GET /auth/me` with a real bearer header → the
    current user, and without auth → 401 (verified in Step 1, not 403).
  - Establish the **authz-isolation pattern** reused by Steps 4–5: seed user A
    and user B via `make_user`, build a real token per user via `auth_token`, and
    assert B's token never sees A's data (`/auth/me` returns only the caller).
- **Gate:** `cd back && make check` green (unchanged); with services up,
  `cd back && uv run pytest -m integration` green; `app/routers/auth.py` is
  exercised (verified by the Step 8 gate once it lands).
- **Depends on:** Step 1, Step 2.
- **Label:** none (test files only).

### Step 4 — Router tests: `decks.py` (ownership + add/remove-card edges)
- [x] **Status:** ✅ done — 2026-06-27 — `tests/integration/test_router_decks.py` (11 tests): CRUD happy paths, cross-user 404 on GET/PUT/DELETE + list/summaries scoped to owner, add/remove-card, non-owned-deck 404, missing-card 404, card-not-in-deck 404, deck-full 400 — branch `spec/backend-api-trust/step-4/router-decks` — PR https://app.graphite.com/github/pr/Hectortilla/creature/28
- **Notes for next agent:**
  - **Cross-user deck access returns 404, not 403** — `DeckService` scopes every read by `user_id`, so a non-owned deck reads as "not found"; there is no distinct 403 path. The plan text "404/403" resolves to 404 for decks.
  - **The `cards` table holds pre-seeded reference rows** (e.g. `code=1` exists) that are NOT in the rollback session. Seed test cards with high codes to avoid `cards_code_key` unique-violation — the local `make_card` fixture hands out `9_000_001+`. Reuse this for Step 5's card/attack seeding.
  - **Deck full = 22 cards** (`GameConfiguration().deck_size`); seed `DeckCard` rows directly via `session` then POST one more → 400 "Deck is full".
- **Why / failure mode closed:** `DeckService` is the most authz-sensitive
  surface (user-scoped CRUD + `add_card_to_deck`/`remove_card_from_deck` raising
  `HTTPException`). A dropped owner check lets one user mutate another's decks.
- **Do:**
  - New `tests/integration/test_router_decks.py` —
    **`pytestmark = pytest.mark.integration`** (uses `client`, `session`,
    `make_user`, `auth_token`): create/list/get/update/delete happy paths;
    **cross-user isolation** — B's token doing `GET`/`PUT`/`DELETE` on A's
    `deck_id` → the router's real 404/403, and `GET /decks` for B never returns
    A's decks; `POST /decks/{id}/cards/{card_id}` and the `DELETE` mirror —
    add to a non-owned deck → error; remove a card not in the deck → the
    `HTTPException`; deck-full path if reachable with seeded data.
  - Seed cards/decks through `session` so the rollback fixture cleans them.
- **Gate:** `cd back && make check` green; with services up, `cd back && uv run
  pytest -m integration` green; `app/routers/decks.py` + `app/services/decks.py`
  exercised.
- **Depends on:** Step 1, Step 3.
- **Label:** none (test files only).

### Step 5 — Router tests: `cards.py`, `attacks.py`, and the `crud.py` factory
- [ ] **Status:** not started
- **Why / failure mode closed:** the read/lookup-heavy routers (and the shared
  `create_crud_router` factory powering elements/types/abilities/characters/
  associations) have no tests; a broken lookup, a **missing auth dependency on a
  generated router**, or a create/delete regression ships silently.
- **Do:**
  - New `tests/integration/test_router_cards.py`,
    `tests/integration/test_router_attacks.py`,
    `tests/integration/test_router_crud.py` — each
    **`pytestmark = pytest.mark.integration`** (use `client`, `session`,
    `make_user`, `auth_token`): list, get-by-code/handle/name, the `by-*`
    lookups, create + delete; **unauth → 401** for each (missing header, verified
    in Step 1), and for `crud` exercise
    the **factory** once via one representative instance (e.g. the elements
    router) to prove every generated router enforces auth.
  - Seed reference rows via `session`.
- **Gate:** `cd back && make check` green; with services up, `cd back && uv run
  pytest -m integration` green; `app/routers/{cards,attacks,crud}.py` exercised.
- **Depends on:** Step 1, Step 3.
- **Label:** none (test files only).

### Step 6 — Service-layer tests: `users`, `cards`, `attacks`, `decks`, `base`, `player_state`
- [ ] **Status:** not started
- **Why / failure mode closed:** services hold the real business logic (password
  hashing in `UserService.create`, enrichment in `CardService`/`AttackService`,
  user-scoping + size limits in `DeckService`, deck validation in
  `player_state`). Testing them directly (a) raises `app.services.*` coverage to
  a level worth gating and (b) is the prerequisite for re-enabling mypy (Step 10).
- **Do:**
  - New `tests/integration/test_services_*.py` —
    **`pytestmark = pytest.mark.integration`**, against the **`session`** rollback
    fixture (services take a live `Session`):
    - `UserService`: `create` hashes the password (stored hash ≠ plaintext,
      `verify_password` true); `get_by_*`; `authenticate` true/false; unknown
      user → `None`.
    - `DeckService`: user-scoping; `add_card_to_deck` raises `HTTPException` on
      missing deck/card and when full; `remove_card_from_deck` raises when card
      absent; `get_user_deck` for another user → `None`.
    - `CardService`/`AttackService`: enrichment produces the expected read models
      from seeded rows.
    - `BaseService` via one concrete subclass (e.g. `ElementService`):
      `get_all`/`get`/`create`/`delete`.
    - `player_state`: the pure serialize path (mark a **`unit`** test in
      `tests/unit/` if it needs no DB) and the DB-backed `build_player_state`
      raising on a deck not owned / invalid for play (integration).
- **Gate:** `cd back && make check` green; with services up, `cd back && uv run
  pytest -m integration` green; `app/services/*` materially exercised.
- **Depends on:** Step 1.
- **Label:** none (test files only).

### Step 7 — Websocket routing/dispatch unit tests (in-memory fakes, no Redis)
- [ ] **Status:** not started
- **Why / failure mode closed:** `MessageRouter.handle_message` is the websocket
  trust boundary — it validates client frames and routes to lobby/runner. A
  malformed frame that crashes the loop, an unknown type that isn't rejected, an
  action dispatched for a player not in a room, or opponent card-ids leaking
  unmasked all ship silently today.
- **Do:**
  - New `tests/unit/test_message_router.py` —
    **`pytestmark = pytest.mark.unit`**, reusing the
    `FakeRegistry`/`FakeConnections`/`FakeWebSocket` + `asyncio.run()` pattern
    from `tests/unit/test_websocket_cleanup.py` (no Redis): each known message
    type routes to the right collaborator / sends the right message; **unknown
    type** → `ErrorMessage`; **malformed `data`** (ValidationError) →
    `ErrorMessage`, loop survives; **`Action` while not in a room** → error path
    → `ErrorMessage`; mid-session re-join → error.
  - New `tests/unit/test_game_runner.py` — **`pytestmark = pytest.mark.unit`**:
    `start_game`/`process_action` update room state and invoke the per-player
    fan-out callback once per player; `get_valid_actions`/`get_game_state` query
    logic — all with stubbed lobby/registry/engine, **no Redis**.
  - Extend serialization coverage if branches remain uncovered beyond
    `test_event_visibility.py` (opponent-card masking).
  - Live-Redis paths (`PlayerConnections._player_loop`, real `RoomRegistry`
    over live Redis, pub/sub delivery) stay out of scope (Follow-up).
- **Gate:** `cd back && make check` green — these are **unit** tests, so they
  lift the `make check` coverage for `app/websocket/{message_router,game_runner}`.
- **Depends on:** Step 1.
- **Label:** none (test files only).

### Step 8 — Per-package coverage gate: script + baseline (label-free)
- [ ] **Status:** not started
- **Why / failure mode closed:** with the test layer in place, the *floor* must
  lock it in. Today one global `fail_under = 62` is met by the engine alone, so
  the new boundary coverage can silently erode. This adds the gate **mechanism**
  (mirroring `scripts/mutation_gate.py`) without yet wiring it into CI, so it
  ships as a small, locally-verifiable PR.
- **Do:**
  - Add `back/scripts/coverage_gate.py` (mirror `scripts/mutation_gate.py`'s
    shape: read JSON → compute → render GitHub-summary table → exit non-zero on
    regression with `+1e-9` tolerance). It reads a coverage JSON
    (`coverage json` / `--cov-report=json:cov.json`) and **aggregates the
    per-file `files` entries into package buckets by path prefix** — `coverage
    json` is keyed by file (`app/routers/auth.py`), it has **no** per-package
    rollup, so the script must sum, per bucket (`app/routers/`, `app/auth/`,
    `app/services/`, `app/websocket/`), the `summary` counts and compute a
    branch-aware percent matching coverage's own metric (`branch = true` is set):
    `100 * (covered_lines + covered_branches) / (num_statements + num_branches)`.
    Compare each bucket to its floor in `back/coverage-baseline.json`; write a
    markdown table (package | coverage | floor | pass/fail) to
    `$GITHUB_STEP_SUMMARY`; `::error::` + non-zero exit on any regression.
  - Add `back/coverage-baseline.json` (mirror `mutation-baseline.json`'s shape):
    `{"packages": {"app.routers": <floor>, "app.auth": <floor>, "app.services":
    <floor>, "app.websocket": <floor>}, "comment": "<measured %, date, counts;
    ratchet up only; lower only behind the harness-change label>"}`. **Measure
    the floors from the full-suite `cov.json`** (services up: `cd back && uv run
    pytest --cov=app --cov-report=json:cov.json`), set each floor **at** the
    measured level so the gate is green on landing, and only ratchet up. These
    floors are measured against the same full-suite run the CI gate will use
    (Step 9) — **not** a `make check` run (which has no DB and would read
    near-zero for routers/services).
  - **`back/scripts/coverage_gate.py` and `back/coverage-baseline.json` are NOT
    harness-protected** — this step is label-free.
- **Gate:** `cd back && make check` green; with services up, generate `cov.json`
  (`uv run pytest --cov=app --cov-report=json:cov.json`) then `cd back && uv run
  python scripts/coverage_gate.py` exits 0. Prove the ratchet bites: bump one
  package's floor above its measured value → the gate exits non-zero → restore.
- **Depends on:** Steps 2–7 (floors must sit at real post-(A) levels).
- **Label:** none (new `back/scripts/*` + `back/coverage-baseline.json` only).

### Step 9 — Wire the per-package coverage gate into CI
- [ ] **Status:** not started
- **Why / failure mode closed:** the gate from Step 8 only protects anything once
  CI runs it. This wires it into the one job that has the infra to measure
  boundary coverage honestly.
- **Do:**
  - In `.github/workflows/ci.yml`, in the **`backend-integration`** job (it
    already provisions Postgres + Redis and runs `alembic upgrade head`), run the
    **full suite** with a JSON coverage report and then the gate: replace/augment
    the `uv run pytest -m integration` step with `uv run pytest --cov=app
    --cov-report=json:cov.json` (the full suite — both markers — since the infra
    is present) followed by `uv run python scripts/coverage_gate.py`. One job,
    one `cov.json`, no `coverage combine`.
  - Do **not** touch `make check`'s `fail_under` (pyproject.toml) — the
    per-package gate is additive and CI-only.
  - Document the gate + ratchet in [`docs/harness.md`](../../harness.md) (the
    sensor list and the "mutation score / coverage" section), describing it as a
    per-package coverage ratchet alongside the mutation ratchet.
- **Gate:** the edited workflow is valid (the `e2e`/`backend-integration` jobs
  still parse and pass); locally re-confirm `cd back && uv run python
  scripts/coverage_gate.py` exits 0 against a full-suite `cov.json`.
- **Depends on:** Step 8.
- **Label:** **LABEL REQUIRED** — edits `.github/workflows/ci.yml` (and
  `docs/harness.md`, which is unprotected). `harness-guard` is **red until a
  human applies `harness-change`**; that is the designed tripwire.

### Step 10 — Re-enable strict mypy on `app.services.*`
- [ ] **Status:** not started
- **Why / failure mode closed:** `app.services.*` carries `ignore_errors = true`
  (pyproject.toml lines ~103–109), so type regressions in the business layer are
  invisible. This is the first half of the deferred **Backend type coverage** rung.
- **Do:**
  - In `back/pyproject.toml`, remove `"app.services.*"` from the `ignore_errors =
    true` override (leave `app.websocket.*` and `app.settings.*` for now). Prefer
    real annotations over a narrower `disable_error_code`; add one only if a
    genuinely intractable dynamic-SQLAlchemy pattern requires it.
  - `cd back && make typecheck`; fix every surfaced error in `app/services/*`
    (annotate returns, narrow `T | None`, type the `Session`/relationship
    accesses). No `# type: ignore` without a one-line why.
  - Update the **Backend type coverage** bullet in
    [`docs/harness.md`](../../harness.md#follow-up-rungs-toward-h3): `services`
    now type-checked; `websocket` pending (Step 11).
- **Gate:** `cd back && make typecheck` clean and `cd back && make check` green.
- **Depends on:** Step 6 (service tests reduce the risk of a type-fix changing
  behaviour).
- **Label:** **LABEL REQUIRED** — edits `back/pyproject.toml`. `harness-guard`
  red until `harness-change` applied.

### Step 11 — Re-enable strict mypy on `app.websocket.*`; finish the rung; complete the plan
- [ ] **Status:** not started
- **Why / failure mode closed:** `app.websocket.*` is the last `ignore_errors`
  boundary package; the async/Redis-adjacent code is exactly where a wrong type
  slips through. Closing it completes the deferred rung.
- **Do:**
  - In `back/pyproject.toml`, remove `"app.websocket.*"` from the `ignore_errors`
    override. `cd back && make typecheck`; fix the surfaced `app/websocket/*`
    errors (async signatures, the `WebSocketMessage` unions, the fan-out
    callbacks, the `redis`/`broadcaster` boundaries — `broadcaster.*` already has
    `ignore_missing_imports`).
  - Update [`docs/harness.md`](../../harness.md#follow-up-rungs-toward-h3): mark
    **Backend type coverage** done for `services` + `websocket` (only `settings`
    may remain); cross-link this plan.
  - **Complete the plan:** confirm all boxes ticked, move this file from
    `docs/exec-plans/active/` to `docs/exec-plans/completed/`, leave a "PLAN
    COMPLETE" note for the next agent.
- **Gate:** `cd back && make typecheck` clean and `cd back && make check` green;
  with services up, `cd back && uv run python scripts/coverage_gate.py` still
  exits 0.
- **Depends on:** Step 7 (websocket tests), Step 10 (services mypy first).
- **Label:** **LABEL REQUIRED** — edits `back/pyproject.toml`. `harness-guard`
  red until `harness-change` applied. (The final move-to-completed is docs-only.)

---

## 5. Notes / decisions

- **Order is by leverage then dependency:** fixtures (unblock everything) → auth
  (top security value) → routers → services → websocket → coverage-gate script →
  wire into CI → mypy services → mypy websocket.
- **Marker discipline.** `--strict-markers` is on and only `unit`/`integration`
  exist. Every new file declares exactly one `pytestmark`: `unit` for DB/Redis-
  free tests (they lift `make check`), `integration` for anything needing
  Postgres or live Redis (they run in `backend-integration` and are scored by the
  per-package gate).
- Steps 1–8 are **label-free** (test files + an unprotected gate script/baseline);
  the ralph loop can ship one per iteration with no human gate.
- Steps 9–11 are the only **LABEL REQUIRED** steps (CI wiring, then
  `pyproject.toml` mypy). Expect `harness-guard` red on the PR until a human
  applies `harness-change`; that is the designed tripwire.
- **Do not** try to make DB-backed tests lift the `make check` `fail_under` — the
  `backend` job has no database, so they skip there. The per-package CI gate is
  what makes their coverage count.

---

## 6. Verification (definition of done)

- `cd back && make check` green after every step (the global unit floor never
  drops; unit-marked steps lift it).
- With services up, `cd back && uv run pytest -m integration` green for every
  integration test added (these run in the `backend-integration` CI job).
- `cd back && make typecheck` clean with `ignore_errors` removed from both
  `app.services.*` and `app.websocket.*`.
- The per-package coverage gate exists (`back/scripts/coverage_gate.py` +
  `back/coverage-baseline.json`), runs in the `backend-integration` CI job over
  the full suite, enforces floors for `app.routers`/`app.auth`/`app.services`/
  `app.websocket` set at honest post-(A) levels that only ratchet up, and
  `cd back && uv run python scripts/coverage_gate.py` exits 0 against a
  full-suite `cov.json`.
- Every boundary test file asserts at least one negative/security path (authz
  isolation, bad/expired/missing token, malformed message, illegal action).
- The **Backend type coverage** rung in
  [`docs/harness.md`](../../harness.md#follow-up-rungs-toward-h3) is updated/
  retired, and the new coverage gate is documented in the sensor list.
- This file moved to `docs/exec-plans/completed/`.

---

## 7. Risks & mitigations

- **R: Router/service tests need real Postgres.** → They are `integration`-marked
  and run in CI's `backend-integration` job (and locally with `make up` +
  `DATABASE_URL`). Their coverage is locked by the per-package CI gate, not
  `make check`. This is stated explicitly so no agent mis-marks them `unit` and
  watches them silently skip.
- **R: Rollback fixture doesn't roll back because routers `.commit()`.** → Step 1
  uses the SAVEPOINT/`begin_nested` + `after_transaction_end` recipe and proves
  it with a leak test; the in-request commit only ends the SAVEPOINT, the outer
  transaction is rolled back on teardown.
- **R: `auth_client` override makes negative auth paths unreachable.** → D3 splits
  the fixtures: negative/cross-user tests use the un-overridden `client` with
  real tokens; `auth_client` is happy-path sugar only.
- **R: Coverage gate set too high → permanent red.** → Floors are measured from
  the same full-suite `cov.json` the CI gate uses (read, don't guess) and set
  **at** that level; ratchet only upward.
- **R: mypy re-enable surfaces a large dynamic-SQLAlchemy error set.** → Fix in
  two scoped steps (services, then websocket) with the service/websocket tests
  already in place as a behaviour safety net; narrow `disable_error_code` only
  where a real dynamic pattern is intractable, never a blanket `ignore_errors`.
- **R: New tests fail on warnings.** → `filterwarnings = ["error"]` treats
  warnings as errors; fix the warning at source (don't silence it).
- **R: Harness tripwire mistaken for breakage.** → Steps 9–11 are flagged LABEL
  REQUIRED; the red `harness-guard` is expected until a human labels.

---

## 8. Follow-up rungs (explicitly out of scope)

- **Activate the Claude PR-review workflow** (`claude-review.yml` — add the
  API-key secret + set `ENABLE_CLAUDE_REVIEW=true`). Independent and trivial;
  tracked in [`docs/harness.md`](../../harness.md#follow-up-rungs-toward-h3), not
  blocked by this plan. (Highest-ROI single action for overnight trust — do it
  alongside this plan, not inside it.)
- **Negative-path & cross-browser (WebKit) / mobile-viewport e2e** — a separate
  plan; this plan stops at the backend trust boundary.
- **`app.settings.*` mypy** — may remain on `ignore_errors`; not part of this
  rung (this plan clears `services` + `websocket` only).
- **Integration-marked coverage of live-Redis paths** (`_player_loop`, real
  `RoomRegistry`, pub/sub delivery) — out of the unit/fakes scope here; the
  per-package gate will count them automatically if/when they're added (it scores
  the full suite).
