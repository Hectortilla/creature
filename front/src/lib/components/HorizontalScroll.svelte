<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { fade } from "svelte/transition";
    import type { Snippet } from "svelte";

    // Constants
    import { FONT_BASE_SIZE } from "$lib/constants";

    interface Props {
        gap?: number;
        margin?: number;
        top?: number;
        smoothFactor?: number;
        showScrollReference?: boolean;
        children?: Snippet;
    }

    let {
        gap = 100,
        margin = 120,
        top = 0,
        smoothFactor = 1,
        showScrollReference = true,
        children,
    }: Props = $props();

    const TRACK_WIDTH = 100;

    let container: HTMLDivElement;
    let wrapper: HTMLDivElement;
    let targetScroll = 0;
    let scrollLeft = $state(0);
    let smoothFactorMix = $derived(smoothFactor / 10);
    let containerWidth = $state(0);
    let wrapperWidth = $state(0);
    let scrollPercent = $state(0);
    let barWidth = $state(0)
    let refBarIsLoaded = $state(false);

    function handleWheel(e: WheelEvent) {
        e.preventDefault();

        containerWidth = container.getBoundingClientRect().width;
        wrapperWidth = wrapper.getBoundingClientRect().width;
        barWidth = wrapperWidth ? (containerWidth / wrapperWidth) * 100 : 0;
        const maxScroll = wrapperWidth - containerWidth;

        const delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY;

        targetScroll -= delta;

        if (targetScroll < -maxScroll) targetScroll = -maxScroll;
        if (targetScroll > 0) targetScroll = 0;
    }

    function animate() {
        const diff = targetScroll - scrollLeft;

        if (Math.abs(diff) < 0.1) {
            scrollLeft = targetScroll;
        } else {
            scrollLeft += diff * smoothFactorMix;
        }

        const maxScroll = wrapperWidth - containerWidth;

        scrollPercent = maxScroll ? -scrollLeft / maxScroll : 0;

        requestAnimationFrame(animate);
    }


    onMount(() => {

        setTimeout(() => {
            containerWidth = container.getBoundingClientRect().width;
            wrapperWidth = wrapper.getBoundingClientRect().width;
            barWidth = wrapperWidth ? (containerWidth / wrapperWidth) * 100 : 0;
            refBarIsLoaded = true;
            console.log(containerWidth / wrapperWidth);
        }, 200)

        animate();
    });

    onDestroy(() => {
        containerWidth = 0;
        wrapperWidth = 0;
        barWidth = 0;
    });

</script>

<div
    class="horizontal-scroll"
    role="slider"
    aria-valuenow={0}
    tabindex="0"
    bind:this={container}
    onwheel={handleWheel}
>
    <div class="horizontal-center">
        <div
            bind:this={wrapper}
            class="horizontal-wrapper"
            style={`
                transform:translateX(${scrollLeft}px);
                --gap:${gap / FONT_BASE_SIZE}rem;
                --padding:${margin / FONT_BASE_SIZE}rem;
                --top:${top}%;
            `}
        >
            {@render children?.()}
        </div>
    </div>

    {#if showScrollReference && refBarIsLoaded && containerWidth < wrapperWidth}
        <div transition:fade class="scroll-reference" style={`--reference-width:${TRACK_WIDTH / FONT_BASE_SIZE}rem`}>
            <div
                class="scroll-bar"
                style={`--bar-width:${barWidth}%; margin-left:${scrollPercent * (100 - (barWidth))}%;`}
            ></div>
        </div>
    {/if}
</div>

<style lang="scss">
    @use "../styles/abstracts/variables" as variables;
    @use "../styles/abstracts/mixins" as mixins;
	@use "../styles/abstracts/functions" as functions;

    .horizontal-scroll {
        width: 100%;
        height: 100%;

        @include mixins.displayFlex(row, 0, flex-start, center, nowrap);

        .horizontal-center {
            width: 100%;
            min-width: max-content;

            @include mixins.displayFlex(row, 0, center, flex-start, nowrap);


            .horizontal-wrapper {
                display: flex;
                flex-direction: row;
                justify-content: center;
                align-items: flex-start;
                flex-wrap: nowrap;
                gap: var(--gap);
                width: max-content;
                height: auto;
                padding: var(--top) var(--padding) 0 var(--padding);
            }
        }

        .scroll-reference {
            position: absolute;
            width: var(--reference-width);
            height: functions.rem(4);
            right: functions.rem(variables.$margin-page-desktop);
            bottom: functions.rem(variables.$margin-page-desktop);
            background-color: var(--color-scroll-reference-background);
            border-radius: functions.rem(20);
            backdrop-filter: blur(functions.rem(12));
            overflow: hidden;

            .scroll-bar {
                position: relative;
                display: block;
                width: var(--bar-width);
                height: 100%;
                background-color: var(--color-scroll-reference-bar);
                border-radius: functions.rem(20);
            }
        }
    }

</style>