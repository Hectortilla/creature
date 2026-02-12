<script lang="ts">
    import type { PageProps } from "./$types";

    // Components
    import HorizontalScroll from "$lib/components/HorizontalScroll.svelte";
    import CollectionCard from "$lib/components/cards/Collection.svelte";

    // Constants
    import { COLLECTION_MENU } from "$lib/constants";

    let { data }: PageProps = $props();
    $inspect(data);

</script>

<div class="collection-container">
    <HorizontalScroll>
        {#each COLLECTION_MENU as { label, path, amount_label, image }, i}
            <CollectionCard
                index={i}
                text={label}
                amount={data?.[`${amount_label}_amount`] ?? 0}
                amount_label={amount_label}
                image={image}
                link={path}
            />
        {/each}
    </HorizontalScroll>
</div>

<style lang="scss">
    @use "../../lib/styles/abstracts/variables" as variables;
	@use "../../lib/styles/abstracts/mixins" as mixins;
	@use "../../lib/styles/abstracts/functions" as functions;

    .collection-container {
        position: relative;
        width: 100%;
        height: 100vh; // prevent browser
        height: 100dvh;
        overflow: hidden;

        @include mixins.displayFlex(row, 60, center, center, nowrap);
    }
</style>