import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import type { Scene } from '@babylonjs/core/scene';
import type { IScript } from 'babylonjs-editor-tools';

import GameNetworkManagerComponent from './GameNetworkManagerComponent';
import { CardEntityManager } from './entities/CardEntityManager';
import type { Zone, ClientCard, ClientGameState } from './game/models';
import {
	GameStateStore,
	type CardMovedData,
	type CardHealthChangedData,
	type CardDestroyedData,
	type PhaseChangedData,
	type TurnChangedData,
	type GameOverData,
	type AttackDeclaredData,
	type CardsSwappedData,
} from './state/GameStateStore';
import type { ZoneRenderer } from './zones/ZoneRenderer';
import { DeckZoneRenderer } from './zones/DeckZoneRenderer';
import { HandZoneRenderer } from './zones/HandZoneRenderer';
import { FieldZoneRenderer } from './zones/FieldZoneRenderer';
import { GraveyardZoneRenderer } from './zones/GraveyardZoneRenderer';
import { AnimationPipeline } from './animation/AnimationPipeline';
import type { GameAnimation } from './animation/GameAnimation';
import { CardMoveAnimation } from './animation/CardMoveAnimation';
import { CardFlipAnimation } from './animation/CardFlipAnimation';
import { AttackAnimation } from './animation/AttackAnimation';
import { DamageAnimation } from './animation/DamageAnimation';
import { DestroyAnimation } from './animation/DestroyAnimation';
import { DelayAnimation } from './animation/DelayAnimation';
import { ParallelAnimation } from './animation/ParallelAnimation';

const ZONE_DECK = 'DECK' as Zone;
const ZONE_HAND = 'HAND' as Zone;
const ZONE_SUPPORTING = 'SUPPORTING' as Zone;
const ZONE_ATTACKING = 'ATTACKING' as Zone;
const ZONE_GRAVEYARD = 'GRAVEYARD' as Zone;

export default class BoardController implements IScript {
	private _stateStore!: GameStateStore;
	private _cardManager!: CardEntityManager;
	private _animationPipeline!: AnimationPipeline;
	private _zones = new Map<string, ZoneRenderer>();

	/**
	 * Guards against premature event handling during processGameStarted.
	 * The store processes initial events (emitting cardAdded/cardMoved) BEFORE
	 * emitting gameStarted. Without this flag, those events would create entities
	 * and enqueue animations before the board is built.
	 */
	private _boardReady = false;

	/** Instance IDs whose cardMoved events should be skipped (handled by cardsSwapped). */
	private _swapInProgress = new Set<string>();

	/** Instance IDs whose cardMoved events should be skipped (handled by cardDestroyed). */
	private _destroyInProgress = new Set<string>();

	public constructor(private _scene: Scene) {}

	// ====================================================================
	// IScript lifecycle
	// ====================================================================

	public onStart(): void {
		const networkManager = GameNetworkManagerComponent.instance;
		if (!networkManager) throw new Error('BoardController: GameNetworkManagerComponent not initialized');

		const store = networkManager.getStateStore();
		if (!store) throw new Error('BoardController: GameStateStore not initialized');
		this._stateStore = store;

		this._cardManager = CardEntityManager.getOrCreate(this._scene);
		this._animationPipeline = new AnimationPipeline(this._scene);

		this._cardManager.initBlueprints('UpsideUpCard_BP', 'UpsideDownCard_BP');
		this._initZoneRenderers();
		this._subscribe();

		this._animationPipeline.onQueueStarted = () => {
			// InteractionManager (Step 9) checks animationPipeline.isPlaying
		};
		this._animationPipeline.onQueueDrained = () => {
			// InteractionManager re-enables interaction
		};
	}

	public onUpdate(): void {}

	public onStop(): void {
		this._unsubscribe();
		this._animationPipeline.dispose();
		for (const renderer of this._zones.values()) renderer.dispose();
		this._zones.clear();
		// Intentionally NOT calling _cardManager.dispose() — the manager singleton
		// may outlive this script (e.g. scene hot-reload). Individual entity cleanup
		// happens in _handleStateReplaced when needed.
	}

