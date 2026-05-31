<script lang="ts">
    import type { Ability } from '$lib/types';
    import { formatHandle } from '$lib/utils/formatHandle';

    // Components
    import CardAbility from "$lib/components/cards/Ability.svelte";
    import InputSearch from "$lib/components/input/Search.svelte";
    import Select from "$lib/components/input/Select.svelte";

    interface PageProps {
        data: {
            abilities?: Ability[];
        };
    }

    let { data }: PageProps = $props();
    console.log(data);

    const types = [
        { id: 1, label: "Físico" , icon: "physical" },
        { id: 2, label: "Mágico" , icon: "magical" }
    ];

    let searchTerm = $state("");
    let filterByType = $state<number | null>(null);

    let filteredAbilities = $derived(() => {
        if (!data.abilities) return [];

        return data.abilities.filter((ability: any) => {
            // Search filter
            const matchesSearch =
                searchTerm.trim() === "" ||
                formatHandle(ability.name).includes(formatHandle(searchTerm)) ||
                String(ability.code).includes(searchTerm.trim());

            // Type filter
            const matchesType =
                filterByType === null || (types.find(t => t.id === filterByType)?.icon === ability.type);
                

            return matchesSearch && matchesType;
        }).sort((a, b) => a.code - b.code);
    });

</script>

{#if data.abilities && data.abilities.length > 0}
    <div class="gallery-container">
        <div class="filters-container">
            <InputSearch bind:value={searchTerm} placeholder="Busca por nombre o por código" />
            {#if types}
                <Select
                    showLabel={false}
                    label="Tipo"
                    noSelectText="Todos"
                    list={types}
                    iconType="icon"
                    isMandatory={false}
                    isDisabled={false}
                    bind:group={filterByType}
                />
            {/if}
        </div>
        <div class="gallery-abilities">
            {#each filteredAbilities() as ability}
                <CardAbility data={ability} />
            {/each}
        </div>
    </div>
{:else}
    <p>No abilities found in this section.</p>
{/if}

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .gallery-abilities {
        width: 100%;
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: functions.rem(12);

        @include mixins.margins;

        @media (max-width: 1300px) {
            grid-template-columns: repeat(2, 1fr);
        }
        @media (max-width: 800px) {
            grid-template-columns: repeat(1, 1fr);
        }
    }
    
</style>