<script lang="ts">
    import { onMount } from "svelte";

    // Components
    import StylishedText from "$lib/components/StylishedText.svelte";
	import SelectorMark from "$lib/components/SelectorMark.svelte";

    interface Props {
        index?: number;
        text: string;
        amount?: number;
        amount_label?: string;
        image?: string;
        link?: string;
        onClick?: () => void;
    }

    let {
        index = 0,
        text = "My Cards",
        amount = 0,
        amount_label = "cards",
        image = "cards",
        link = "/my-collection/cards",
        onClick,
    }: Props = $props();

    let isLoaded = $state(false);

    onMount(() => {
        // Staggered animation effect
        setTimeout(() => {
            isLoaded = true;
        }, (index + 1) * 100);
    });
</script>

<svelte:element
    class="collection-card"
    class:is-loaded={isLoaded}
    this={link ? "a" : "button"}
    href={link}
    aria-label={text}
    role="button"
    tabindex="0"
    onclick={onClick}
>
    <div class="selector-mark-container">
        <SelectorMark size={30} />
    </div>
    <div class="image-wrapper">
        <picture>
            <source
                srcset={`
                    /images/collection/card-${image}-back.png 1x,
                    /images/collection/card-${image}-back@2x.png 2x,
                    /images/collection/card-${image}-back@3x.png 3x
                `}
            />
            <img
                src={`/images/collection/card-${image}-back.png`}
                alt={`Back of ${text}`}
                loading="lazy"
                decoding="async"
            />
        </picture>
        <div class="masked">
            <img src={`/images/collection/card-${image}-front.png`} alt={`Front of ${text}`} />
            <picture>
                <source
                    srcset={`
                        /images/collection/card-${image}-front.png 1x,
                        /images/collection/card-${image}-front@2x.png 2x,
                        /images/collection/card-${image}-front@3x.png 3x
                    `}
                />
                <img
                    src={`/images/collection/card-${image}-front.png`}
                    alt={`Front of ${text}`}
                    loading="lazy"
                    decoding="async"
                />
            </picture>
        </div>
    </div>
    <div class="text-wrapper">
        <StylishedText text={text} fontSize={40} />
        <div class="collection-card__amount">
            {amount} {amount_label}
        </div>
    </div>
</svelte:element>

<style lang="scss">
    @use "../../styles/abstracts/variables" as variables;
    @use "../../styles/abstracts/mixins" as mixins;
	@use "../../styles/abstracts/functions" as functions;

    .collection-card {
        position: relative;
        width: 100%;
        max-width: functions.rem(400);
        min-width: functions.rem(300);
        opacity: 0;
        cursor: pointer;

        @include mixins.transition(.6s);
        @include mixins.displayFlex(column, 40, center, center, nowrap);

        .selector-mark-container {
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%) translateY(-50%);
            z-index: 1;
            opacity: 0;

            @include mixins.transition(.3s);
        }

        .image-wrapper {
            position: relative;
            width: 100%;
            height: auto;
            overflow: hidden;

            img {
                width: 100%;
                height: auto;
                display: block;
            }

            .masked {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                mask-image: url("/images/collection-mask.svg");
                mask-repeat: no-repeat;
                mask-position: center;
                mask-size: cover;

                img {
                    width: 100%;
                    height: auto;
                    display: block;
                    transform: translateY(functions.rem(-40)) scale(1.02);

                    @include mixins.transition(.6s);
                }
            }
        }

        .text-wrapper {
            width: 100%;
            text-align: center;
            transform: translateY(functions.rem(20));
            opacity: 0;

            @include mixins.transition(.6s);
            @include mixins.displayFlex(column, 0, center, center, nowrap);
        }

        &.is-loaded {
            opacity: 1;

            .masked img {
                transform: translateY(0) scale(1);
            }

            .text-wrapper {
                transform: translateY(functions.rem(0));
                opacity: 1;
            }
        }

        &:hover,
        &:focus {
            outline: none;

            .masked img {
                transform: translateY(functions.rem(-20)) scale(1.02);
            }

            .selector-mark-container {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }
    }
</style>