	// ====================================================================
	// Zone renderer initialization
	// ====================================================================

	private _initZoneRenderers(): void {
		const myId = this._stateStore.myPlayerId;
		const oppId = this._stateStore.getOpponentId() ?? '';

		this._registerZone('my', ZONE_DECK, new DeckZoneRenderer(myId, this._anchor('My_Deck_Anchor')));
		this._registerZone('my', ZONE_HAND, new HandZoneRenderer(myId, this._anchor('My_Hand_Anchor'), true));
		this._registerZone('my', ZONE_SUPPORTING, new FieldZoneRenderer(ZONE_SUPPORTING, myId, this._anchor('My_Supporting_Anchor'), 3, true));
		this._registerZone('my', ZONE_ATTACKING, new FieldZoneRenderer(ZONE_ATTACKING, myId, this._anchor('My_Attacking_Anchor'), 2, true));
		this._registerZone('my', ZONE_GRAVEYARD, new GraveyardZoneRenderer(myId, this._anchor('My_Graveyard_Anchor')));

		this._registerZone('opp', ZONE_DECK, new DeckZoneRenderer(oppId, this._anchor('Opp_Deck_Anchor')));
		this._registerZone('opp', ZONE_HAND, new HandZoneRenderer(oppId, this._anchor('Opp_Hand_Anchor'), false));
		this._registerZone('opp', ZONE_SUPPORTING, new FieldZoneRenderer(ZONE_SUPPORTING, oppId, this._anchor('Opp_Supporting_Anchor'), 3, false));
		this._registerZone('opp', ZONE_ATTACKING, new FieldZoneRenderer(ZONE_ATTACKING, oppId, this._anchor('Opp_Attacking_Anchor'), 2, false));
		this._registerZone('opp', ZONE_GRAVEYARD, new GraveyardZoneRenderer(oppId, this._anchor('Opp_Graveyard_Anchor')));
	}

	private _registerZone(perspective: 'my' | 'opp', zone: Zone, renderer: ZoneRenderer): void {
		this._zones.set(this._zoneKey(perspective, zone), renderer);
	}

	private _anchor(name: string): TransformNode {
		const node = this._scene.getTransformNodeByName(name);
		if (!node) throw new Error(`BoardController: missing required anchor node "${name}" in scene`);
		return node;
	}

	// ====================================================================
	// State store subscriptions
	// ====================================================================

	private _subscribe(): void {
		this._stateStore.on('gameStarted', this._onGameStarted);
		this._stateStore.on('stateReplaced', this._onStateReplaced);
		this._stateStore.on('cardAdded', this._onCardAdded);
		this._stateStore.on('cardsSwapped', this._onCardsSwapped);
		this._stateStore.on('cardMoved', this._onCardMoved);
		this._stateStore.on('attackDeclared', this._onAttackDeclared);
		this._stateStore.on('cardHealthChanged', this._onCardHealthChanged);
		this._stateStore.on('cardDestroyed', this._onCardDestroyed);
		this._stateStore.on('phaseChanged', this._onPhaseChanged);
		this._stateStore.on('turnChanged', this._onTurnChanged);
		this._stateStore.on('gameOver', this._onGameOver);
	}

	private _unsubscribe(): void {
		this._stateStore.off('gameStarted', this._onGameStarted);
		this._stateStore.off('stateReplaced', this._onStateReplaced);
		this._stateStore.off('cardAdded', this._onCardAdded);
		this._stateStore.off('cardsSwapped', this._onCardsSwapped);
		this._stateStore.off('cardMoved', this._onCardMoved);
		this._stateStore.off('attackDeclared', this._onAttackDeclared);
		this._stateStore.off('cardHealthChanged', this._onCardHealthChanged);
		this._stateStore.off('cardDestroyed', this._onCardDestroyed);
		this._stateStore.off('phaseChanged', this._onPhaseChanged);
		this._stateStore.off('turnChanged', this._onTurnChanged);
		this._stateStore.off('gameOver', this._onGameOver);
	}

