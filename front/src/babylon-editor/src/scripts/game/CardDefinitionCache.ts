/**
 * CardDefinitionCache — fetches all card definitions from the REST API
 * and provides lookups by database card_id or game instance_id.
 *
 * Singleton. Initialized once at game start with the API base URL and auth token.
 */

export interface CardDefinition {
	id: number;
	name: string;
	code: number;
	handle: string;
	description?: string | null;
	image?: string | null;
	overlay_image?: string | null;
	health?: number | null;
	physical_defence?: number | null;
	magic_defence?: number | null;
	first_element_id?: number | null;
	second_element_id?: number | null;
	first_attack_id?: number | null;
	second_attack_id?: number | null;
	ability_id?: number | null;
	association_id?: number | null;
	is_evolution_id?: number | null;
	first_element?: Record<string, unknown> | null;
	second_element?: Record<string, unknown> | null;
	first_attack?: Record<string, unknown> | null;
	second_attack?: Record<string, unknown> | null;
	ability?: Record<string, unknown> | null;
	association?: Record<string, unknown> | null;
	strengths?: number[] | null;
	weaknesses?: number[] | null;
	[key: string]: unknown;
}

export class CardDefinitionCache {
	static instance: CardDefinitionCache | null = null;

	private _definitions = new Map<number, CardDefinition>();
	private _instanceToCardId = new Map<string, number>();
	private _initialized = false;
	private _initPromise: Promise<void> | null = null;

	static getOrCreate(): CardDefinitionCache {
		if (!CardDefinitionCache.instance) {
			CardDefinitionCache.instance = new CardDefinitionCache();
		}
		return CardDefinitionCache.instance;
	}

	get initialized(): boolean {
		return this._initialized;
	}

	/**
	 * Fetch all card definitions from the REST API.
	 * Converts the WebSocket URL to an HTTP URL automatically.
	 */
	async initialize(wsUrl: string, token: string): Promise<void> {
		if (this._initialized) return;
		if (this._initPromise) return this._initPromise;

		this._initPromise = this._fetch(wsUrl, token);
		await this._initPromise;
	}

	private async _fetch(wsUrl: string, token: string): Promise<void> {
		const httpBase = wsUrl.replace(/^ws(s?):\/\//, "http$1://");

		const response = await fetch(`${httpBase}/cards`, {
			headers: { Authorization: `Bearer ${token}` },
		});

		if (!response.ok) {
			console.error(`CardDefinitionCache: failed to fetch cards (${response.status})`);
			return;
		}

		const cards: CardDefinition[] = await response.json();
		for (const card of cards) {
			this._definitions.set(card.id, card);
		}
		this._initialized = true;
	}

	/** Register the mapping from a game instance_id to a database card_id. */
	registerInstance(instanceId: string, cardId: number): void {
		if (cardId > 0) {
			this._instanceToCardId.set(instanceId, cardId);
		}
	}

	/** Look up a card definition by database id. */
	getByCardId(cardId: number): CardDefinition | undefined {
		return this._definitions.get(cardId);
	}

	/** Look up a card definition by game instance_id (requires prior registerInstance call). */
	getByInstanceId(instanceId: string): CardDefinition | undefined {
		const cardId = this._instanceToCardId.get(instanceId);
		return cardId !== undefined ? this._definitions.get(cardId) : undefined;
	}

	/** Get the database card_id for an instance_id, or undefined if unknown. */
	getCardIdForInstance(instanceId: string): number | undefined {
		return this._instanceToCardId.get(instanceId);
	}

	/** Number of card definitions loaded. */
	get size(): number {
		return this._definitions.size;
	}

	dispose(): void {
		this._definitions.clear();
		this._instanceToCardId.clear();
		this._initialized = false;
		this._initPromise = null;
		CardDefinitionCache.instance = null;
	}
}
