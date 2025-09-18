<script lang="ts">
    import { formatHandle } from "$lib/utils/formatHandle";
    interface Props {
        type: "primary" | "secondary";
        link?: string | boolean;
        text: string;
        isDisabled: boolean;
        onClick?:() => void;
    }

    let {
        type = "primary",
        link = false,
        text = "Button",
        isDisabled = false,
        onClick
        
    }: Props = $props();
</script>

{#if link && typeof link === 'string'}
    <a
        href={link}
        aria-label={text}
        class={`button ${type}`}
        class:disabled={isDisabled}
    >
        {text}
    </a>
{:else}
    <button
        aria-label={formatHandle(text)}
        class={type}
        class:disabled={isDisabled}
        disabled={isDisabled}
        onclick={onClick}
    >
        {text}
    </button>
{/if}

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    button, .button {
        width: auto;
        height: functions.rem(variables.$input-height);
        padding: functions.rem(20);
        border-radius: functions.rem(variables.$input-radius);
        background-color: var(--color-input-button-background);
        color: var(--color-input-button-light-top);
        cursor: pointer;
        will-change: opacity, box-shadow;

        @include mixins.displayFlex(row, 0, center, center, nowrap);
        @include mixins.transition;

        &.primary {
            background-color: var(--color-button-primary-background);
            color: var(--color-button-primary-text);
            box-shadow:
                0 functions.rem(20) functions.rem(40) functions.rem(-20) transparent;

            &:hover {
                box-shadow:
                    0 functions.rem(20) functions.rem(40) functions.rem(-20) var(--color-button-primary-background);
            }
        }

        &.secondary {
            background-color: var(--color-button-secondary-background);
            box-shadow:
                0 functions.rem(2) functions.rem(4) functions.rem(-2) var(--color-input-button-light-top) inset,
                0 functions.rem(-2) functions.rem(6) functions.rem(1) var(--color-input-button-light-bottom) inset;

            &:hover {
                color: var(--color-input-button-light-top);
                box-shadow:
                    0 functions.rem(-2) functions.rem(4) functions.rem(-2) var(--color-input-button-light-top) inset,
                    0 functions.rem(2) functions.rem(6) functions.rem(1) var(--color-input-button-light-bottom) inset;
            }
        }

        &:disabled, &.disabled {
            opacity: .4;
            box-shadow: none;
            pointer-events: none;
        }
    }
</style>