	// ====================================================================
	// Event handlers (arrow functions to preserve `this`)
	// ====================================================================

	private _onGameStarted = (state: ClientGameState): void => {
		this._buildBoard(state);
		this._boardReady = true;
	};

	private _onStateReplaced = (state: ClientGameState): void => {
		this._animationPipeline.skipAll();
		this._tearDownBoard();
		this._buildBoard(state);
		this._boardReady = true;
	};

	private _onCardAdded = (card: ClientCard): void => {
		if (!this._boardReady) return;
		this._cardManager.createEntity(card, card.faceUp);
	};

	private _onCardMoved = (data: CardMovedData): void => {
		if (!this._boardReady) return;

		if (this._swapInProgress.delete(data.instanceId)) return;
		if (this._destroyInProgress.delete(data.instanceId)) return;

		const entity = this._cardManager.getByInstanceId(data.instanceId);
		if (!entity) return;

		const sourceRenderer = this._rendererFor(data.ownerId, data.fromZone);
		const destRenderer = this._rendererFor(data.ownerId, data.toZone);
		if (!destRenderer) return;

		const wasInRenderer = this._rendererContains(sourceRenderer, data.instanceId);
		if (wasInRenderer) sourceRenderer!.removeCard(data.instanceId);

		const from = wasInRenderer
			? entity.mesh.position.clone()
			: (sourceRenderer?.getExitPosition() ?? entity.mesh.position.clone());
		const to = destRenderer.getEntryPosition();

		const batch: GameAnimation[] = [new CardMoveAnimation(entity, from, to)];

		if (data.fromZone === ZONE_DECK && data.toZone === ZONE_HAND && this._isMine(data.ownerId)) {
			batch.push(new CardFlipAnimation(entity, true));
		}

		batch.push(this._callback(() => {
			destRenderer.addCard(entity, false);
			if (wasInRenderer) sourceRenderer!.repositionAll(true);
		}));

		this._animationPipeline.enqueueBatch(batch);
	};

	private _onCardsSwapped = (data: CardsSwappedData): void => {
		if (!this._boardReady) return;

		this._swapInProgress.add(data.supportingId);
		this._swapInProgress.add(data.attackingId);

		const supEntity = this._cardManager.getByInstanceId(data.supportingId);
		const atkEntity = this._cardManager.getByInstanceId(data.attackingId);
		if (!supEntity || !atkEntity) return;

		const supRenderer = this._rendererFor(data.ownerId, ZONE_SUPPORTING);
		const atkRenderer = this._rendererFor(data.ownerId, ZONE_ATTACKING);
		if (!supRenderer || !atkRenderer) return;

		supRenderer.removeCard(data.supportingId);
		atkRenderer.removeCard(data.attackingId);

		const parallel = new ParallelAnimation([
			new CardMoveAnimation(supEntity, supEntity.mesh.position.clone(), atkRenderer.getEntryPosition()),
			new CardMoveAnimation(atkEntity, atkEntity.mesh.position.clone(), supRenderer.getEntryPosition()),
		]);

		this._animationPipeline.enqueue(parallel);
		this._animationPipeline.enqueue(this._callback(() => {
			atkRenderer.addCard(supEntity, false);
			supRenderer.addCard(atkEntity, false);
		}));
	};

	private _onAttackDeclared = (data: AttackDeclaredData): void => {
		if (!this._boardReady) return;

		const attacker = this._cardManager.getByInstanceId(data.attackerId);
		if (!attacker) return;

		const target = this._cardManager.getByInstanceId(data.targetId);
		const targetOrPos = target ?? this._opponentFieldCenter();

		this._animationPipeline.enqueue(new AttackAnimation(attacker, targetOrPos));
	};

