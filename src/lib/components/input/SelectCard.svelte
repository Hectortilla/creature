<script lang="ts">
    import type { CardCreature } from '$lib/types';
    import { formatHandle } from '$lib/utils/formatHandle';
    import { blur } from "svelte/transition"

    // Components
    import CreatureCard360 from "$lib/components/creature/Card360.svelte"
    import Button from "$lib/components/Button.svelte"
    import InputSearch from "$lib/components/input/Search.svelte"

    interface Props {
        cards: CardCreature[];
        buttonText: string,
        group: number | null,
        isDisabled: boolean
    }
    let {
        cards,
        buttonText,
        group = $bindable(0),
        isDisabled = false

    }: Props = $props();

    let popInIsOpen = $state(false);

    function openPopIn() {
        popInIsOpen = true;
        document.body.classList.add("no-scroll");
    }

    function closePopIn() {
        popInIsOpen = false;
        document.body.classList.remove("no-scroll");
    }

    let selectedCardName = $derived.by(() => 
        (cards && group ? cards?.find((cards): cards is CardCreature => 'code' in cards && cards.code === group)?.name ?? "No seleccionado" : "No seleccionado")
    );

    /**
     * Search cards
     */
    let searchTerm = $state("");

    let filteredCards = $derived(() => {
        if (!cards) return [];
        let filterCards: any[] = cards;

        // Search input
        const searching = searchTerm.trim() !== "";

        if (searching) {
            filterCards = cards.filter((card: any) =>
                formatHandle(card.name).includes(formatHandle(searchTerm)) ||
                formatHandle(card.code).includes(formatHandle(searchTerm))
            );
        }

        return filterCards;

    });
</script>

<Button
    type="secondary"
    text={buttonText}
    isDisabled={isDisabled}
    onClick={() => {openPopIn()}}
/>

{#if popInIsOpen}
    <div transition:blur class="pop-in">
        <div class="wrapper">
            <div class="filters-container">
                <InputSearch bind:value={searchTerm} placeholder="Busca por nombre o por código"/> 
            </div>
            {#if filteredCards().length > 0}
                <ul class="cards-gallery">
                    {#each filteredCards() as card, i}
                        <li>
                            <input
                                type="radio"
                                name={formatHandle(buttonText)}
                                id={formatHandle(card.name)}
                                value={card.code}
                                bind:group={group}
                            >
                            <label for={formatHandle(card.name)}>
                                <CreatureCard360
                                    data={card}
                                    key={i}
                                    allowLink={false}
                                    showInfo={false}
                                    showCode={true}
                                    allowHoverEffect={false}
                                    containerPos={0}
                                />
                            </label>
                        </li>
                    {/each}
                </ul>
            {:else}
                <div class="empty">
                    <p>No se han encontrado cartas</p>
                </div> 
            {/if}
            <div class="btn-wrapper">
                <Button
                    type="secondary"
                    text="Cancelar"
                    isDisabled={false}
                    onClick={() => {group = 0; closePopIn()}}
                />
                {#if group !== 0 && group !== null}
                    <Button
                        type="primary"
                        text={`Seleccionar: ${selectedCardName}`}
                        isDisabled={false}
                        onClick={() => {closePopIn()}}
                    />
                {/if}
            </div>
        </div>
    </div>
{/if}

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .pop-in {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: var(--color-pop-in-background);
        backdrop-filter: blur(functions.rem(26));
        z-index: 10;

        @include mixins.displayFlex(column, 20, center, center, nowrap);
        @include mixins.margins;

        .wrapper {
            position: relative;
            width: 100%;
            height: 90%;
            max-width: functions.rem(1200);
            background-color: var(--color-background);
            border-radius: functions.rem(20);

            @include mixins.displayFlex(column, 20, flex-start, flex-start, nowrap);

            .filters-container {
                width: 100%;
                max-width: functions.rem(400);
                position: absolute;
                top: functions.rem(20);
                left: 50%;
                transform: translateX(-50%);
                padding: 0 functions.rem(20);
                z-index: 1;
            }

            .empty {
                width: 100%;
                height: 100%;

                @include mixins.displayFlex(column, 0, center, center, nowrap);

                p {
                    color: var(--color-input-label)
                }
            }

            ul.cards-gallery {
                width: 100%;
                overflow-y: auto;
                display: grid;
                grid-template-columns: repeat(5,1fr);
                gap: functions.rem(4);
                padding: functions.rem(80) functions.rem(20) functions.rem(20) functions.rem(20);

                @media (max-width: 1300px) {
                    grid-template-columns: repeat(4, 1fr);
                }
                @media (max-width: 800px) {
                    grid-template-columns: repeat(3, 1fr);
                }
                @media (max-width: 600px) {
                    grid-template-columns: repeat(2, 1fr);
                }

                li {
                    input {display: none;}
                    label {
                        height: 100%;
                        display: block;
                        padding: functions.rem(4);
                        border-radius: functions.rem(10);
                        border: solid 1px transparent;
                        cursor: pointer;
                        will-change: border-color, box-shadow;

                        @include mixins.displayFlex(column, 0 ,center, center, nowrap);
                        @include mixins.transition;
                    }

                    input:checked + label{
                        border-color: var(--color-input-button-light-top);
                        box-shadow:
                            0 0 functions.rem(10) functions.rem(-4) var(--color-input-button-light-top) inset,
                            0 0 functions.rem(10) functions.rem(-4) var(--color-input-button-light-top);
                    }
                }

            }

            .btn-wrapper {
                position: absolute;
                left: 50%;
                bottom: functions.rem(40);
                transform: translateX(-50%);

                @include mixins.displayFlex(row, 12, flex-start, flex-start, nowrap);
            }
        }
    }
</style>