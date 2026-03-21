/**
 * AnimationManager — IScript that owns all visual / rendering concerns.
 *
 * Subscribes to BoardController events and translates them into
 * zone-renderer operations and animation-pipeline sequences.
 * Reads deck card ids from `gameStarted.state` (authoritative server snapshot).
 */

import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import type { Scene } from '@babylonjs/core/scene';
import type { IScript } from 'babylonjs-editor-tools';

import BoardController from '../BoardController';
import { CardEntityManager } from '../entities/CardEntityManager';
import type { Zone, ClientCard, ClientGameState } from '../game/models';

import type {
	CardMovedData,
	CardHealthChangedData,
	CardDestroyedData,
	PhaseChangedData,
	TurnChangedData,
	GameOverData,
	AttackDeclaredData,
	CardsSwappedData,
	GameStartedEventData,
} from '../state/events';

import type { ZoneRenderer } from '../zones/ZoneRenderer';
import { DeckZoneRenderer } from '../zones/DeckZoneRenderer';
import { HandZoneRenderer } from '../zones/HandZoneRenderer';
import { FieldZoneRenderer } from '../zones/FieldZoneRenderer';
import { GraveyardZoneRenderer } from '../zones/GraveyardZoneRenderer';
import { AnimationPipeline } from './AnimationPipeline';
import type { GameAnimation } from './GameAnimation';
import { CardMoveAnimation } from './CardMoveAnimation';
import { CardFlipAnimation } from './CardFlipAnimation';
import { AttackAnimation } from './AttackAnimation';
import { DamageAnimation } from './DamageAnimation';
import { DestroyAnimation } from './DestroyAnimation';
import { DelayAnimation } from './DelayAnimation';
import { ParallelAnimation } from './ParallelAnimation';

const ZONE_DECK = 'DECK' as Zone;
const ZONE_HAND = 'HAND' as Zone;
const ZONE_SUPPORTING = 'SUPPORTING' as Zone;
const ZONE_ATTACKING = 'ATTACKING' as Zone;
const ZONE_GRAVEYARD = 'GRAVEYARD' as Zone;

export default class AnimationManager implements IScript {
	static instance: AnimationManager | null = null;

	private _board!: BoardController;
	private _cardManager!: CardEntityManager;
	private _animationPipeline!: AnimationPipeline;
	private _zones = new Map<string, ZoneRenderer>();

	private _boardReady = false;
	private _pendingCardMoves: CardMovedData[] = [];
	private _swapInProgress = new Set<string>();
	private _destroyInProgress = new Set<string>();

	private _myPlayerId = '';
	private _opponentId = '';

	public constructor(private _scene: Scene) {}

	// ====================================================================
	// IScript lifecycle
	// ====================================================================

	public onStart(): void {
		const board = BoardController.instance;
		if (!board) throw new Error('AnimationManager: BoardController not initialized');
		this._board = board;

		this._cardManager = CardEntityManager.getOrCreate(this._scene);
		this._cardManager.initBlueprints('UpsideUpCard_BP', 'UpsideDownCard_BP');
		this._animationPipeline = new AnimationPipeline(this._scene);
		this._initZoneRenderers();
		this._subscribe();
		AnimationManager.instance = this;
	}

	public onUpdate(): void {}

	public onStop(): void {
		this._unsubscribe();
		this._animationPipeline.dispose();
		for (const renderer of this._zones.values()) renderer.dispose();
		this._zones.clear();
		AnimationManager.instance = null;
	}

	// ====================================================================
	// BoardController subscriptions
	// ====================================================================

	private _subscribe(): void {
		this._board.on('gameStarted', this._onGameStarted);
		this._board.on('stateReplaced', this._onStateReplaced);
		this._board.on('cardsSwapped', this._onCardsSwapped);
		this._board.on('cardMoved', this._onCardMoved);
		this._board.on('attackDeclared', this._onAttackDeclared);
		this._board.on('cardHealthChanged', this._onCardHealthChanged);
		this._board.on('cardDestroyed', this._onCardDestroyed);
		this._board.on('phaseChanged', this._onPhaseChanged);
		this._board.on('turnChanged', this._onTurnChanged);
		this._board.on('gameOver', this._onGameOver);
	}

	private _unsubscribe(): void {
		this._board.off('gameStarted', this._onGameStarted);
		this._board.off('stateReplaced', this._onStateReplaced);
		this._board.off('cardsSwapped', this._onCardsSwapped);
		this._board.off('cardMoved', this._onCardMoved);
		this._board.off('attackDeclared', this._onAttackDeclared);
		this._board.off('cardHealthChanged', this._onCardHealthChanged);
		this._board.off('cardDestroyed', this._onCardDestroyed);
		this._board.off('phaseChanged', this._onPhaseChanged);
		this._board.off('turnChanged', this._onTurnChanged);
		this._board.off('gameOver', this._onGameOver);
	}

	// ====================================================================
	// Event handlers
	// ====================================================================

	private _onGameStarted = (data: GameStartedEventData): void => {
		this._myPlayerId = data.myPlayerId;
		this._opponentId = data.opponentId;
		void this._runGameStarted(data);
	};

	private async _runGameStarted(data: GameStartedEventData): Promise<void> {
		await this._buildBoard(data);
		this._boardReady = true;
		const pending = this._pendingCardMoves;
		this._pendingCardMoves = [];
		for (const move of pending) this._onCardMoved(move);
	}

