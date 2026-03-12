import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import type { Scene } from '@babylonjs/core/scene';
import type { IScript } from 'babylonjs-editor-tools';

import GameConnection from './game/GameConnection';
import { CardDefinitionCache } from './game/CardDefinitionCache';
import { CardEntityManager } from './entities/CardEntityManager';
import type { GameMessage, ValidAction } from './game/types';
import type { Zone, ClientCard, ClientGameState } from './game/models';
import { createFaceDownCard } from './game/models';
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
	private _connection!: GameConnection;
	private _stateStore!: GameStateStore;
	private _cardCache!: CardDefinitionCache;
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
		const conn = GameConnection.instance;
		if (!conn) throw new Error('BoardController: GameConnection not initialized');
		this._connection = conn;

		const store = conn.getStateStore();
		if (!store) throw new Error('BoardController: GameStateStore not initialized');
		this._stateStore = store;

		this._cardCache = conn.getCardCache()!;
		this._cardManager = CardEntityManager.getOrCreate(this._scene);
		this._animationPipeline = new AnimationPipeline(this._scene);

		this._cardManager.initBlueprints('UpsideUpCard_BP', 'UpsideDownCard_BP');
		this._initZoneRenderers();
		this._subscribe();

		this._connection.onMessage = this._handleRawMessage;

		this._animationPipeline.onQueueStarted = () => {
			// InteractionManager checks animationPipeline.isPlaying
		};
		this._animationPipeline.onQueueDrained = () => {
			// InteractionManager re-enables interaction
		};
	}

	public onUpdate(): void {}

	public onStop(): void {
		this._unsubscribe();
		if (this._connection) this._connection.onMessage = null;
		this._animationPipeline.dispose();
		for (const renderer of this._zones.values()) renderer.dispose();
		this._zones.clear();
	}

	// ====================================================================
	// Raw WebSocket message routing
	// ====================================================================

	private _handleRawMessage = (message: GameMessage): void => {
		if (message.type === 'action_result' && message.data?.success === false) return;

		switch (message.type) {
			case 'game_started':
				this._stateStore.processGameStarted(message.data);
				this._registerCardsFromEvents(message.data.events as Record<string, unknown>[] | undefined);
				break;
			case 'action_result': {
				const d = message.data;
				if (d.events) {
					const events = d.events as Record<string, unknown>[];
					this._stateStore.processGameEvents(events);
					this._registerCardsFromEvents(events);
				}
				if (d.game_state)
					this._stateStore.processGameState(d.game_state as Record<string, unknown>);
				if (d.valid_actions)
					this._stateStore.updateValidActions(
						(d.valid_actions as ValidAction[]).filter(a => a.player_id === this._stateStore.myPlayerId),
					);
				break;
			}
			case 'valid_actions':
				if (message.data.actions)
					this._stateStore.updateValidActions(
						(message.data.actions as ValidAction[]).filter(a => a.player_id === this._stateStore.myPlayerId),
					);
				break;
			case 'game_state':
				if (message.data.state)
					this._stateStore.processGameState(message.data.state as Record<string, unknown>);
				break;
		}
	};

	private _registerCardsFromEvents(events: Record<string, unknown>[] | undefined): void {
		if (!events) return;
		for (const event of events) {
			const instanceId = event.instance_id as string | undefined;
			const cardId = event.card_id as number | undefined;
			if (instanceId && cardId && cardId > 0) {
				this._cardCache?.registerInstance(instanceId, cardId);
			}
		}
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

	private async _buildBoard(state: ClientGameState): Promise<void> {
		const myId = this._stateStore.myPlayerId;
		const oppId = this._stateStore.getOpponentId() ?? '';
		const deckSize = state.config?.deck_size ?? 0;
		const DELAY_MS = 100;
	
		const allPromises: Promise<void>[] = [];
	
		for (const ownerId of [myId, oppId]) {
			const prefix = ownerId === myId ? 'my' : 'opp';
			const renderer = this._rendererFor(ownerId, ZONE_DECK);
			if (!renderer) continue;
	
			for (let i = 0; i < deckSize; i++) {
				const entity = this._cardManager.createEntity(
					createFaceDownCard(`${prefix}_deck_${i}`, ownerId),
					false,
				);
	
				// schedule each addCard with a delay
				const p = new Promise<void>(resolve => {
					setTimeout(async () => {
						await renderer.addCard(entity, true);
						resolve();
					}, i * DELAY_MS);
				});
	
				allPromises.push(p);
			}
		}
	
		// wait for all addCard calls to finish
		await Promise.all(allPromises);
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
