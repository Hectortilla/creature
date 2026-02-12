<script lang="ts">
	import type { Snippet } from "svelte";

    interface Props {
        link?: string;
        ariaLabel?: string;
        rotateIcon?: number;
        isDisabled?: boolean;
        children: Snippet;
        onClick?: () => void;
    }

    let {
        link,
        ariaLabel = 'Action',
        rotateIcon = 0,
        isDisabled,
        children,
        onClick,
    }: Props = $props();

</script>

<svelte:element
    this={link ? 'a' : 'button'}
    role="button"
    tabindex="0"
    aria-label={ariaLabel}
    onclick={onClick}
    class:disabled={isDisabled}
    disabled={isDisabled}
>   
    <span style={`--rotate-icon:${rotateIcon}deg`}>
        {@render children?.()}
    </span>
</svelte:element>

<style lang="scss">
    @use "../../../lib/styles/abstracts/variables" as variables;
    @use "../../../lib/styles/abstracts/mixins" as mixins;
	@use "../../../lib/styles/abstracts/functions" as functions;

    a, button {
        width: functions.rem(28);
        height: functions.rem(28);
        border-radius: 100%;
        background-color: var(--color-icon-button-background);
        color: var(--color-icon-button-color);
        cursor: pointer;

        box-shadow: inset 0 functions.rem(-1) functions.rem(8) functions.rem(-3) var(--color-highlight);

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