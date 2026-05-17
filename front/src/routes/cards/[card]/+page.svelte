<script lang="ts">
    import type { Creature, Element } from '$lib/types';
	import { goto } from "$app/navigation";
    import { changeThemeTo } from '$lib/utils/changeThemeTo';
    import { onDestroy, onMount } from 'svelte';
    import { deleteCardCardsCardIdDelete } from '$lib/api';

    // Components
    import CreatureCard360 from "$lib/components/creature/Card360.svelte"
    import Divider from "$lib/components/Divider.svelte"
    import Button from "$lib/components/Button.svelte"
    import CardStaticDetails from "$lib/components/cards/CardStaticDetails.svelte"

    interface PageProps {
        data: {
            card?: string | number;
            cards?: Creature[];
            variants: Creature[];
            elements: Element[];
        };
    }
    let { data }: PageProps = $props();

    let card = $derived.by(() => data.cards && data.cards.length === 1 ? data.cards[0] : null);

    /// Creature card
    let cardContainer = $state<HTMLElement>();
    let cardContainerPosition = $state(0);
    let cardEvoContainer = $state<HTMLElement>();
    let cardEvoContainerPosition = $state(0);
    let cardVariantsContainer = $state<HTMLElement>();
    let cardVariantsContainerPosition = $state(0);

    const handleDeleteCard = async () => {
        if (!card) return;
        await deleteCardCardsCardIdDelete({ path: { card_id: card.id } });
        goto('/cards');
	};

    $effect(() => {
        if (card) changeThemeTo(card.first_element?.label);
        else changeThemeTo("default");
    });

    /**
     * Genera ramas de pre-evoluciones y evoluciones a partir de una carta.
     */
    const getAllEvolutionLines = (card: Creature): Creature[][] => {
        // --- Subir todas las posibles cadenas de preevoluciones ---
        const getPreChains = (c: Creature): Creature[][] => {
            if (!c.is_evolution) return [[c]]; // no tiene pre, arranca aquí

            const prev = c.is_evolution;
            let chains: Creature[][] = [];

            if (Array.isArray(prev)) {
                for (const p of prev) {
                    for (const chain of getPreChains(p as Creature)) {
                        chains.push([...chain, c]);
                    }
                }
            } else {
                for (const chain of getPreChains(prev as Creature)) {
                    chains.push([...chain, c]);
                }
            }

            return chains;
        };

        // --- Bajar todas las posibles cadenas de evoluciones ---
        const getNextChains = (c: Creature): Creature[][] => {
            if (!c.next_evolutions || c.next_evolutions.length === 0) {
                return [[c]]; // no tiene next, termina aquí
            }

            let chains: Creature[][] = [];
            for (const n of c.next_evolutions) {
                for (const chain of getNextChains(n as Creature)) {
                    chains.push([c, ...chain]);
                }
            }
            return chains;
        };

        // --- Combinar pre + next ---
        const preChains = getPreChains(card);   // todas las cadenas de previas hasta `card`
        const allLines: Creature[][] = [];

        for (const preChain of preChains) {
            const last = preChain[preChain.length - 1]; // el `card` en esa rama
            const nextChains = getNextChains(last);
            for (const nextChain of nextChains) {
                // evitamos duplicar `card` porque ya está en ambas
                allLines.push([...preChain.slice(0, -1), ...nextChain]);
            }
        }

        return allLines;
    };

    const evoLines = $derived.by(() => card ? getAllEvolutionLines(card) : []);

    onMount (() => {
        cardContainerPosition = cardContainer?.getBoundingClientRect().top ?? 0;
        cardEvoContainerPosition = cardEvoContainer?.getBoundingClientRect().top ?? 0;
        cardVariantsContainerPosition = cardVariantsContainer?.getBoundingClientRect().top ?? 0;
    });

    onDestroy(() => {
        changeThemeTo("default");
    });
</script>