	private _onStateReplaced = (_state: ClientGameState): void => {
		this._animationPipeline.skipAll();
		this._pendingCardMoves = [];
		this._tearDownBoard();
		this._boardReady = true;
	};

	private _onCardMoved = (data: CardMovedData): void => {
		if (!this._boardReady) {
			this._pendingCardMoves.push(data);
			return;
		}

		if (this._swapInProgress.delete(data.instanceId)) return;
		if (this._destroyInProgress.delete(data.instanceId)) return;

		const entity = this._cardManager.getByInstanceId(data.instanceId);

		const sourceRenderer = this._rendererFor(data.ownerId, data.fromZone);
		const destRenderer = this._rendererFor(data.ownerId, data.toZone);

		sourceRenderer.removeCard(data.instanceId);

		const from = entity.mesh.getAbsolutePosition().clone()
		const to = destRenderer.getEntryPosition();

		const batch: GameAnimation[] = [new CardMoveAnimation(entity, from, to)];

		if (data.fromZone === ZONE_DECK && data.toZone === ZONE_HAND && this._isMine(data.ownerId)) {
			batch.push(new CardFlipAnimation(entity, true));
		}

		batch.push(this._callback(() => {
			destRenderer.addCard(entity, false);
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
	// Zone renderer initialisation
	// ====================================================================

	private _initZoneRenderers(): void {
		for (const renderer of this._zones.values()) renderer.dispose();
		this._zones.clear();

		this._registerZone('my', ZONE_DECK, new DeckZoneRenderer(this._anchor('My_Deck_Anchor')));
		this._registerZone('my', ZONE_HAND, new HandZoneRenderer(this._anchor('My_Hand_Anchor')));
		this._registerZone('my', ZONE_SUPPORTING, new FieldZoneRenderer(ZONE_SUPPORTING, this._anchor('My_Supporting_Anchor'), 3));
		this._registerZone('my', ZONE_ATTACKING, new FieldZoneRenderer(ZONE_ATTACKING, this._anchor('My_Attacking_Anchor'), 2));
		this._registerZone('my', ZONE_GRAVEYARD, new GraveyardZoneRenderer(this._anchor('My_Graveyard_Anchor')));

		this._registerZone('opp', ZONE_DECK, new DeckZoneRenderer(this._anchor('Opp_Deck_Anchor')));
		this._registerZone('opp', ZONE_HAND, new HandZoneRenderer(this._anchor('Opp_Hand_Anchor')));
		this._registerZone('opp', ZONE_SUPPORTING, new FieldZoneRenderer(ZONE_SUPPORTING, this._anchor('Opp_Supporting_Anchor'), 3));
		this._registerZone('opp', ZONE_ATTACKING, new FieldZoneRenderer(ZONE_ATTACKING, this._anchor('Opp_Attacking_Anchor'), 2));
		this._registerZone('opp', ZONE_GRAVEYARD, new GraveyardZoneRenderer(this._anchor('Opp_Graveyard_Anchor')));
	}

	private _registerZone(perspective: 'my' | 'opp', zone: Zone, renderer: ZoneRenderer): void {
		this._zones.set(this._zoneKey(perspective, zone), renderer);
	}

	getMyRenderer(zone: Zone): ZoneRenderer | undefined {
		return this._zones.get(this._zoneKey('my', zone));
	}

	getOppRenderer(zone: Zone): ZoneRenderer | undefined {
		return this._zones.get(this._zoneKey('opp', zone));
	}

	private _anchor(name: string): TransformNode {
		const node = this._scene.getTransformNodeByName(name);
		if (!node) throw new Error(`AnimationManager: missing required anchor node "${name}" in scene`);
		return node;
	}

	// ====================================================================
	// Board building
	// ====================================================================

	private async _buildBoard(data: GameStartedEventData): Promise<void> {
		const myId = this._myPlayerId;
		const oppId = this._opponentId;
		const DELAY_MS = 100;
		const allPromises: Promise<void>[] = [];

		for (const ownerId of [myId, oppId]) {
			const renderer = this._rendererFor(ownerId, ZONE_DECK);

			const deckCards = this._gatherInitialCardsInDeck(data.state, ownerId);

			for (const [i, card] of deckCards.entries()) {
				const entity = this._cardManager.getByInstanceId(card.instanceId);
				const p = new Promise<void>(resolve => {
					setTimeout(async () => {
						await renderer.addCard(entity, true);
						resolve();
					}, i * DELAY_MS);
				});

				allPromises.push(p);
			}
		}
		await Promise.all(allPromises);
	}

	private _gatherInitialCardsInDeck(state: ClientGameState, ownerId: string): ClientCard[] {
		const player = state.players[ownerId];
		const handIds = player.zones.HAND?.card_ids ?? [];
		const deckIds = player.zones.DECK?.card_ids ?? [];
		return [...handIds, ...deckIds].map((id) => state.cards[id]);
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

	private _rendererFor(ownerId: string, zone: Zone): ZoneRenderer {
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
		return ownerId === this._myPlayerId;
	}

	private _opponentFieldCenter(): Vector3 {
		const renderer = this._zones.get(this._zoneKey('opp', ZONE_ATTACKING));
		return renderer?.getEntryPosition() ?? Vector3.Zero();
	}

	private _callback(fn: () => void): GameAnimation {
		return {
			name: 'Callback',
			duration: 0,
			execute: () => { fn(); return Promise.resolve(); },
			cancel: () => { fn(); },
		};
	}
}
