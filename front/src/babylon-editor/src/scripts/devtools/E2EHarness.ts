/**
 * E2EHarness — build-gated `window.__creature` test API.
 *
 * Implements the shared contract in ./e2e-contract.ts (the Playwright side
 * imports the same file, so the two can't drift; the `CreatureHarness`
 * annotation below is the conformance check). A THIN facade: every behavior
 * lives on its owning class — reads on GameStateStore, action queries on
 * ActionBuilder, waits on BoardController (`once`/`waitForState`), mesh
 * resolution on CardEntityManager — and this file only adds the harness glue:
 * singleton lookup, contract-default timeouts, throw-on-missing wrappers, and
 * the world→page-coordinate projection used by the real-pointer smoke.
 *
 * Attached to `window` only when the build-time `PUBLIC_E2E_HOOKS` flag is set
 * (wired from BabylonEditorScene.svelte); unset builds tree-shake it away. It
 * drives actions through the REAL production path (ActionBuilder →
 * GameConnection), so it's no privilege escalation — the socket is
 * authenticated and the server validates every action.
 */

import { Matrix, Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { Scene } from '@babylonjs/core/scene';

import BoardController from '../BoardController';
import GameConnection from '../game/GameConnection';
import { CardEntityManager } from '../entities/CardEntityManager';
import { GameStateStore } from '../state/GameStateStore';
import { ActionBuilder } from '../state/ActionBuilder';
import type { ValidAction } from '../game/types';
import type { Zone } from '../game/models';
import type { StateChangeEvents } from '../state/events';
import type { CreatureHarness, HarnessAction } from './e2e-contract';

const DEFAULT_TIMEOUT_MS = 10_000;

// ── Singleton accessors (resolved lazily, at call time) ────────────────

function requireStore(): GameStateStore {
	const store = GameStateStore.instance;
	if (!store) throw new Error('E2EHarness: GameStateStore not initialized');
	return store;
}

function requireBoard(): BoardController {
	const board = BoardController.instance;
	if (!board) throw new Error('E2EHarness: BoardController not initialized');
	return board;
}

function requireScene(): Scene {
	const scene = CardEntityManager.instance?.scene;
	if (!scene) throw new Error('E2EHarness: CardEntityManager not initialized');
	return scene;
}

// Cache one ActionBuilder per live connection — a new game gets a fresh one.
let cachedBuilder: ActionBuilder | null = null;
let cachedBuilderConn: GameConnection | null = null;

function requireBuilder(): ActionBuilder {
	const conn = GameConnection.instance;
	if (!conn) throw new Error('E2EHarness: GameConnection not initialized');
	if (!cachedBuilder || cachedBuilderConn !== conn) {
		cachedBuilder = new ActionBuilder(conn);
		cachedBuilderConn = conn;
	}
	// The builder is store-free by design — feed it the live actions at each use.
	cachedBuilder.setValidActions(requireStore().validActions);
	return cachedBuilder;
}

function requireAction(action: ValidAction | undefined, describe: string): ValidAction {
	if (!action) {
		throw new Error(`E2EHarness: no valid action found for ${describe}`);
	}
	return action;
}

// ── Harness factory ────────────────────────────────────────────────────

export function attachE2EHarness(): CreatureHarness {
	const dispatch = (action: HarnessAction): void => {
		requireBuilder().execute(action);
	};

	const harness: CreatureHarness = {
		// Read
		getState: () => requireStore().state,
		validActions: () => requireStore().validActions,
		phase: () => requireStore().currentPhase,
		isMyTurn: () => requireStore().isMyTurn,
		myPlayerId: () => requireStore().myPlayerId,
		opponentId: () => requireStore().getOpponentId(),
		// Specs pass server zone strings; the store API takes the Zone union.
		cardsInZone: (zone, perspective = 'my') =>
			perspective === 'opp'
				? requireStore().getOpponentCardsInZone(zone as Zone)
				: requireStore().getMyCardsInZone(zone as Zone),

		// World position of a card mesh → page coords, so a spec can `page.mouse.click`
		// it and exercise the real scene.pick → InteractionManager chain the drive API skips.
		screenPositionOf: (instanceId) => {
			const entity = CardEntityManager.instance?.getByInstanceId(instanceId);
			if (!entity) {
				throw new Error(`E2EHarness: no card mesh for ${instanceId}`);
			}
			const mesh = entity.mesh;
			const scene = mesh.getScene();
			const camera = scene.activeCamera;
			if (!camera) throw new Error('E2EHarness: scene has no active camera');
			const engine = scene.getEngine();
			const renderWidth = engine.getRenderWidth();
			const renderHeight = engine.getRenderHeight();
			const canvas = engine.getRenderingCanvas();
			if (!canvas) throw new Error('E2EHarness: engine has no rendering canvas');

			// Project the mesh centre to render-buffer pixels, then map to page coords
			// (buffer size can differ from the displayed canvas under devicePixelRatio).
			mesh.computeWorldMatrix(true);
			const projected = Vector3.Project(
				mesh.getAbsolutePosition(),
				Matrix.Identity(),
				scene.getTransformMatrix(),
				camera.viewport.toGlobal(renderWidth, renderHeight),
			);
			const rect = canvas.getBoundingClientRect();
			return {
				x: rect.left + (projected.x / renderWidth) * rect.width,
				y: rect.top + (projected.y / renderHeight) * rect.height,
			};
		},
		cardAtScreenPoint: (x, y) => {
			const scene = requireScene();
			const engine = scene.getEngine();
			const canvas = engine.getRenderingCanvas();
			if (!canvas) throw new Error('E2EHarness: engine has no rendering canvas');
			const rect = canvas.getBoundingClientRect();
			// Page coords → render-buffer pixels (the space scene.pick expects).
			const canvasX = ((x - rect.left) / rect.width) * engine.getRenderWidth();
			const canvasY = ((y - rect.top) / rect.height) * engine.getRenderHeight();
			const pick = scene.pick(canvasX, canvasY);
			if (!pick?.hit || !pick.pickedMesh) return null;
			return CardEntityManager.instance?.resolveFromMesh(pick.pickedMesh)?.instanceId ?? null;
		},

		// Drive — find via ActionBuilder's affordance queries (the same API the
		// interactive board uses), then execute through the real path.
		dispatch,
		playCard: (instanceId) => {
			// play_card references its card via the `instance_ids` list, which
			// ActionBuilder's _referencesCard already matches.
			const action = requireAction(
				requireBuilder()
					.getActionsForCard(instanceId)
					.find((a) => a.action === 'play_card'),
				`play_card ${instanceId}`,
			);
			dispatch(action);
			return action;
		},
		pass: () => {
			const action = requireAction(requireBuilder().getPassAction(), 'pass');
			dispatch(action);
			return action;
		},
		swap: (supportingId, attackingId) => {
			const action = requireAction(
				requireBuilder()
					.getActionsForCard(supportingId)
					.find((a) => a.action === 'swap' && a.attacking_card_id === attackingId),
				`swap ${supportingId} ↔ ${attackingId}`,
			);
			dispatch(action);
			return action;
		},
		attack: (attackerId, targetId) => {
			// Falsy target check on purpose: the backend sends "" for no-defender.
			const action = requireAction(
				requireBuilder()
					.getActionsForCard(attackerId)
					.find(
						(a) =>
							a.action === 'attack' &&
							(targetId === undefined ? !a.target_card_id : a.target_card_id === targetId),
					),
				`attack ${attackerId} → ${targetId ?? '(no defender)'}`,
			);
			dispatch(action);
			return action;
		},
		promote: (instanceId) => {
			const action = requireAction(
				requireBuilder()
					.getActionsForCard(instanceId)
					.find((a) => a.action === 'promote'),
				`promote ${instanceId}`,
			);
			dispatch(action);
			return action;
		},

		// Wait — BoardController owns the bus and the wait primitives; the
		// harness only applies the contract's default timeout.
		waitForState: (predicate, timeout = DEFAULT_TIMEOUT_MS) =>
			requireBoard().waitForState(predicate, timeout),
		// The contract keeps event names as plain strings; the bus is typed.
		nextEvent: (name, timeout = DEFAULT_TIMEOUT_MS) =>
			requireBoard().once(name as keyof StateChangeEvents, timeout),
	};

	window.__creature = harness;
	console.log('[E2EHarness] window.__creature attached');
	return harness;
}
