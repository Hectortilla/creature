<script lang="ts">
    import { formatHandle } from '$lib/utils/formatHandle';
    import { fade } from "svelte/transition"

    // Icons
    import searchIcon from "$lib/assets/icons/search.svg?raw"
    import refreshIcon from "$lib/assets/icons/refresh.svg?raw"

    interface Props {
        placeholder: string,
        value: string,
    }
    let {
        placeholder,
        value = $bindable(""),
    }: Props = $props();

    /**
     * Reset input value
     */
    function resetValue() {
        value = "";
    }
</script>

<div class="input-wrapper">
    <div class="icon-search">{@html searchIcon}</div>
    <input
        type="search"
        id={formatHandle(placeholder)}
        bind:value
        placeholder={placeholder}
        autocomplete="off"
        autocorrect="off"
        autocapitalize="off"
    />
    {#if value !== ''}
        <button
            transition:fade
            class="icon-reset"
            aria-label={`Reset ${placeholder}`}
            onclick={() => resetValue()}
        >
            {@html refreshIcon}
        </button>
    {/if}
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .input-wrapper {
        $padding-reset: functions.rem(6);

        position: relative;
        flex: 1;
        max-width: functions.rem(500);

        input {
            // reset
            border: none;
            outline: none;

            width: 100%;
            height: functions.rem(variables.$input-height);
            padding: 0 calc(functions.rem(variables.$input-padding) + (functions.rem(variables.$input-height) - ($padding-reset * 2))) 0 functions.rem(variables.$input-height);
            border-radius: functions.rem(variables.$input-radius);
            font-size: functions.rem(variables.$input-font-size);
            background: var(--color-input-search-background);
            color: var(--color-input-text);
            overflow: hidden;
            backdrop-filter: blur(functions.rem(10));

            @include mixins.transition;

            &::placeholder {
                color: var(--color-input-placeholder);
            }

            &::-webkit-search-cancel-button {
                -webkit-appearance: none;
            }
        }

        .icon-search {
            position: absolute;
            top: $padding-reset;
            left: $padding-reset;
            width: calc(functions.rem(variables.$input-height) - ($padding-reset * 2));
            height: calc(functions.rem(variables.$input-height) - ($padding-reset * 2));
            padding: functions.rem(10);
            z-index: 1;
            pointer-events: none;
        }

        .icon-reset {
            position: absolute;
            top: $padding-reset;
            right: $padding-reset;
            width: calc(functions.rem(variables.$input-height) - ($padding-reset * 2));
            height: calc(functions.rem(variables.$input-height) - ($padding-reset * 2));
            padding: functions.rem(10);
            border-radius: calc(functions.rem(variables.$input-radius) - $padding-reset);
            cursor: pointer;
            will-change: opacity, box-shadow;
            
            @include mixins.transition;

            &:hover {
                background-color: var(--color-input-button-background);
                color: var(--color-input-button-light-top);
                box-shadow:
                    0 functions.rem(2) functions.rem(4) functions.rem(-2) var(--color-input-button-light-top) inset,
                    0 functions.rem(-2) functions.rem(6) functions.rem(1) var(--color-input-button-light-bottom) inset;
            }
        }
    }
</style>