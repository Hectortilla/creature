<script lang="ts">
    import type { CardCreature } from '$lib/types';
    import { blur } from "svelte/transition";
    import { formatHandle } from '$lib/utils/formatHandle';

    // Components
    import Code from "$lib/components/creature/Code.svelte";
    import Icon from '$lib/components/creature/Icon.svelte';
    import Evolution from '$lib/components/creature/Evolution.svelte';
    import Spinner from '$lib/components/creature/Spinner.svelte';

    interface PageProps {
        data: CardCreature;
        key: number;
        showInfo?: boolean;
        showCode?: boolean;
        showEvolutionCode?: boolean;
        allowLink?: boolean;
        allowHoverEffect?: boolean;
        containerPos: number;
    }

    let {
        data,
        key,
        showInfo = true,
        showCode = true,
        showEvolutionCode = true,
        allowLink = true,
        allowHoverEffect = true,
        containerPos = 0,
    }: PageProps = $props();

    // Focus
    let isFocus = $state(false);

    // Image loader
    let isImageLoading = $state(false);
    let isOverlayImageLoading = $state(false);

    // Card Move
    let moveX = $state(0);
    let moveY = $state(0);

     // Point o light Y
    let pointOneY = $state(-100);
    let pointOneYOpacity = $state(0);
    let pointTwoY = $state(100);
    let pointTwoYOpacity = $state(0);

    // Point o light X
    let pointOneX = $state(-100);
    let pointOneXOpacity = $state(0);
    let pointTwoX = $state(100);
    let pointTwoXOpacity = $state(0);

    // Finger Prints
    let fingerPrintsOpacity = $state(.3)

    function handleMouseCapture(e:any, code:number) {
        if(!allowHoverEffect) return;

        const round2 = (v: number) => Math.round(v * 100) / 100;

        let cardWidth = e.srcElement.clientWidth;
        let cardHeight = e.srcElement.clientHeight;
        let mouseX = e.offsetX;
        let mouseY = e.offsetY;

        // Limit mov to 2
        const limit = 2;
        const normX = (mouseX - cardWidth / 2) / (cardWidth / 2);
        const normY = (mouseY - cardHeight / 2) / (cardHeight / 2);

        moveX = round2(normX * limit);
        moveY = round2(normY * -limit);

        const percentMouseY = (mouseY * 100) / cardHeight
        const percentMouseX = (mouseX * 100) / cardWidth

        const distanceToCenterY = Math.abs(percentMouseY - 50) / 50;
        const distanceToCenterX = Math.abs(percentMouseX - 50) / 50;

        const cardFactorY = ((e.clientY - containerPos) / window.innerHeight);
        const cardFactorX = (e.clientX / window.innerWidth);

        // Point of light and effects
        // It depends on the card position on the screen
        // Y
        pointOneY = percentMouseY;
        pointOneYOpacity = (distanceToCenterY) * (
            cardFactorY * (percentMouseY / 100) + (1 - cardFactorY) * (1 - percentMouseY / 100)
        );

        pointTwoY = percentMouseY;
        pointTwoYOpacity = pointOneYOpacity;

        // X
        pointOneX = percentMouseX;
        pointOneXOpacity = (distanceToCenterX) * (
            cardFactorX * (percentMouseX / 100) + (1 - cardFactorX) * (1 - percentMouseX / 100)
        );

        pointTwoY = percentMouseX;
        pointTwoYOpacity = pointOneXOpacity;

        // Fingers
        fingerPrintsOpacity = 0.3 + ((100 - pointOneY) / 100) * (1 - 0.3); // .3 -> 1

    }

    function handleMouseLeave() {
        // reset
        moveX = 0;
        moveY = 0;
        // pointOneY = -100;
        // pointOneX = -100;
        pointOneYOpacity = 0;
        pointTwoYOpacity = 0;
        pointOneXOpacity = 0;
        pointTwoXOpacity = 0;
        fingerPrintsOpacity = .3;
    }

    function handleImageLoad() {
        setTimeout(() => {
            isImageLoading = false;
        }, 300);
    }

    function handleOverlayImageLoad() {
        setTimeout(() => {
            isOverlayImageLoading = false;
        }, 300);
    }

    let imgSrc = $derived.by(() => data.image !== '' && data.image ? data.image:  '/images/cards/placeholder.jpg');
    let overlayImgSrc = $derived.by(() => data.overlay_image ?? null);

    $effect(() => {
        const img = imgSrc;
        const overlay = overlayImgSrc ?? true;
        if (img && overlay) {
            isImageLoading = true;
            isOverlayImageLoading = true;
        }
    });

