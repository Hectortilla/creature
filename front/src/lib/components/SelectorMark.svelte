<script lang="ts">
    import { onMount } from "svelte";

    // Constants
    import { FONT_BASE_SIZE } from "$lib/constants";

    // Icons
    import IconRaw from "$lib/assets/icons/icon.svg?raw";

    const gradientId = `grad-${Math.random().toString(36).slice(2)}`;
	

    interface Props {
        size?: number;
    }

    let {
        size = 24,
    }: Props = $props();

    let Icon = $state(IconRaw);

    onMount(() => {
        Icon = IconRaw.replace(
            "<svg",
            `<svg>
                <defs>
                <linearGradient id="${gradientId}" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="var(--color-icon-mark-start)" />
                    <stop offset="100%" stop-color="var(--color-icon-mark-end)" />
                </linearGradient>
                </defs>`
            ).replace(/fill="[^"]*"/g, `fill="url(#${gradientId})"`
        );
    });
</script>

<div class="selector-wrapper" style={`--size: ${size / FONT_BASE_SIZE}rem`}>
    <div class="selector-mark-icon blur">
        {@html Icon}
    </div>
    <div class="selector-mark-icon">
        {@html Icon}
    </div>
</div>

<style lang="scss">
    @use "../styles/abstracts/variables" as variables;
    @use "../styles/abstracts/mixins" as mixins;
	@use "../styles/abstracts/functions" as functions;

    .selector-wrapper {
        position: relative;
        width: var(--size);
        height: var(--size);

        .selector-mark-icon {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: block;
            color: var(--color-stylished-gradient-text);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: var(--color-stylished-gradient-text);
            
            filter: blur(functions.rem(.6));

            &.blur {
                filter: blur(functions.rem(12));
                opacity: .6;
            }
        }
    }

</style>