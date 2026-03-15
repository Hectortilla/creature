/**
 * BoardController — event bus and raw-message router.
 *
 * Receives raw WebSocket messages from GameConnection, applies state to
 * GameStateStore, then parses events into typed signals that AnimationManager,
 * HUD components, and InteractionManager subscribe to.
 *
 * Contains NO visual / animation logic — that lives in AnimationManager.
 */

import type { Scene } from '@babylonjs/core/scene';
import type { IScript } from 'babylonjs-editor-tools';

import GameConnection from './game/GameConnection';
import { CardDefinitionCache } from './game/CardDefinitionCache';
import { GameStateStore } from './state/GameStateStore';
import type { GameMessage, ValidAction } from './game/types';
import type { Zone, TurnPhase, ClientCard, ClientGameState, ClientPlayerState } from './game/models';

import type {
	StateChangeEvents,
	StateChangeCallback,
	GameStartedEventData,
} from './state/events';

export default class BoardController implements IScript {
	static instance: BoardController | null = null;

	private _connection!: GameConnection;
	private _stateStore!: GameStateStore;
	private _cardCache!: CardDefinitionCache;

	private _listeners = new Map<keyof StateChangeEvents, Set<StateChangeCallback<any>>>();

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

		BoardController.instance = this;
		this._connection.onMessage = this._handleRawMessage;
	}

	public onUpdate(): void {}

	public onStop(): void {
		if (this._connection) this._connection.onMessage = null;
		this._listeners.clear();
		BoardController.instance = null;
	}

	// ====================================================================
	// Event bus
	// ====================================================================

	on<K extends keyof StateChangeEvents>(
		event: K,
		cb: StateChangeCallback<StateChangeEvents[K]>,
	): void {
		if (!this._listeners.has(event)) this._listeners.set(event, new Set());
		this._listeners.get(event)!.add(cb);
	}

	off<K extends keyof StateChangeEvents>(
		event: K,
		cb: StateChangeCallback<StateChangeEvents[K]>,
	): void {
		this._listeners.get(event)?.delete(cb);
	}

	private _emit<K extends keyof StateChangeEvents>(
		event: K,
		data: StateChangeEvents[K],
	): void {
		console.log('BoardController: event', event, data);

		const set = this._listeners.get(event);
		if (!set) return;
		for (const cb of set) cb(data);
	}

	// ====================================================================
	// Raw WebSocket message routing
	// ====================================================================

	private _handleRawMessage = (message: GameMessage): void => {
		if (message.data?.success === false) {
			console.error('BoardController: game action failed', message);
			return;
		}

		this._registerCardsFromEvents(message.data);
		const d = message.data;

		// 1. Apply authoritative state
		if (d.game_state)
			this._stateStore.applyServerState(d.game_state as Record<string, unknown>);

		// 2. Game started (must fire before granular events so subscribers can initialize)
		if (message.type === 'game_started')
			this._emit('gameStarted', this._buildGameStartedPayload());

		// 3. Emit typed events for animations + HUD
		if (d.events)
			this.emitGameEvents(d.events as Record<string, unknown>[]);

		// 4. Valid actions
		if (d.valid_actions) {
			const mine = (d.valid_actions as ValidAction[]).filter(
				(a) => a.player_id === this._stateStore.myPlayerId,
			);
			this._stateStore.updateValidActions(mine);
			this._emit('validActionsChanged', { actions: mine, isMyTurn: this._stateStore.isMyTurn });
		}
	};

	private _registerCardsFromEvents(data: Record<string, unknown>): void {
		const events = data.events as Record<string, unknown>[] | undefined;
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
	// Game event emission
	// ====================================================================

	emitGameEvents(events: Record<string, unknown>[]): void {
		for (const raw of events) {
			this._dispatchEvent(raw);
		}
	}

	private _dispatchEvent(raw: Record<string, unknown>): void {
		const eventType = raw.event_type as string | undefined;
		if (!eventType) return;

		switch (eventType) {
			case 'CardDrawnEvent':       return this._handleCardDrawn(raw);
			case 'CardMovedEvent':       return this._handleCardMoved(raw);
			case 'CardPlayedEvent':      return this._handleCardPlayed(raw);
			case 'CardPromotedEvent':    return this._handleCardPromoted(raw);
			case 'CardSwappedEvent':     return this._handleCardSwapped(raw);
			case 'CardAssociatedEvent':  return this._handleCardAssociated(raw);
			case 'CardEvolvedEvent':     return this._handleCardEvolved(raw);
			case 'AttackDeclaredEvent':  return this._handleAttackDeclared(raw);
			case 'DamageDealtEvent':     return this._handleDamageDealt(raw);
			case 'CardDestroyedEvent':   return this._handleCardDestroyed(raw);
			case 'ElementsConsumedEvent': return this._handleElementsConsumed(raw);
			case 'ElementsRestoredEvent': return this._handleElementsRestored(raw);
			case 'TurnStartedEvent':     return this._handleTurnStarted(raw);
			case 'TurnEndedEvent':       return this._handleTurnEnded(raw);
			case 'PhaseChangedEvent':    return this._handlePhaseChanged(raw);
			case 'GameStartedEvent':     break; // handled at message level
			case 'GameEndedEvent':       return this._handleGameEnded(raw);
			case 'NoDefenderEvent':      return this._handleNoDefender(raw);
			case 'EffectTriggeredEvent': return this._handleEffectTriggered(raw);
			case 'EffectAppliedEvent':   return this._handleEffectApplied(raw);
			default:
				console.warn(`BoardController: unhandled event type "${eventType}"`);
		}
	}

	// ====================================================================
	// Pure-emit event handlers (no state mutation)
	// ====================================================================

	private _opponentDrawCounter = 0;

	private _handleCardDrawn(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		let instanceId = raw.instance_id as string;
		const cardId = (raw.card_id as number) ?? 0;
		const isOwn = playerId === this._stateStore.myPlayerId;

		if (isOwn) {
			const card = this._stateStore.getCard(instanceId)!;
			this._emit('cardAdded', card);
		} else {
			instanceId = `opponent-draw-${playerId}-${++this._opponentDrawCounter}`;
			this._emit('cardAdded', {
				instanceId, cardId, ownerId: playerId,
				name: '', zone: 'HAND' as Zone,
				currentHealth: 0, maxHealth: 0,
				physicalDefence: 0, magicDefence: 0,
				isAlive: true, faceUp: false,
			} satisfies ClientCard);
		}


		this._emit('cardMoved', {
			instanceId,
			ownerId: playerId,
			fromZone: 'DECK' as Zone,
			toZone: 'HAND' as Zone,
		});
	}

	private _handleCardMoved(raw: Record<string, unknown>): void {
		const fromZone = raw.from_zone as Zone;
		const toZone = raw.to_zone as Zone;
		if (!fromZone || !toZone) return;

		this._emit('cardMoved', {
			instanceId: raw.instance_id as string,
			ownerId: raw.owner_id as string,
			fromZone,
			toZone,
		});
	}

	private _handleCardPlayed(raw: Record<string, unknown>): void {
		this._emit('cardMoved', {
			instanceId: raw.instance_id as string,
			ownerId: raw.player_id as string,
			fromZone: 'HAND' as Zone,
			toZone: 'SUPPORTING' as Zone,
		});
	}

	private _handleCardPromoted(raw: Record<string, unknown>): void {
		this._emit('cardMoved', {
			instanceId: raw.instance_id as string,
			ownerId: raw.player_id as string,
			fromZone: 'SUPPORTING' as Zone,
			toZone: 'ATTACKING' as Zone,
		});
	}

	private _handleCardSwapped(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const supportingId = raw.supporting_card_id as string;
		const attackingId = raw.attacking_card_id as string;

		this._emit('cardsSwapped', { ownerId: playerId, supportingId, attackingId });

		this._emit('cardMoved', {
			instanceId: supportingId, ownerId: playerId,
			fromZone: 'SUPPORTING' as Zone, toZone: 'ATTACKING' as Zone,
		});
		this._emit('cardMoved', {
			instanceId: attackingId, ownerId: playerId,
			fromZone: 'ATTACKING' as Zone, toZone: 'SUPPORTING' as Zone,
		});
	}

	private _handleCardAssociated(raw: Record<string, unknown>): void {
		const sourceZone = (raw.source_zone as Zone) ?? null;

		if (sourceZone) {
			this._emit('cardMoved', {
				instanceId: raw.association_card_id as string,
				ownerId: raw.player_id as string,
				fromZone: sourceZone,
				toZone: 'SUPPORTING' as Zone,
			});
		}

		this._emit('cardAssociated', {
			playerId: raw.player_id as string,
			associationCardId: raw.association_card_id as string,
			targetCardId: raw.target_card_id as string,
			cardId: (raw.card_id as number) ?? 0,
			sourceZone: sourceZone as string | null,
		});
	}

	private _handleCardEvolved(raw: Record<string, unknown>): void {
		this._emit('cardEvolved', {
			playerId: raw.player_id as string,
			baseCardId: raw.base_card_id as string,
			evolutionCardId: raw.evolution_card_id as string,
			cardId: (raw.card_id as number) ?? 0,
			baseCardName: (raw.base_card_name as string) ?? '',
			evolutionCardName: (raw.evolution_card_name as string) ?? '',
		});
	}

	private _handleAttackDeclared(raw: Record<string, unknown>): void {
		this._emit('attackDeclared', {
			attackerOwnerId: raw.attacker_owner_id as string,
			attackerId: raw.attacker_id as string,
			targetId: raw.target_id as string,
			attackId: (raw.attack_id as number) ?? 0,
			attackName: (raw.attack_name as string) ?? '',
		});
	}

	private _handleDamageDealt(raw: Record<string, unknown>): void {
		const finalDamage = (raw.final_damage as number) ?? 0;
		const remainingHealth = (raw.remaining_health as number) ?? 0;

		this._emit('cardHealthChanged', {
			instanceId: raw.target_id as string,
			oldHealth: remainingHealth + finalDamage,
			newHealth: remainingHealth,
			maxHealth: (raw.max_health as number) ?? remainingHealth + finalDamage,
		});
	}

	private _handleCardDestroyed(raw: Record<string, unknown>): void {
		const instanceId = raw.instance_id as string;
		const ownerId = raw.owner_id as string;
		const card = this._stateStore.getCard(instanceId);
		const fromZone = card?.zone ?? ('ATTACKING' as Zone);

		this._emit('cardDestroyed', {
			instanceId,
			ownerId,
			cardName: (raw.card_name as string) ?? '',
		});

		this._emit('cardMoved', {
			instanceId,
			ownerId,
			fromZone,
			toZone: 'GRAVEYARD' as Zone,
		});
	}

	private _handleElementsConsumed(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const pool = this._getPlayerPool(playerId);
		this._emit('elementsConsumed', {
			playerId,
			elements: (raw.elements as Record<string, number>) ?? {},
			currentPool: pool.elements,
			maxPool: pool.maxElements,
		});
	}

	private _handleElementsRestored(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const pool = this._getPlayerPool(playerId);
		this._emit('elementsRestored', {
			playerId,
			elements: (raw.elements as Record<string, number>) ?? {},
			currentPool: pool.elements,
			maxPool: pool.maxElements,
		});
	}

	private _handleTurnStarted(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		this._emit('turnChanged', {
			playerId,
			turnNumber: (raw.turn_number as number) ?? 0,
			isFirstTurn: (raw.is_first_turn as boolean) ?? false,
			isMyTurn: playerId === this._stateStore.myPlayerId,
		});
	}

	private _handleTurnEnded(raw: Record<string, unknown>): void {
		this._emit('turnEnded', {
			playerId: raw.player_id as string,
			turnNumber: (raw.turn_number as number) ?? 0,
		});
	}

	private _handlePhaseChanged(raw: Record<string, unknown>): void {
		const toPhase = raw.to_phase as TurnPhase;
		if (!toPhase) return;
		this._emit('phaseChanged', {
			fromPhase: raw.from_phase as TurnPhase,
			toPhase,
			playerId: raw.player_id as string,
		});
	}

	private _handleGameEnded(raw: Record<string, unknown>): void {
		this._emit('gameOver', {
			winnerId: (raw.winner_id as string) ?? '',
			loserId: (raw.loser_id as string) ?? '',
			reason: (raw.reason as string) ?? '',
		});
	}

	private _handleNoDefender(raw: Record<string, unknown>): void {
		this._emit('noDefender', {
			defenderId: (raw.defender_id as string) ?? '',
			attackerId: (raw.attacker_id as string) ?? '',
			mustDefend: (raw.must_defend as boolean) ?? false,
			gameLost: (raw.game_lost as boolean) ?? false,
		});
	}

	private _handleEffectTriggered(raw: Record<string, unknown>): void {
		this._emit('effectTriggered', {
			sourceCardId: (raw.source_card_id as string) ?? '',
			effectId: (raw.effect_id as string) ?? '',
			effectName: (raw.effect_name as string) ?? '',
			triggerReason: (raw.trigger_reason as string) ?? '',
		});
	}

	private _handleEffectApplied(raw: Record<string, unknown>): void {
		this._emit('effectApplied', {
			effectId: (raw.effect_id as string) ?? '',
			affectedCardIds: (raw.affected_card_ids as string[]) ?? [],
			description: (raw.description as string) ?? '',
		});
	}

	// ====================================================================
	// Helpers
	// ====================================================================

	private _buildGameStartedPayload(): GameStartedEventData {
		const state = this._stateStore.state!;
		const myId = this._stateStore.myPlayerId;
		const oppId = this._stateStore.getOpponentId() ?? '';
		const myPlayer = state.players[myId];

		return {
			state,
			myPlayerId: myId,
			opponentId: oppId,
			isMyTurn: state.activePlayerId === myId,
			currentPhase: state.currentPhase,
			deckSize: state.config?.deck_size ?? 0,
			myElementPool: {
				elements: myPlayer?.elementPool?.elements ?? {},
				maxElements: myPlayer?.elementPool?.max_elements ?? {},
			},
		};
	}

	private _getPlayerPool(playerId: string): { elements: Record<string, number>; maxElements: Record<string, number> } {
		const player = this._stateStore.state?.players[playerId];
		return {
			elements: (player?.elementPool?.elements ?? {}) as Record<string, number>,
			maxElements: (player?.elementPool?.max_elements ?? {}) as Record<string, number>,
		};
	}
}
