<script lang="ts">
    import type { PageProps } from "./$types";

    let { data }: PageProps = $props();
    $inspect(data);

    import GallerySearchAndFilter from "$lib/components/GallerySearchAndFilter.svelte";

</script>

<div class="cards-container">
    <GallerySearchAndFilter
        cards={data.cards}
        onClickOnCard={() => console.log('click on card')}
    />
</div>

<style lang="scss">
    @use "../../../../lib/styles/abstracts/variables" as variables;
	@use "../../../../lib/styles/abstracts/mixins" as mixins;
	@use "../../../../lib/styles/abstracts/functions" as functions;

    .cards-container {
        position: relative;
        width: 100%;
        //overflow: hidden;
        padding-top: functions.rem(220);

        @include mixins.displayFlex(row, 0, center, center, nowrap);
    }
</style>