<script lang="ts">
    import type { Association } from '$lib/types';

    // Components
    import NarrativeText from '$lib/components/NarrativeText.svelte';

    interface PageProps {
        data: Association;
        allowLink?: boolean;
        showDescription?: boolean;
    }

    let {
        data,
        allowLink = true,
        showDescription = true
    }: PageProps = $props();

</script>

<a
    href={`/associations/${data.code}`}
    aria-label={`Ver asociación ${data.name}`}
    class="card-attack-container"
    class:no-link={!allowLink}
>
    <div class="info">
        <p class="name">{data.name}</p>
    </div>
    {#if showDescription && data.description}
        <NarrativeText text={data.description}/>
    {/if}
</a>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .card-attack-container {
        width: 100%;
        height: 100%;
        border-radius: functions.rem(16);
        padding: functions.rem(16);
        background-color: var(--color-card-background);
        box-shadow:
            0 functions.rem(-2) functions.rem(4) functions.rem(-2) transparent inset,
            0 functions.rem(2) functions.rem(6) functions.rem(1) transparent inset;

        @include mixins.displayFlex(column, 16, flex-start, flex-start, nowrap);
        @include mixins.transition;

        &:hover {
            box-shadow:
                0 functions.rem(0) functions.rem(4) functions.rem(-2) var(--color-input-button-light-top) inset,
                0 functions.rem(0) functions.rem(2) functions.rem(-2) var(--color-input-button-light-bottom) inset;
        }

        &.no-link {
            cursor: default;
            pointer-events: none;
        }

        .info {
            width: 100%;
            @include mixins.displayFlex(row, 16, flex-start, center, wrap);

            p.name {
                flex: 1;
                font-size: functions.rem(22);
                font-family: variables.$font-title;
            }
        }
    }

</style>