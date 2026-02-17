<script lang="ts">
    import type { CardCreature } from '$lib/types';
    import { blur, scale } from "svelte/transition";
    import { formatHandle } from '$lib/utils/formatHandle';
    import type { Snippet } from 'svelte';

    // Rarity Styles
    import "$lib/styles/components/rarity/base.css";
    import "$lib/styles/components/rarity/amazing-rare.css";
    import "$lib/styles/components/rarity/cosmos-holo.css";
    import "$lib/styles/components/rarity/radiant-holo.css";
    import "$lib/styles/components/rarity/rainbow-alt.css";
    import "$lib/styles/components/rarity/regular-holo.css";
    import "$lib/styles/components/rarity/radiant-holo.css";
    import "$lib/styles/components/rarity/reverse-holo.css";
    import "$lib/styles/components/rarity/secret-rare.css";
    import "$lib/styles/components/rarity/shiny-rare.css";
    import "$lib/styles/components/rarity/shiny-v.css";
    import "$lib/styles/components/rarity/shiny-vmax.css";
    import "$lib/styles/components/rarity/swsh-pikachu.css";
    import "$lib/styles/components/rarity/trainer-gallery-secret-rare.css";
    import "$lib/styles/components/rarity/trainer-gallery-v-max.css";
    import "$lib/styles/components/rarity/trainer-gallery-v-regular.css";
    import "$lib/styles/components/rarity/trainer-gallery-holo.css";
    import "$lib/styles/components/rarity/trainer-full-art.css";
    import "$lib/styles/components/rarity/v-max.css";
    import "$lib/styles/components/rarity/v-regular.css";
    import "$lib/styles/components/rarity/v-star.css";
    import "$lib/styles/components/rarity/v-full-art.css";


    // Components
    import Code from "$lib/components/creature/Code.svelte";
    import Icon from '$lib/components/creature/Icon.svelte';
    import Evolution from '$lib/components/creature/Evolution.svelte';
    import Spinner from '$lib/components/creature/Spinner.svelte';


    // TO ADD IN DATABASE
    // 
    //  'normal' | 'rare secret' | 'rare holo cosmos' | 'rare ultra' | 'trainer gallery rare holo';
    //
    let DATA_RARITY = $state("rare ultra");

    interface PageProps {
        data: CardCreature;
        key: number;

        // HTML
        role?: 'a' | 'button' | 'div';
        ariaLabel?: string;

        // Events
        onClick?: () => void;
        onLongClick?: () => void;

        // Show
        showInfo?: boolean;
        showCode?: boolean;
        showEvolutionCode?: boolean;
        showLoader?: boolean;

        // Effects
        allow360Effect?: boolean;
        perspective?: number,

        // Child for buttons
        children?: Snippet;
    }

    let {
        data,
        key,
        role = 'a',
        onClick,
        onLongClick,
        ariaLabel,
        showInfo = true,
        showCode = true,
        showEvolutionCode = true,
        allow360Effect = true,
        perspective = 1000,
        showLoader = false,
        children,
    }: PageProps = $props();

    /* -----------------------------------------------------
       STATE
    ----------------------------------------------------- */

    // Image loading state
    let isImageLoading = $state(false);

    // Card rotation movement
    let moveX = $state(0);
    let moveY = $state(0);

    // Light reflection positions (Y axis)
    let pointOneY = $state(-100);
    let pointOneYOpacity = $state(0);
    let pointTwoY = $state(100);
    let pointTwoYOpacity = $state(0);

    // Light reflection positions (X axis)
    let pointOneX = $state(-100);
    let pointOneXOpacity = $state(0);
    let pointTwoX = $state(100);
    let pointTwoXOpacity = $state(0);

    // Fingerprint overlay opacity
    let fingerPrintsOpacity = $state(0.3);

    // Holo Foil
    let hasRarity = $derived(DATA_RARITY !== 'normal');
    let pointerX = $state(0);
    let pointerY = $state(0);
    let pointerFromCenter = $state(0);
    let backgroundX = $state(0);
    let backgroundY = $state(0);
    let cardOpacity = $state(0);

    let showActions = $state(true);


    /* -----------------------------------------------------
       HTML PROPS
    ----------------------------------------------------- */

    const HTMLProps = $derived.by(() => {
        if (role === 'a') {
            return { href: `/cards/${data.code}` };
        }

        if (role === 'button') {
            return {
                onpointerdown: handlePointerDown,
                onpointerup: handlePointerUp,
                onpointerleave: handlePointerLeave,
                role: 'button',
                'aria-label': ariaLabel
            };
        }
    });

    /* -----------------------------------------------------
       CLICK EVENTS
    ----------------------------------------------------- */

    let clickTimeout: ReturnType<typeof setTimeout> | null = null;
    const LONG_PRESS_DURATION = 500; // ms para considerar long press

    function handlePointerDown() {
        // Inicia el timer de long press
        clickTimeout = setTimeout(() => {
            if (onLongClick) onLongClick();
            clickTimeout = null; // ya se ejecutó long click
        }, LONG_PRESS_DURATION);
    }

    function handlePointerUp() {
        if (clickTimeout) {
            // Si todavía no se cumplió el tiempo, es click normal
            clearTimeout(clickTimeout);
            clickTimeout = null;
            if (onClick) onClick();
        }
    }

    function handlePointerLeave() {
        // Cancelar si el usuario mueve fuera del área
        if (clickTimeout) {
            clearTimeout(clickTimeout);
            clickTimeout = null;
        }
    }

    /* -----------------------------------------------------
       MOUSE INTERACTION
    ----------------------------------------------------- */

    function handleMouseCapture(e: MouseEvent) {
        if (!allow360Effect) return;

        const target = e.currentTarget as HTMLElement;

        const round2 = (v: number) => Math.round(v * 100) / 100;

        const cardWidth = target.clientWidth;
        const cardHeight = target.clientHeight;

        const mouseX = e.offsetX;
        const mouseY = e.offsetY;

        // Normalize mouse position (-1 to 1 range)
        const normX = (mouseX - cardWidth / 2) / (cardWidth / 2);
        const normY = (mouseY - cardHeight / 2) / (cardHeight / 2);

        const limit = 2;

        moveX = round2(normX * limit);
        moveY = round2(normY * -limit);

        // Mouse position in percentage
        const percentMouseX = (mouseX * 100) / cardWidth;
        const percentMouseY = (mouseY * 100) / cardHeight;

        const distanceToCenterX = Math.abs(percentMouseX - 50) / 50;
        const distanceToCenterY = Math.abs(percentMouseY - 50) / 50;

        // Screen-based factor
        const cardFactorY = e.clientY / window.innerHeight;
        const cardFactorX = e.clientX / window.innerWidth;

        /* ---------------------------
           Y Light reflections
        --------------------------- */

        pointOneY = percentMouseY;
        pointTwoY = percentMouseY;

        pointOneYOpacity =
            distanceToCenterY *
            (cardFactorY * (percentMouseY / 100) +
                (1 - cardFactorY) * (1 - percentMouseY / 100));

        pointTwoYOpacity = pointOneYOpacity;

        /* ---------------------------
           X Light reflections
        --------------------------- */

        pointOneX = percentMouseX;
        pointTwoX = percentMouseX;

        pointOneXOpacity =
            distanceToCenterX *
            (cardFactorX * (percentMouseX / 100) +
                (1 - cardFactorX) * (1 - percentMouseX / 100));

        pointTwoXOpacity = pointOneXOpacity;

        // Adjust fingerprint opacity dynamically
        fingerPrintsOpacity =
            0.3 + ((100 - percentMouseY) / 100) * (1 - 0.3);


        /* ---------------------------
           X Light reflections
        --------------------------- */

        pointerX = percentMouseX;
        pointerY = percentMouseY;

        const distanceToCenter = Math.sqrt(
            Math.pow(percentMouseX - 50, 2) +
            Math.pow(percentMouseY - 50, 2)
        ) / 50;
        
        pointerFromCenter = Math.min(distanceToCenter, 1);
        backgroundX = percentMouseX / 4;
        backgroundY = percentMouseY / 4;

        cardOpacity = 1;
    }

    

    function handleMouseLeave() {
        // Reset movement
        moveX = 0;
        moveY = 0;

        // Reset reflections
        pointOneYOpacity = 0;
        pointTwoYOpacity = 0;
        pointOneXOpacity = 0;
        pointTwoXOpacity = 0;

        // Reset fingerprint overlay
        fingerPrintsOpacity = 0.3;

        backgroundY = 0;
        backgroundX = 0;
        pointerFromCenter = 0;

        cardOpacity = 0;
    }

    /* -----------------------------------------------------
       IMAGE LOADING
    ----------------------------------------------------- */

    function handleImageLoad() {
        setTimeout(() => {
            isImageLoading = false;
        }, 300);
    }

    /* -----------------------------------------------------
       DERIVED VALUES
    ----------------------------------------------------- */

    let imgSrc = $derived.by(() =>
        data.image && data.image !== ''
            ? data.image
            : '/images/cards/placeholder.jpg'
    );

    $effect(() => {
        if (imgSrc) {
            isImageLoading = true;
        }
    });
