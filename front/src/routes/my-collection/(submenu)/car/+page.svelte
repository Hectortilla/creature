<script lang="ts">
    import type { PageProps } from "./$types";

    let { data }: PageProps = $props();
    $inspect(data);

</script>

<div class="cards-container">
    Cards
</div>

<style lang="scss">
    @use "../../../../lib/styles/abstracts/variables" as variables;
	@use "../../../../lib/styles/abstracts/mixins" as mixins;
	@use "../../../../lib/styles/abstracts/functions" as functions;

    .cards-container {
        position: relative;
        width: 100%;
        height: 100vh; // prevent browser
        height: 100dvh;
        overflow: hidden;

        @include mixins.displayFlex(row, 0, center, center, nowrap);
    }
</style>