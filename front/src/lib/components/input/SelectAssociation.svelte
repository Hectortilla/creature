<script lang="ts">
    import type { Association } from '$lib/types';
    import { formatHandle } from '$lib/utils/formatHandle';
    import { blur, slide } from "svelte/transition"

    // Components
    import CardAssociation from "$lib/components/cards/Association.svelte"
    import Button from "$lib/components/Button.svelte"
    import InputSearch from "$lib/components/input/Search.svelte"

    // Icons
    import plusIcon from "$lib/assets/icons/plus.svg?raw"

    interface Props {
        associations: Association[];
        buttonText: string,
        group: number | null,
        isDisabled: boolean
    }
    let {
        associations,
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

    let selectedAssociationName = $derived.by(() => 
        (associations && group ? associations?.find((associations): associations is Association => 'code' in associations && associations.code === group)?.name ?? "No seleccionado" : "No seleccionado")
    );

    let selectedAssociation = $derived.by(() => 
        associations.find(a => a.code === group)
    );

    /**
     * Search cards
     */
    let searchTerm = $state("");

    let filteredAssociations = $derived(() => {
        if (!associations) return [];
        let filterAssociations: any[] = associations;

        // Search input
        const searching = searchTerm.trim() !== "";

        if (searching) {
            filterAssociations = associations.filter((ability: any) =>
                formatHandle(ability.name).includes(formatHandle(searchTerm)) ||
                formatHandle(ability.code).includes(formatHandle(searchTerm))
            );
        }

        return filterAssociations;

    });

    function deleteAbility() {
        selectedAssociation = undefined;
        group = null;
    };
</script>

{#if selectedAssociation === null || selectedAssociation === undefined}
    <button
        transition:slide
        class="add-attack"
        class:disabled={isDisabled}
        aria-label="Añadir habilidad"
        onclick={() => {openPopIn()}}
        disabled={isDisabled}
    >
        <span class="icon">
            {@html plusIcon}
        </span>
        <p>{buttonText}</p>
    </button>
{/if}
{#if selectedAssociation !== null && selectedAssociation !== undefined}
    <div class="preview-attack" transition:slide>
        <CardAssociation data={selectedAssociation} allowLink={false}/>
        <button aria-label="Borrar habilidad" onclick={() => {deleteAbility()}}>
            <span>{@html plusIcon}</span>
        </button>
    </div>
{/if}

{#if popInIsOpen}
    <div transition:blur class="pop-in">
        <div class="wrapper">
            <div class="filters-container">
                <InputSearch bind:value={searchTerm} placeholder="Busca por nombre o por código"/> 
            </div>
            {#if filteredAssociations().length > 0}
                <ul class="cards-gallery">
                    {#each filteredAssociations() as attack}
                        <li>
                            <input
                                type="radio"
                                name={formatHandle(buttonText)}
                                id={formatHandle(attack.name)}
                                value={attack.code}
                                bind:group={group}
                            >
                            <label for={formatHandle(attack.name)}>
                                <CardAssociation
                                    data={attack}
                                    allowLink={false}
                                    showDescription={true}
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
                        text={`Seleccionar: ${selectedAssociationName}`}
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

    button.add-attack {
        width: 100%;
        border: solid 1px var(--color-pop-in-background);
        border-radius: functions.rem(12);
        color: var(--color-input-label);
        padding: functions.rem(40);
        cursor: pointer;

        @include mixins.displayFlex(row, 6, center, center, nowrap);
        @include mixins.transition;

        &:hover {
            background-color: var(--color-pop-in-background);
        }

        p {
            font-family: variables.$font-title;
            font-size: functions.rem(22);
        }

        .icon {
            width: functions.rem(20);
            height: functions.rem(20);
        }

        &:disabled, &.disabled {
            pointer-events: none;
            cursor: default;
            background-color: var(--color-pop-in-background);
            opacity: .6;

            p, .icon{
                opacity: .6;
            }
        }
    }

    .preview-attack {
        width: 100%;
        @include mixins.displayFlex(row, 6, flex-start, stretch, nowrap);

        button {
            width: functions.rem(40);
            background-color: var(--color-pop-in-background);
            border-radius: functions.rem(12);
            padding: functions.rem(12);
            cursor: pointer;

            @include mixins.displayFlex(column, 0, center, center, nowrap);

            span {
                transform: rotate(45deg);
                color: var(--color-input-placeholder);

                @include mixins.transition;
            }

            &:hover {
                span {
                    color: var(--color-input-label);
                }
            }
        }
    }

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
                grid-template-columns: repeat(3,1fr);
                gap: functions.rem(4);
                padding: functions.rem(80) functions.rem(20) functions.rem(120) functions.rem(20);

                @media (max-width: 1300px) {
                    grid-template-columns: repeat(2, 1fr);
                }
                @media (max-width: 800px) {
                    grid-template-columns: repeat(1, 1fr);
                }

                li {
                    input {display: none;}
                    label {
                        height: 100%;
                        display: block;
                        padding: functions.rem(4);
                        border-radius: functions.rem(20);
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