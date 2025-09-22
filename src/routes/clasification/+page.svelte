<script lang="ts">
    import type { Element } from '$lib/types';

    // Components
    import ElementsTable from '$lib/components/ElementsTable.svelte'

    interface PageProps {
        data: {
            elements?: Element[];
        };
    }

    let { data }: PageProps = $props();
</script>
<div class="page-container">
    <ElementsTable elements={data.elements} />
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;
    @use "$lib/styles/abstracts/functions" as functions;
    @use "$lib/styles/abstracts/variables" as variables;

    .page-container {
        @include mixins.displayFlex(column, 40, flex-start, center, wrap);
        @include mixins.margins;
    }
</style>