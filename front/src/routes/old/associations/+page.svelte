<script lang="ts">
    import type { Association } from '$lib/types';
    import { formatHandle } from '$lib/utils/formatHandle';

    // Components
    import CardAssociation from "$lib/components/cards/Association.svelte";
    import InputSearch from "$lib/components/input/Search.svelte";

    interface PageProps {
        data: {
            associations?: Association[];
        };
    }

    let { data }: PageProps = $props();
    console.log(data);

    let searchTerm = $state("");

    let filteredAssociation = $derived(() => {
        if (!data.associations) return [];
        let filterAssociations: any[] = data.associations;

        // Search input
        const searching = searchTerm.trim() !== "";

        if (searching) {
            filterAssociations = data.associations.filter((association: any) =>
                formatHandle(association.name).includes(formatHandle(searchTerm)) ||
                formatHandle(association.code).includes(formatHandle(searchTerm))
            );
        }

        return filterAssociations.sort((a, b) => a.code - b.code);

    });

</script>

{#if data.associations && data.associations.length > 0}
    <div class="gallery-container">
        <div class="filters-container">
            <InputSearch bind:value={searchTerm} placeholder="Busca por nombre o por código" />
        </div>
        <div class="gallery-associations">
            {#each filteredAssociation() as association}
                <CardAssociation data={association}/>
            {/each}
        </div>
    </div>
{:else}
    <p>No associations found in this section.</p>
{/if}

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .gallery-associations {
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