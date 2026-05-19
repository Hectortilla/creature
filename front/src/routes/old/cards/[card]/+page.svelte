<script lang="ts">
    import type { Creature, Element } from '$lib/types';
	import { goto } from "$app/navigation";
    import { changeThemeTo } from '$lib/utils/changeThemeTo';
    import { onDestroy, onMount } from 'svelte';
    import { deleteCardCardsCardIdDelete } from '$lib/api';

    // Components
    import CreatureCard360 from "$lib/components/creature/Card360.svelte"
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

    const handleDeleteCard = async () => {
        if (!card) return;
        await deleteCardCardsCardIdDelete({ path: { card_id: card.id } });
        goto('/cards');
	};

    $effect(() => {
        if (card) changeThemeTo(card.first_element?.label);
        else changeThemeTo("default");
    });

    onMount (() => {
        cardContainerPosition = cardContainer?.getBoundingClientRect().top ?? 0;
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
                <CardStaticDetails card={card} elements={data.elements} variants={data.variants ?? []} />

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

            .btn-wrapper {
                width: 100%;
                padding-top: functions.rem(40);

                @include mixins.displayFlex(row, 12, flex-start, flex-start, wrap);
            }
        }
    }
</style>