{#if data.cards && data.card}
    {#if data.cards.length > 1}
        <div class="cards-multiple-container">
            <h2>Hay multiples cartas para <span>{data.cards[0].name}</span></h2>
            <ul class="card-gallery" bind:this={cardContainer}>
                {#each data.cards as cardItem,i}
                    <CreatureCard360
                        data={cardItem}
                        key={i}
                        showCode={true}
                        showInfo={true}
                        allowLink= {true}
                        allowHoverEffect={true}
                        containerPos={cardContainerPosition}
                    />
                {/each}
            </ul>
        </div>
    {:else if card} 
        <div class="card-page-container">
            <div class="card-wrapper" bind:this={cardContainer}>
                <CreatureCard360
                    data={card}
                    key={1}
                    showCode={true}
                    showInfo={false}
                    allowLink= {false}
                    allowHoverEffect={true}
                    containerPos={cardContainerPosition}
                />
            </div>
            <div class="form-group">
                <CardStaticDetails card={card} elements={data.elements} />

                {#if evoLines.length > 0 && evoLines[0].length > 1}
                    <Divider title={evoLines.length > 1 ? `Líneas evolutivas` : `Línea evolutiva`} hasMargins={false}></Divider>
                    <div class="evo-line-container" bind:this={cardEvoContainer}>
                        {#each evoLines as line, lineI}
                            <div class="evo-line-wrapper">
                                {#each line as item,i}
                                    <div class="card-item" class:selected={item.code === card.code}>
                                        <CreatureCard360
                                            data={item}
                                            key={lineI * 10 + i}
                                            showCode={item.code !== card.code}
                                            showInfo={false}
                                            showEvolutionCode={false}
                                            allowLink= {item.code !== card.code}
                                            allowHoverEffect={item.code !== card.code}
                                            containerPos={cardEvoContainerPosition}
                                        />
                                        <svg xmlns="http://www.w3.org/2000/svg" width="334" height="378" viewBox="0 0 334 378" fill="none">
                                            <path d="M323.111 171.679C336.445 179.377 336.445 198.622 323.111 206.32L30.6919 375.149C17.3586 382.847 0.691878 373.224 0.691879 357.828L0.691894 20.1715C0.691894 4.77545 17.3586 -4.84709 30.6919 2.85091L323.111 171.679Z" fill="currentColor"/>
                                        </svg>
                                    </div>
                                {/each}
                            </div>
                        {/each}
                    </div>
                {/if}
                {#if data.variants && data.variants.length > 1}
                    <Divider title={data.variants.length > 1 ? `Variantes` : `Variante`} hasMargins={false}></Divider>
                    <div class="gallery-cards" bind:this={cardVariantsContainer}>
                        {#each data.variants as variant,i}
                            {#if variant.code !== card.code}
                                <CreatureCard360
                                    data={variant}
                                    key={i}
                                    showCode={true}
                                    showInfo={true}
                                    showEvolutionCode={true}
                                    allowLink= {true}
                                    allowHoverEffect={true}
                                    containerPos={cardVariantsContainerPosition}
                                />
                            {/if}
                        {/each}
                    </div>
                {/if}
                <div class="btn-wrapper">
                    <Button type="primary" text="Editar carta" link={`/cards/${card.code}/edit`} isDisabled={false} />
                    <Button type="secondary" text="Borrar carta" onClick={handleDeleteCard} isDisabled={false} />
                </div>
            </div>
        </div>
        
    {/if}
{:else}
    <p>Card not found</p>
{/if}


<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .cards-multiple-container {
        width: 100%;
        padding-top: functions.rem(60);

        @include mixins.displayFlex(column, 40, center, center, nowrap);
        @include mixins.margins;

        h2 {
            font-size: functions.rem(28);
            font-family: variables.$font-title;
            font-weight: 300;
        }
        .card-gallery {
            perspective: 1000px;
           @include mixins.displayFlex(row, 20, center, flex-start, nowrap); 
        }
    }

    .card-page-container {
        width: 100%;
        padding-top: functions.rem(60);

        @include mixins.displayFlex(row, 40, center, flex-start, nowrap);
        @include mixins.margins;

        @media (max-width: 800px) {
            flex-direction: column;
            align-items: center;
        }

        .card-wrapper {
            position: sticky;
            top: functions.rem(40);
            left: 0;
            width: 90dvw;
            max-width: functions.rem(300);
            perspective: 1000px;
            z-index: 0;

            @media (max-width: 800px) {
                position: relative;
                top: inherit;
                left: inherit;
                width: 70dvw;
            }
        }

        .form-group {
            width: 100%;
            max-width: functions.rem(600);
            padding: functions.rem(10) 0;

            @include mixins.displayFlex(column, 28, flex-start, flex-start, wrap);

            .evo-line-container {
                @include mixins.displayFlex(column, 60, flex-start, flex-start, nowrap);

                .evo-line-wrapper {
                    @include mixins.displayFlex(row, 60, flex-start, center, nowrap);

                    .card-item {
                        perspective: 1000px;
                        position: relative;
                        flex: 1;
                        max-width: functions.rem(160);

                        &.selected {
                            flex: .8;
                            max-width: functions.rem(120);
                        }

                        svg {
                            position: absolute;
                            top: 50%;
                            right: 0;
                            transform: translateY(-50%) translateX(150%);
                            width: functions.rem(30);
                            height: functions.rem(30);
                            color: var(--color-divider-bar);
                            z-index: -1;
                            pointer-events: none;
                            fill-opacity: .6;
                        }

                        &:last-child svg{
                            display: none;
                        }
                    }
                }
            }

            .gallery-cards {
                perspective: 1000px;
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: functions.rem(20);
            }

            .btn-wrapper {
                width: 100%;
                padding-top: functions.rem(40);

                @include mixins.displayFlex(row, 12, flex-start, flex-start, wrap);
            }
        }
    }
</style>
