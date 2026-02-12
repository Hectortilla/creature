<script lang="ts">
	import type { DeckReadWithCards, CardReadWithRelations, DeckCreate } from '$lib/api';
	import type { Creature } from '$lib/types';
	import {
		getAllDecksDecksGet,
		getAllCardsCardsGet,
		createDeckDecksPost,
		addCardToDeckDecksDeckIdCardsCardIdPost,
		removeCardFromDeckDecksDeckIdCardsCardIdDelete,
		deleteDeckDecksDeckIdDelete
	} from '$lib/api';
	import { formatHandle } from '$lib/utils/formatHandle';
	import { onMount } from 'svelte';

	// Components
	import CreatureCard360 from '$lib/components/creature/Card360.svelte';
	import InputSearch from '$lib/components/input/Search.svelte';
	import InputText from '$lib/components/input/Text.svelte';
	import Button from '$lib/components/Button.svelte';
	import Select from '$lib/components/input/Select.svelte';

	interface PageProps {
		data: {
			decks?: DeckReadWithCards[];
		};
	}

	let { data }: PageProps = $props();

	let decks = $state<DeckReadWithCards[]>(data.decks ?? []);
	let allCards = $state<Creature[]>([]);
	let cardsLoaded = $state(false);

	// Create deck form
	let showCreateForm = $state(false);
	let newDeckName = $state('');
	let newDeckDescription = $state('');

	// Card selection for adding to deck
	let selectedDeckId = $state<number | null>(null);
	let searchTerm = $state('');
	let filterByElement = $state<number | null>(null);
	let filterByType = $state<number | null>(null);
	let filterByCharacter = $state<number | null>(null);

	// Load cards when user opens "add cards" section
	async function loadCardsIfNeeded() {
		if (!cardsLoaded && selectedDeckId !== null) {
			try {
				const response = await getAllCardsCardsGet({});
				if (response.data) {
					allCards = response.data;
					cardsLoaded = true;
				}
			} catch (err) {
				console.error('Error loading cards:', err);
			}
		}
	}

	// Watch for selectedDeckId changes to load cards
	$effect(() => {
		if (selectedDeckId !== null) {
			loadCardsIfNeeded();
		}
	});

	// Get available elements, types, and characters from cards
	let availableElements = $derived(() => {
		const elementMap = new Map();
		allCards.forEach((card) => {
			if (card.first_element) {
				elementMap.set(card.first_element.id, card.first_element);
			}
			if (card.second_element) {
				elementMap.set(card.second_element.id, card.second_element);
			}
		});
		return Array.from(elementMap.values());
	});

	let availableTypes = $derived(() => {
		const typeMap = new Map();
		allCards.forEach((card) => {
			if (card.type) {
				typeMap.set(card.type.id, card.type);
			}
		});
		return Array.from(typeMap.values());
	});

	let availableCharacters = $derived(() => {
		const characterMap = new Map();
		allCards.forEach((card) => {
			if (card.character) {
				characterMap.set(card.character.id, card.character);
			}
		});
		return Array.from(characterMap.values());
	});

	// Filter cards based on search and filters (cards can be repeated in decks)
	let filteredCards = $derived(() => {
		if (!allCards) return [];

		return allCards
			.filter((card: any) => {
				// Search filter
				const matchesSearch =
					searchTerm.trim() === '' ||
					formatHandle(card.name).includes(formatHandle(searchTerm)) ||
					String(card.code).includes(searchTerm.trim());

				// Element filter
				const matchesElement =
					filterByElement === null ||
					Number(card.first_element?.id) === filterByElement ||
					Number(card.second_element?.id) === filterByElement;

				// Type filter
				const matchesType =
					filterByType === null || Number(card.type.id) === filterByType;

				// Character filter
				const matchesCharacter =
					filterByCharacter === null || Number(card.character.id) === filterByCharacter;

				return matchesSearch && matchesElement && matchesType && matchesCharacter;
			})
			.sort((a, b) => a.code - b.code);
	});

	// Container card position
	let cardContainer = $state<HTMLElement>();
	let cardContainerPosition = $state(0);

	onMount(() => {
		cardContainerPosition = cardContainer?.getBoundingClientRect().top ?? 0;
	});

	async function handleCreateDeck() {
		if (!newDeckName.trim()) {
			alert('El nombre del mazo es obligatorio');
			return;
		}

		try {
			const deckData: DeckCreate = {
				name: newDeckName.trim(),
				description: newDeckDescription.trim() || null
			};

			const response = await createDeckDecksPost({ body: deckData });

			if (response.data) {
				decks = [...decks, response.data];
				newDeckName = '';
				newDeckDescription = '';
				showCreateForm = false;
				alert('Mazo creado con éxito');
			}
		} catch (err) {
			console.error('Error creando el mazo:', err);
			alert(`Hubo un error al crear el mazo: ${(err as Error).message}`);
		}
	}

	async function handleAddCardToDeck(deckId: number, cardId: number) {
		try {
			await addCardToDeckDecksDeckIdCardsCardIdPost({
				path: {
					deck_id: deckId,
					card_id: cardId
				}
			});

			// Refresh decks
			const response = await getAllDecksDecksGet({});
			if (response.data) {
				decks = response.data;
			}
		} catch (err) {
			console.error('Error añadiendo carta al mazo:', err);
			alert(`Hubo un error al añadir la carta: ${(err as Error).message}`);
		}
	}

	async function handleRemoveCardFromDeck(deckId: number, cardId: number) {
		try {
			await removeCardFromDeckDecksDeckIdCardsCardIdDelete({
				path: {
					deck_id: deckId,
					card_id: cardId
				}
			});

			// Refresh decks
			const response = await getAllDecksDecksGet({});
			if (response.data) {
				decks = response.data;
			}
		} catch (err) {
			console.error('Error eliminando carta del mazo:', err);
			alert(`Hubo un error al eliminar la carta: ${(err as Error).message}`);
		}
	}

	async function handleDeleteDeck(deckId: number) {
		if (!confirm('¿Estás seguro de que quieres eliminar este mazo?')) {
			return;
		}

		try {
			await deleteDeckDecksDeckIdDelete({
				path: {
					deck_id: deckId
				}
			});

			// Remove from local state
			decks = decks.filter((d) => d.id !== deckId);
			if (selectedDeckId === deckId) {
				selectedDeckId = null;
			}
			alert('Mazo eliminado con éxito');
		} catch (err) {
			console.error('Error eliminando el mazo:', err);
			alert(`Hubo un error al eliminar el mazo: ${(err as Error).message}`);
		}
	}

	function getCardCount(deck: DeckReadWithCards): number {
		return deck.cards?.length ?? 0;
	}

	function getCardCountInDeck(deckId: number, cardId: number): number {
		const deck = decks.find((d) => d.id === deckId);
		if (!deck || !deck.cards) return 0;
		return deck.cards.filter((c) => c.id === cardId).length;
	}
