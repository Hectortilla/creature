<script lang="ts">
    import type { Creature, Element, Type, Character } from '$lib/types';
    import { formatHandle } from "$lib/utils/formatHandle";
    import { onMount } from 'svelte';

    // Components
    import CreatureCard360 from "$lib/components/creature/Card360.svelte";
    import InputSearch from "$lib/components/input/Search.svelte";
    import Select from "$lib/components/input/Select.svelte";

    interface PageProps {
        data: {
            cards?: Creature[];
            elements?: Element[];
            types?: Type[];
            characters?: Character[]
        };
    }

    let { data }: PageProps = $props();
    console.log(data);

    let searchTerm = $state("");
    let filterByElement = $state<number | null>(null);
    let filterByType = $state<number | null>(null);
    let filterByCharacter = $state<number | null>(null);

    let filteredCards = $derived(() => {
        if (!data.cards) return [];

        return data.cards.filter((card: any) => {
            // Search filter
            const matchesSearch =
                searchTerm.trim() === "" ||
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
        });
    });


    // Container card position
    let cardContainer = $state<HTMLElement>();
    let cardContainerPosition = $state(0);

    onMount (() => {
        cardContainerPosition = cardContainer?.getBoundingClientRect().top ?? 0;
    });

</script>

<div class="gallery-container">
    <div class="filters-container">
        <InputSearch bind:value={searchTerm} placeholder="Busca por nombre o por código" />
        {#if data.elements}
            <Select
                showLabel={false}
                label="Elemento"
                noSelectText="Todos"
                list={data.elements}
                iconType="image"
                isMandatory={false}
                isDisabled={false}
                bind:group={filterByElement}
            />
        {/if}
        {#if data.types}
            <Select
                showLabel={false}
                label="Tipo"
                noSelectText="Todos"
                list={data.types}
                iconType="icon"
                isMandatory={false}
                isDisabled={false}
                bind:group={filterByType}
            />
        {/if}
        {#if data.characters}
            <Select
                showLabel={false}
                label="Naturaleza"
                noSelectText="Todas"
                list={data.characters}
                iconType="icon"
                isMandatory={false}
                isDisabled={false}
                bind:group={filterByCharacter}
            />
        {/if}
    </div>
    {#if data.cards && data.cards.length > 0}
        <div class="gallery-cards" bind:this={cardContainer}>
            {#each filteredCards() as card, i}
                <CreatureCard360
                    data={card}
                    key={i}
                    showCode={true}
                    showInfo={true}
                    allowLink= {true}
                    containerPos={cardContainerPosition}
                    allowHoverEffect={true}
                />
            {/each}
        </div>
    {:else}
        <p>No cards found in this section.</p>
    {/if}
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .gallery-cards {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: functions.rem(10);
        justify-items: center;
        align-items: start;

        perspective: 2000px;
        -webkit-perspective: 2000px;

        @media (max-width: 1250px) {
            grid-template-columns: repeat(4, 1fr);
        }

        @media (max-width: 1000px) {
            grid-template-columns: repeat(3, 1fr);
        }

        @media (max-width: 600px) {
            grid-template-columns: repeat(2, 1fr);
        }
    }
</style>