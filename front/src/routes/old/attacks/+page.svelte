<script lang="ts">
    import type { Attack, Element } from '$lib/types';
    import { formatHandle } from '$lib/utils/formatHandle';

    // Components
    import CardAttack from "$lib/components/cards/Attack.svelte";
    import InputSearch from "$lib/components/input/Search.svelte";
    import Select from "$lib/components/input/Select.svelte";

    interface PageProps {
        data: {
            attacks?: Attack[];
            elements?: Element[];
        };
    }

    let { data }: PageProps = $props();
    console.log(data);

    const types = [
        { id: 1, label: "Físico" , icon: "physical" },
        { id: 2, label: "Mágico" , icon: "magical" }
    ];

    let searchTerm = $state("");
    let filterByElement = $state<number | null>(null);
    let filterByType = $state<number | null>(null);

    let filteredAttacks = $derived(() => {
        if (!data.attacks) return [];

        return data.attacks.filter((attack: any) => {
            // Search filter
            const matchesSearch =
                searchTerm.trim() === "" ||
                formatHandle(attack.name).includes(formatHandle(searchTerm)) ||
                String(attack.code).includes(searchTerm.trim());

            // Element filter
            const matchesElement =
                filterByElement === null ||
                Number(attack.element?.id) === filterByElement

            // Type filter
            const matchesType =
                filterByType === null || (types.find(t => t.id === filterByType)?.icon === attack.type);

            return matchesSearch && matchesElement && matchesType;
        }).sort((a, b) => a.code - b.code);
    });

</script>

{#if data.attacks && data.attacks.length > 0}
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
        <div class="gallery-attacks">
            {#each filteredAttacks() as attack, i}
                <CardAttack data={attack} key={i}/>
            {/each}
        </div>
    </div>
{:else}
    <p>No attacks found in this section.</p>
{/if}

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .gallery-attacks {
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