</script>

<div
    class={`card-container theme-${data.first_element?.label ? formatHandle(data.first_element.label): 'default'}`}
    role="none"
    onfocus={() => {isFocus = true}}
    onmousemovecapture={() => {handleMouseCapture(event, data.code)}}
    onmouseleave={() => {handleMouseLeave()}}
    style={`--x: ${moveX}; --y: ${moveY};`}
>
    <a href="/cards/{data.code}" class="card-wrapper" class:no-link={!allowLink}>
        {#if showCode || (showInfo && data.is_evolution !== null)}
            <div class="info">
                {#if showCode && data.code}
                    <Code code={data.code} />
                {/if}
                {#if data.is_evolution !== null && data.is_evolution && showEvolutionCode}
                    <Evolution evolutionCode={data.is_evolution.code}/>
                {/if}
            </div>
        {/if}
        {#if showInfo}
            <div class="hover-info">
                <div class="classification">
                    {#if data.type?.icon}
                        <Icon name={data.type.icon} size={0} isBackground={true} />
                    {/if}
                    {#if data.character?.icon} 
                        <Icon name={data.character.icon} size={0} isBackground={true} />
                    {/if}
                </div>
                <div class="elements">
                    {#if data.first_element}
                        <div class="element">
                            <img
                                src={data.first_element.icon}
                                alt={data.first_element.label}
                                style="--color-element:#{data.first_element.color}"
                            />
                        </div>
                    {/if}
                    {#if data.second_element}
                        <div class="element">
                            <img
                                src={data.second_element.icon}
                                alt={data.second_element.label}
                                style="--color-element:#{data.second_element.color}"
                            />
                        </div>
                    {/if}
                </div>
            </div>
        {/if}
        {#if isImageLoading && isOverlayImageLoading}
            <div out:blur class="loader">
                <Spinner />
            </div>
        {/if}
        <img
            src={imgSrc}
            alt={data.name}
            width="300"
            onload={handleImageLoad}
        />
        {#if overlayImgSrc && overlayImgSrc !== null}
            <img
                class="parallax"
                src={overlayImgSrc}
                alt={`${data.name} - parallax`}
                width="300"
                onload={handleOverlayImageLoad}
                style={`--x: ${moveX}; --y: ${moveY}; --tx:${moveY * -2}px; --ty:${moveX * -2}px;`}
            />
        {/if}
        <div
            class="effects"
            style={`
                --pointOneYOpacity: ${pointOneYOpacity};
                --pointOneY: ${pointOneY}%;
                --pointTwoYOpacity: ${pointTwoYOpacity};
                --pointTwoY: ${pointTwoY}%;
                --pointOneXOpacity: ${pointOneXOpacity};
                --pointOneX: ${pointOneX}%;
                --pointTwoXOpacity: ${pointTwoXOpacity};
                --pointTwoX: ${pointTwoX}%;
                --fingerPrintsOpacity: ${fingerPrintsOpacity};
            `}
        >
            <div class="lateral-lights"></div>
            <div class="finger-prints" style={`background: url('/images/finger-prints/${(key % 4) + 1}.jpg');`}></div>
        </div>
    </a>
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .card-container {
        position: relative;
        width: 100%;
        height: auto;
        mask-image: url("/images/card-mask.svg");
        mask-position: center;
        mask-size: 100% 100%;
        mask-repeat: no-repeat;
        transform-style: preserve-3d;
        transform: rotate3d(var(--y), var(--x), 0, 12deg);

        @include mixins.displayFlex(column, 0, flex-start, flex-start, nowrap);
        @include mixins.transition();

        .card-wrapper {
            position: relative;
            width: 100%;
            height: auto;

            &.no-link {
                pointer-events: none;
            }

            .effects {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                box-shadow:
                    0 functions.rem(2) functions.rem(6) functions.rem(-2) var(--color-creature-card-light-top) inset,
                    0 functions.rem(-2) functions.rem(8) functions.rem(1) var(--color-creature-card-light-bottom) inset;

                .finger-prints {
                    width: 100%;
                    height: 100%;
                    background: url("/images/finger-prints/1.jpg");
                    background-position: center;
                    background-repeat: no-repeat;
                    background-size: cover;
                    mix-blend-mode: plus-lighter;
                    opacity: var(--fingerPrintsOpacity);
                    will-change: opacity;

                    @include mixins.transition(opacity, 0.3s);
                }

                .lateral-lights {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;

                    &::before, &::after {
                        content: "";
                        position: absolute;
                        top: 0;
                        height: 100%;
                        pointer-events: none;
                        filter: blur(functions.rem(40));
                        will-change: transform, opacity;

                        @include mixins.transition(opacity, 0.3s);
                    }

                    &::before {
                        left: -10%;
                        transform: translateX(var(--pointOneX)) translateY(0);
                        background-color: var(--color-creature-card-reflection-one);
                        opacity: var(--pointOneXOpacity);
                        width: 20%;
                    }
                    &::after {
                        right: -10%;
                        transform: translateX(var(--pointTwoX)) translateY(0);
                        background-color: var(--color-creature-card-reflection-two);
                        opacity: var(--pointTwoXOpacity);
                        width: 10%;
                    }
                    
                }

                &::before, &::after {
                    content: "";
                    position: absolute;
                    left: 50%;
                    width: 100%;
                    pointer-events: none;
                    filter: blur(functions.rem(30));
                    will-change: transform, opacity;

                    @include mixins.transition(opacity, 0.3s);
                }

                &::before {
                    top: 0;
                    transform: translateX(-50%) translateY(var(--pointOneY));
                    background-color: var(--color-creature-card-reflection-one);
                    opacity: var(--pointOneYOpacity);
                    height: 20%;
                }
                &::after {
                    bottom: 30%;
                    transform: translateX(-50%) translateY(var(--pointTwoY));
                    background-color: var(--color-creature-card-reflection-two);
                    opacity: var(--pointTwoYOpacity);
                    height: 10%;
                }
            }

            img {
                width: 100%;
                height: auto;
                pointer-events: none;
            }
            img.parallax {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: auto;
                transform-style: preserve-3d;
                pointer-events: none;
                transform:
                    rotate3d(var(--y), var(--x), 0, 13deg)
                    translate3d(var(--ty), var(--tx), -10px)
                    scale(1.03);

                @include mixins.transition(.6s);
            }

            .info {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 16%;
                max-height: functions.rem(62);
                min-height: functions.rem(56);
                padding: functions.rem(12);

                @include mixins.displayFlex(row, 10, space-between, flex-start, nowrap);
            }

            .hover-info {
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 14%;
                max-height: functions.rem(54);
                min-height: functions.rem(44);
                padding: functions.rem(12);
                opacity: 0;
                will-change: opacity;

                @include mixins.displayFlex(row, 20, space-between, flex-start, nowrap);
                @include mixins.transition(opacity, 0.3s);

                .elements, .classification {
                    position: relative;
                    width: max-content;
                    height: 100%;
                    @include mixins.displayFlex(row, 4, flex-start, flex-start, nowrap);

                    &::before {
                        content: "";
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 140%;
                        background-color: black;
                        pointer-events: none;
                        filter: blur(functions.rem(14));
                        z-index: -1;
                    }
                }

                .elements .element {
                    flex-shrink: 0;
                    width: auto;
                    height: 100%;

                    img {
                        flex-shrink: 0;
                        width: 100%;
                        height: 100%;
                        filter: drop-shadow(0 0 functions.rem(20) var(--color-element));
                    }
                }
            }
        }

        &:hover .card-wrapper .hover-info {
            opacity: 1;
        }

        // to component
        .loader {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: var(--color-creature-loader-background);
            z-index: 1;

            @include mixins.displayFlex(column, 0, center, center, nowrap);
        }
    }
</style>