</script>

<div class="outer" style={`--perspective:${perspective}px;`}>
    {#if children && showActions}
        <div
            transition:scale
            role="dialog"
            tabindex="0"
            onfocus={() => showActions = true}
            onmouseover={() => showActions = true}
            class="actions-out-wrapper"
        >
            {@render children?.()}
        </div>
    {/if}
    <svelte:element
        this={role}
        {...HTMLProps}
        class={`card-container card theme-${data.first_element?.label ? formatHandle(data.first_element.label): 'default'}`}
        onmousemovecapture={(e:MouseEvent) => handleMouseCapture(e)}
        onmouseleave={handleMouseLeave}
        data-theme={formatHandle(data.first_element?.label)}
        data-has-rarity={hasRarity}
        data-rarity={DATA_RARITY}
        data-supertype="pokémon"
        style={`--x: ${moveX}; --y: ${moveY};`}
    >
        <div class="card-wrapper">
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

            {#if isImageLoading && showLoader}
                <div out:blur class="loader">
                    <Spinner />
                </div>
            {/if}

            <img
                class="cardboard"
                src="/images/card-mask.svg"
                alt=""
            />

            <img
                class="art"
                src={imgSrc}
                alt={data.name}
                width="300"
                onload={handleImageLoad}
                draggable="false"
            />

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
                    --pointer-x: ${pointerX}%;
                    --pointer-y: ${pointerY}%;
                    --pointer-from-center: ${Math.max(.5, pointerFromCenter)};
                    --background-x: ${backgroundX}%;
                    --background-y: ${backgroundY}%;
                    --card-opacity: ${Math.max(.5, cardOpacity)};
                `}
            >
                <div class="lateral-lights"></div>
                <div class="finger-prints" style={`background: url('/images/finger-prints/${(key % 4) + 1}.jpg');`}></div>
                {#if hasRarity}
                    <div class="card__shine"></div>
                {/if}
            </div>
        </div>
    </svelte:element>
</div>

<style lang="scss">
    @use "../../styles/abstracts/variables" as variables;
    @use "../../styles/abstracts/mixins" as mixins;
    @use "../../styles/abstracts/functions" as functions;

    .outer {
        position: relative;
        perspective: var(--perspective);
    }

    .actions-out-wrapper {
        position: absolute;
        width: auto;
        height: auto;
        left: 50%;
        bottom: 0;
        transform: translateX(-50%) translateY(50%);
        z-index: 2;

        @include mixins.transition(all, .4s);

    }

    a.card-container,
    button.card-container {
        cursor: pointer;
    }

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

            img {
                width: 100%;
                height: 100%;
                pointer-events: none;

                &.cardboard {
                    opacity: 0;
                    pointer-events: none;
                }

                &.art {
                    position: absolute;
                    inset: 0;
                    z-index: 0;
                    object-fit: cover;
                }
            }

            .loader {
                position: absolute;
                inset: 0;
                background-color: var(--color-creature-loader-background);
                z-index: 1;

                @include mixins.displayFlex(column, 0, center, center, nowrap);
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
                z-index: 1;
                pointer-events: none;

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
                z-index: 1;
                will-change: opacity;
                pointer-events: none;

                @include mixins.displayFlex(row, 20, space-between, flex-start, nowrap);
                @include mixins.transition(opacity, 0.3s);

                .elements,
                .classification {
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
                        width: 100%;
                        height: 100%;
                        filter: drop-shadow(0 0 functions.rem(20) var(--color-element));
                    }
                }
            }

            .effects {
                position: absolute;
                inset: 0;
                box-shadow:
                    0 functions.rem(2) functions.rem(6) functions.rem(-2) var(--color-creature-card-light-top) inset,
                    0 functions.rem(-2) functions.rem(8) functions.rem(1) var(--color-creature-card-light-bottom) inset;

                .finger-prints {
                    width: 100%;
                    height: 100%;
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
                    inset: 0;

                    &::before,
                    &::after {
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

                &::before,
                &::after {
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

        }

        &:hover .card-wrapper .hover-info {
            opacity: 1;
        }
    }

    .card-container {
        --grain: url("/images/card-effects/grain.webp");
        --glitter: url("/images/card-effects/glitter.png");
        --glittersize: 25%;

        --space: 5%;
        --angle: 133deg;
        --imgsize: cover;

        --red: #f80e35;
        --yellow: #eedf10;
        --green: #21e985;
        --blue: #0dbde9;
        --violet: #c929f1;
    }

    .card__shine {
        position: absolute;
        inset: 0;
        pointer-events: none;

        will-change: transform, opacity, background-image, background-size,
        background-position, background-blend-mode, filter;
    }
 
</style>