	private _onCardHealthChanged = (data: CardHealthChangedData): void => {
		if (!this._boardReady) return;

		const entity = this._cardManager.getByInstanceId(data.instanceId);
		if (!entity) return;

		const damage = data.oldHealth - data.newHealth;
		this._animationPipeline.enqueue(new DamageAnimation(entity, damage, data.newHealth));
	};

	private _onCardDestroyed = (data: CardDestroyedData): void => {
		if (!this._boardReady) return;

		this._destroyInProgress.add(data.instanceId);

		const entity = this._cardManager.getByInstanceId(data.instanceId);
		if (!entity) return;

		const currentRenderer = this._findRendererContaining(data.instanceId);
		currentRenderer?.removeCard(data.instanceId);

		const graveyardRenderer = this._rendererFor(data.ownerId, ZONE_GRAVEYARD);
		const graveyardPos = graveyardRenderer?.getEntryPosition() ?? Vector3.Zero();

		this._animationPipeline.enqueue(new DestroyAnimation(entity, graveyardPos));
		this._animationPipeline.enqueue(this._callback(() => {
			entity.mesh.visibility = 1;
			entity.mesh.scaling.setAll(1);
			graveyardRenderer?.addCard(entity, false);
			currentRenderer?.repositionAll(true);
		}));
	};

	private _onPhaseChanged = (_data: PhaseChangedData): void => {
		if (!this._boardReady) return;
		this._animationPipeline.enqueue(new DelayAnimation(200));
	};

	private _onTurnChanged = (_data: TurnChangedData): void => {
		if (!this._boardReady) return;
		this._animationPipeline.enqueue(new DelayAnimation(800));
	};

	private _onGameOver = (_data: GameOverData): void => {
		this._animationPipeline.skipAll();
	};

	// ====================================================================
	// Board building
	// ====================================================================

	private _buildBoard(state: ClientGameState): void {
		const myId = this._stateStore.myPlayerId;
		for (const card of Object.values(state.cards)) {
			const isMine = card.ownerId === myId;
			const faceUp = isMine && card.zone !== ZONE_DECK;
			const entity = this._cardManager.createEntity(card, faceUp);
			this._rendererFor(card.ownerId, card.zone)?.addCard(entity, false);
		}
	}

	private _tearDownBoard(): void {
		for (const entity of this._cardManager.getAllEntities()) {
			this._cardManager.destroyEntity(entity.instanceId);
		}
		for (const renderer of this._zones.values()) renderer.dispose();
		this._zones.clear();
		this._swapInProgress.clear();
		this._destroyInProgress.clear();
		this._initZoneRenderers();
	}

	// ====================================================================
	// Helpers
	// ====================================================================

	private _zoneKey(perspective: 'my' | 'opp', zone: Zone): string {
		return `${perspective}_${zone}`;
	}

	private _rendererFor(ownerId: string, zone: Zone): ZoneRenderer | undefined {
		const p = this._isMine(ownerId) ? 'my' : 'opp';
		return this._zones.get(this._zoneKey(p, zone));
	}

	private _findRendererContaining(instanceId: string): ZoneRenderer | undefined {
		for (const renderer of this._zones.values()) {
			if (renderer.getEntities().some((e) => e.instanceId === instanceId)) return renderer;
		}
		return undefined;
	}

	private _rendererContains(renderer: ZoneRenderer | undefined, instanceId: string): boolean {
		return renderer?.getEntities().some((e) => e.instanceId === instanceId) ?? false;
	}

	private _isMine(ownerId: string): boolean {
		return ownerId === this._stateStore.myPlayerId;
	}

	private _opponentFieldCenter(): Vector3 {
		const renderer = this._zones.get(this._zoneKey('opp', ZONE_ATTACKING));
		return renderer?.getEntryPosition() ?? Vector3.Zero();
	}

	/** Inline GameAnimation that executes a synchronous callback. */
	private _callback(fn: () => void): GameAnimation {
		return {
			name: 'Callback',
			duration: 0,
			execute: () => { fn(); return Promise.resolve(); },
			cancel: () => { fn(); },
		};
	}
}
