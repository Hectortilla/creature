<script lang="ts">
	import { FONT_BASE_SIZE } from "$lib/constants";
	import type { Snippet } from "svelte";

    interface Props {
        link?: string;
        ariaLabel?: string;
        rotateIcon?: number;
        isDisabled?: boolean;
        size?: number;
        theme?: 'light' | 'dark';
        children: Snippet;
        onClick?: () => void;
    }

    let {
        link,
        ariaLabel = 'Action',
        rotateIcon = 0,
        isDisabled,
        size = 28,
        theme = 'light',
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
    class={`${theme}`}
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
        cursor: pointer;

        @include mixins.displayFlex(row, 0, center, center, nowrap);
        @include mixins.transition(.4s);

        span {
            flex-shrink: 0;
            width: 50%;
            height: 50%;
            display: block;
            position: relative;
            transform: rotate(var(--rotate-icon));
        }

        &.disabled,
        :disabled {
            opacity: .4;
            pointer-events: none;
            box-shadow: none;
        }

        &.light {
            background-color: var(--color-icon-button-light-background);
            color: var(--color-icon-button-color);

            box-shadow: inset 0 functions.rem(-1) functions.rem(8) functions.rem(-3) var(--color-highlight);
            backdrop-filter: blur(functions.rem(8));

            &:not(.disabled):hover {
                box-shadow: inset 0 functions.rem(-1) functions.rem(8) functions.rem(-1) var(--color-highlight);
            }
        }

        &.dark {
            background-color: var(--color-icon-button-dark-background);
            color: var(--color-icon-button-color);

            backdrop-filter: blur(functions.rem(8));

            &:not(.disabled):hover {
                background: var(--color-icon-button-dark-background-hover);
            }
        }
    }
</style>