</script>

<div class="decks-container">
	<div class="decks-header">
		<h1>Mis Mazos</h1>
		<Button
			type="primary"
			text={showCreateForm ? 'Cancelar' : 'Crear Nuevo Mazo'}
			isDisabled={false}
			onClick={() => {
				showCreateForm = !showCreateForm;
				if (!showCreateForm) {
					newDeckName = '';
					newDeckDescription = '';
				}
			}}
		/>
	</div>

	{#if showCreateForm}
		<div class="create-deck-form">
			<h2>Crear Nuevo Mazo</h2>
			<InputText
				type="text"
				label="Nombre del Mazo"
				bind:value={newDeckName}
				error={false}
				placeholder="Ingresa el nombre del mazo"
				maxLength={255}
				minLength={1}
				isMandatory={true}
			/>
			<InputText
				type="textarea"
				label="Descripción"
				bind:value={newDeckDescription}
				error={false}
				placeholder="Ingresa una descripción (opcional)"
				maxLength={1000}
				minLength={0}
				isMandatory={false}
			/>
			<Button
				type="primary"
				text="Crear Mazo"
				isDisabled={!newDeckName.trim()}
				onClick={handleCreateDeck}
			/>
		</div>
	{/if}

	<div class="decks-list">
		{#if decks.length === 0}
			<p class="no-decks">No tienes mazos creados. ¡Crea tu primer mazo!</p>
		{:else}
			{#each decks as deck}
				<div class="deck-card">
					<div class="deck-header">
						<div class="deck-info">
							<h3>{deck.name}</h3>
							{#if deck.description}
								<p class="deck-description">{deck.description}</p>
							{/if}
							<p class="deck-count">{getCardCount(deck)} cartas</p>
						</div>
						<div class="deck-actions">
							<Button
								type="secondary"
								text={selectedDeckId === deck.id ? 'Cerrar' : 'Añadir Cartas'}
								isDisabled={false}
								onClick={() => {
									selectedDeckId = selectedDeckId === deck.id ? null : deck.id;
									searchTerm = '';
									filterByElement = null;
									filterByType = null;
									filterByCharacter = null;
								}}
							/>
							<Button
								type="secondary"
								text="Eliminar"
								isDisabled={false}
								onClick={() => handleDeleteDeck(deck.id)}
							/>
						</div>
					</div>

					{#if deck.cards && deck.cards.length > 0}
						<div class="deck-cards">
							<h4>Cartas en el mazo:</h4>
							<ul class="cards-grid" bind:this={cardContainer}>
								{#each deck.cards as card, index (index)}
									<li>
										<div class="card-wrapper">
											<CreatureCard360
												data={card as Creature}
												key={index}
												showCode={true}
												showInfo={true}
												allowLink={true}
												containerPos={cardContainerPosition}
												allowHoverEffect={true}
											/>
											<button
												class="remove-card-btn"
												onclick={() => handleRemoveCardFromDeck(deck.id, card.id)}
												aria-label="Eliminar carta del mazo"
											>
												×
											</button>
										</div>
									</li>
								{/each}
							</ul>
						</div>
					{:else}
						<p class="no-cards">Este mazo no tiene cartas aún.</p>
					{/if}
				</div>
			{/each}
		{/if}
	</div>

	{#if selectedDeckId}
		<div class="add-cards-section">
			<h2>Añadir Cartas al Mazo</h2>
			<div class="filters-container">
				<InputSearch bind:value={searchTerm} placeholder="Busca por nombre o por código" />
				{#if availableElements().length > 0}
					<Select
						showLabel={false}
						label="Elemento"
						noSelectText="Todos"
						list={availableElements()}
						iconType="image"
						isMandatory={false}
						isDisabled={false}
						bind:group={filterByElement}
					/>
				{/if}
				{#if availableTypes().length > 0}
					<Select
						showLabel={false}
						label="Tipo"
						noSelectText="Todos"
						list={availableTypes()}
						iconType="icon"
						isMandatory={false}
						isDisabled={false}
						bind:group={filterByType}
					/>
				{/if}
				{#if availableCharacters().length > 0}
					<Select
						showLabel={false}
						label="Naturaleza"
						noSelectText="Todas"
						list={availableCharacters()}
						iconType="icon"
						isMandatory={false}
						isDisabled={false}
						bind:group={filterByCharacter}
					/>
				{/if}
			</div>

			{#if filteredCards().length > 0}
				<ul class="available-cards-grid">
					{#each filteredCards() as card}
						{@const cardCount = selectedDeckId ? getCardCountInDeck(selectedDeckId, card.id) : 0}
						<li>
							<div class="card-wrapper">
								<CreatureCard360
									data={card}
									key={card.id}
									showCode={true}
									showInfo={true}
									allowLink={true}
									containerPos={cardContainerPosition}
									allowHoverEffect={true}
								/>
								<button
									class="add-card-btn"
									onclick={() => handleAddCardToDeck(selectedDeckId!, card.id)}
									aria-label="Añadir carta al mazo"
									title={cardCount > 0 ? `Ya tienes ${cardCount} copia${cardCount > 1 ? 's' : ''} en el mazo` : 'Añadir carta al mazo'}
								>
									+
								</button>
								{#if cardCount > 0}
									<span class="card-count-badge" title="{cardCount} copia{cardCount > 1 ? 's' : ''} en el mazo">
										{cardCount}
									</span>
								{/if}
							</div>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="no-cards">No hay cartas disponibles con estos filtros.</p>
			{/if}
		</div>
	{/if}
</div>

<style lang="scss">
	@use "../../lib/styles/abstracts/mixins" as mixins;
	@use "../../lib/styles/abstracts/functions" as functions;
	@use "../../lib/styles/abstracts/variables" as variables;

	.decks-container {
		@include mixins.margins;
		padding: functions.rem(20);
	}

	.decks-header {
		@include mixins.displayFlex(row, 20, space-between, center);
		margin-bottom: functions.rem(30);

		h1 {
			font-family: variables.$font-title;
			font-size: functions.rem(32);
		}
	}

	.create-deck-form {
		background-color: var(--color-pop-in-background);
		border-radius: functions.rem(16);
		padding: functions.rem(24);
		margin-bottom: functions.rem(30);
		@include mixins.displayFlex(column, 16, flex-start, stretch);

		h2 {
			font-family: variables.$font-title;
			font-size: functions.rem(24);
			margin-bottom: functions.rem(16);
		}
	}

	.decks-list {
		@include mixins.displayFlex(column, 20, flex-start, stretch);
	}

	.deck-card {
		background-color: var(--color-pop-in-background);
		border-radius: functions.rem(16);
		padding: functions.rem(24);
		@include mixins.displayFlex(column, 20, flex-start, stretch);
	}

	.deck-header {
		@include mixins.displayFlex(row, 20, space-between, flex-start);
		flex-wrap: wrap;
	}

	.deck-info {
		flex: 1;
		min-width: 200px;

		h3 {
			font-family: variables.$font-title;
			font-size: functions.rem(24);
			margin-bottom: functions.rem(8);
		}

		.deck-description {
			color: var(--color-input-text);
			opacity: 0.7;
			margin-bottom: functions.rem(8);
		}

		.deck-count {
			font-size: functions.rem(16);
			opacity: 0.6;
		}
	}

	.deck-actions {
		@include mixins.displayFlex(row, 10, flex-end, center);
		flex-wrap: wrap;
	}

	.deck-cards {
		margin-top: functions.rem(20);

		h4 {
			font-family: variables.$font-title;
			font-size: functions.rem(20);
			margin-bottom: functions.rem(16);
		}
	}

	.cards-grid,
	.available-cards-grid {
		display: grid;
		grid-template-columns: repeat(6, 1fr);
		gap: functions.rem(10);
		justify-items: center;
		align-items: start;

		@media (max-width: 1250px) {
			grid-template-columns: repeat(4, 1fr);
		}

		@media (max-width: 1000px) {
			grid-template-columns: repeat(3, 1fr);
		}

		@media (max-width: 600px) {
			grid-template-columns: repeat(2, 1fr);
		}

		li {
			perspective: 1000px;
			position: relative;
		}
	}

	.card-wrapper {
		position: relative;
		width: 100%;

		.remove-card-btn,
		.add-card-btn {
			position: absolute;
			top: functions.rem(8);
			right: functions.rem(8);
			width: functions.rem(32);
			height: functions.rem(32);
			border-radius: 50%;
			border: none;
			background-color: var(--color-button-primary-background);
			color: var(--color-button-primary-text);
			font-size: functions.rem(24);
			font-weight: bold;
			cursor: pointer;
			z-index: 10;
			@include mixins.displayFlex(row, 0, center, center);
			@include mixins.transition;

			&:hover {
				transform: scale(1.1);
				box-shadow: 0 functions.rem(4) functions.rem(8) rgba(0, 0, 0, 0.3);
			}
		}

		.remove-card-btn {
			background-color: var(--color-semantic-error, #ff4444);
		}

		.card-count-badge {
			position: absolute;
			bottom: functions.rem(8);
			right: functions.rem(8);
			background-color: var(--color-button-primary-background);
			color: var(--color-button-primary-text);
			border-radius: functions.rem(16);
			padding: functions.rem(4) functions.rem(8);
			font-size: functions.rem(12);
			font-weight: bold;
			z-index: 10;
			pointer-events: none;
		}
	}

	.add-cards-section {
		margin-top: functions.rem(40);
		padding-top: functions.rem(40);
		border-top: solid 1px var(--color-input-border);

		h2 {
			font-family: variables.$font-title;
			font-size: functions.rem(28);
			margin-bottom: functions.rem(24);
		}
	}

	.filters-container {
		@include mixins.displayFlex(row, 12, flex-start, center);
		flex-wrap: wrap;
		margin-bottom: functions.rem(24);
	}

	.no-decks,
	.no-cards {
		text-align: center;
		padding: functions.rem(40);
		opacity: 0.6;
		font-size: functions.rem(18);
	}
</style>

