<script lang="ts">
    import { formatHandle } from "$lib/utils/formatHandle"
    import { fade } from "svelte/transition"

    // Icons
    import refreshIcon from "$lib/assets/icons/refresh.svg?raw"

    interface Props {
        type: "text" | "textarea";
        label: string;
        value: string | null;
        error: boolean;
        placeholder: string;
        maxLength: number;
        minLength: number;
        isMandatory: boolean;
    }

    let {
        label,
        type = "text",
        value = $bindable(''),
        error = false,
        maxLength = 9999,
        minLength = 1,
        isMandatory = false,
        placeholder
    }: Props = $props();

    let isAlmostMaxLength = $state(false);
    let isMaxLength = $state(false);

    /**
     * Reset input value
     */
    function resetValue() {
        value = "";
    }

</script>

<div class="input-container text">
    <div class="label-wrapper">
        <label for={formatHandle(label)}>
            {label}
            {#if isMandatory}
                <span>*</span>
            {/if}
        </label>
        <p
            class="message"
            class:warning={value ? value.length >= maxLength - (maxLength / 4) : false}
            class:max={value ? value.length === maxLength : false}
        >
            {value ? value.length: 0}/{maxLength}
        </p>
    </div>
    <div class="input-wrapper">
        {#if type === "textarea"}
            <textarea
                id={formatHandle(label)}
                class:error
                class:warning={value ? value.length >= maxLength - (maxLength / 4) : false}
                class:max={value ? value.length === maxLength : false}
                placeholder={placeholder}
                maxlength={maxLength}
                minlength={minLength}
                bind:value
                autocomplete="off"
                autocapitalize="off"
            ></textarea>
        {:else}
            <input
                id={formatHandle(label)}
                type={type}
                class:error
                class:warning={value ? value.length >= maxLength - (maxLength / 4): false}
                class:max={value ? value.length === maxLength: false}
                placeholder={placeholder}
                maxlength={maxLength}
                minlength={minLength}
                bind:value
                autocomplete="off"
                autocorrect="off"
                autocapitalize="off"
            />
        {/if}
        {#if value !== ''}
            <button
                transition:fade
                class="icon-reset"
                aria-label={`Reset ${label}`}
                onclick={() => resetValue()}
            >
                {@html refreshIcon}
            </button>
        {/if}
    </div>
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .input-wrapper {
        $padding-reset: functions.rem(6);

        position: relative;
        width: 100%;

        input {
            height: functions.rem(variables.$input-height);
            padding: 0 calc(functions.rem(variables.$input-padding) + (functions.rem(variables.$input-height) - ($padding-reset * 2))) 0 functions.rem(variables.$input-padding);
        }

        textarea {
            max-height: functions.rem(100);
            padding:
                functions.rem(variables.$input-padding)
                calc(functions.rem(variables.$input-padding) + (functions.rem(variables.$input-height) - ($padding-reset * 2)))
                functions.rem(variables.$input-padding)
                functions.rem(variables.$input-padding);
            resize: none;
        }

        input, textarea {
            // reset
            border: none;
            outline: none;

            width: 100%;
            border-radius: functions.rem(variables.$input-radius);
            font-size: functions.rem(variables.$input-font-size);
            background: transparent;
            color: var(--color-input-text);
            overflow: hidden;
            border: solid 1px var(--color-input-border);

            @include mixins.transition;

            // Delete browser arrows
            &::-webkit-inner-spin-button,
            &::-webkit-outer-spin-button {
                -webkit-appearance: none;
                margin: 0;
            }

            &.error {
                box-shadow: 0 0 functions.rem(40) functions.rem(-24) functions.color(semantic, error) inset;
                color: functions.color(semantic, error);
            }

            &.warning {
                color: var(--color-input-text-warning);
            }

            &.max {
                color: var(--color-input-text-max);
            }

            &::placeholder {
                color: var(--color-input-placeholder);
            }
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