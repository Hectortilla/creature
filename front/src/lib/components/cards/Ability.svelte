<script lang="ts">
    import type { Ability } from '$lib/types';

    // Components
    import NarrativeText from '$lib/components/NarrativeText.svelte';

    // Icons
    import physical from "$lib/icons/physical-type.svg?raw";
    import magical from "$lib/icons/magical-type.svg?raw";

    // Tipado de props
    type IconName =
        string | "physical" | "magical";

    interface PageProps {
        data: Ability;
        allowLink?: boolean;
        showDescription?: boolean;
    }

    let {
        data,
        allowLink = true,
        showDescription = true
    }: PageProps = $props();

    // Mapa de iconos
    const iconType: Record<IconName, string> = {
        physical,
        magical
    };

</script>

<a
    href={`/abilities/${data.code}`}
    aria-label={`Ver habilidad ${data.name}`}
    class="card-attack-container"
    class:no-link={!allowLink}
>
    <div class="info">
        <p class="name">{data.name}</p>
        {#if data.type}
            <div class="item">
                <div class="icon">{@html iconType[data.type]}</div>
            </div>
        {/if}
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

            .item {
                @include mixins.displayFlex(row, 4, flex-start, center, wrap);

                .icon {
                    width: functions.rem(20);
                    height: functions.rem(20);
                }
            }
        }
    }

</style>