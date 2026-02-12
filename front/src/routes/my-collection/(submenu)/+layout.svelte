<script lang="ts">
    // Constants
    import { COLLECTION_MENU } from "$lib/constants";

    // Components
    import QuickAccess from "$lib/components/menu/QuickAccess.svelte";

    let { children } = $props();
</script>

<QuickAccess
    menu={[...COLLECTION_MENU]}
    maxWidth={300}
/>

{@render children?.()}

<style lang="scss">
    @use "../../../lib/styles/abstracts/variables" as variables;
    @use "../../../lib/styles/abstracts/mixins" as mixins;
	@use "../../../lib/styles/abstracts/functions" as functions;
    
</style>