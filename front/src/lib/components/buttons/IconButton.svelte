<script lang="ts">
	import { FONT_BASE_SIZE } from "$lib/constants";
	import type { Snippet } from "svelte";

    interface Props {
        link?: string;
        ariaLabel?: string;
        rotateIcon?: number;
        isDisabled?: boolean;
        size?: number;
        children: Snippet;
        onClick?: () => void;
    }

    let {
        link,
        ariaLabel = 'Action',
        rotateIcon = 0,
        isDisabled,
        size = 28,
        children,
        onClick,
    }: Props = $props();

</script>

<svelte:element
    this={link ? 'a' : 'button'}
    role="button"
    tabindex="0"
    aria-label={ariaLabel}
    href={link}
    onclick={onClick}
    class:disabled={isDisabled}
    disabled={isDisabled}
    style={`
        --rotate-icon:${rotateIcon}deg;
        --size:${size / FONT_BASE_SIZE}rem
    `}
>   
    <span>
        {@render children?.()}
    </span>
</svelte:element>

<style lang="scss">
    @use "../../../lib/styles/abstracts/variables" as variables;
    @use "../../../lib/styles/abstracts/mixins" as mixins;
	@use "../../../lib/styles/abstracts/functions" as functions;

    a, button {
        width: var(--size);
        height: var(--size);
        border-radius: 100%;
        background-color: var(--color-icon-button-background);
        color: var(--color-icon-button-color);
        cursor: pointer;

        box-shadow: inset 0 functions.rem(-1) functions.rem(8) functions.rem(-3) var(--color-highlight);
        backdrop-filter: blur(functions.rem(8));

        @include mixins.displayFlex(row, 0, center, center, nowrap);
        @include mixins.transition(.4s);

        span {
            width: 50%;
            height: 50%;
            display: block;
            position: relative;
            transform: rotate(var(--rotate-icon));
        }

        &:not(.disabled):hover {
            box-shadow: inset 0 functions.rem(-1) functions.rem(8) functions.rem(-1) var(--color-highlight);
        }

        &.disabled,
        :disabled {
            opacity: .4;
            pointer-events: none;
            box-shadow: none;
        }
    }
</style>