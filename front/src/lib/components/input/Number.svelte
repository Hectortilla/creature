<script lang="ts">
    import { formatHandle } from "$lib/utils/formatHandle"

    // Icons
    import plusIcon from "$lib/icons/plus.svg?raw"
    import minusIcon from "$lib/icons/minus.svg?raw"
    import infoIcon from "$lib/icons/info.svg?raw"

    interface Props {
        label: string;
        value: number;
        error: boolean;
        maxValue: number;
        minValue: number;
        step: number;
        isMandatory: boolean;
        isDisabled: boolean;
        showInfo?: boolean;
        children?: any
    }

    let {
        label,
        value = $bindable(0),
        error = false,
        maxValue = 9999,
        minValue = 1,
        step = 1,
        isMandatory = false,
        isDisabled = true,
        showInfo = false,
        children
    }: Props = $props();

    let maxValueLenght = $state(Math.abs(maxValue).toString().length);

    /**
     * Handle value
     */
    const handleChangeValue = (v: number) => {
        error = false;

        if (!v) {
            value = minValue;
            return;
        }

        if (v < minValue) {
            value = minValue;
            return;
        }
        if (v > maxValue) {
            value = maxValue;
            return;
        }

        const remainder = (v - minValue) % step;
        if (remainder !== 0) {
            value = v - remainder + (remainder >= step / 2 ? step : 0);
        }
    }

    const handleInputValue = (v: number) => {
        const remainder = (v - minValue) % step;

        if (!v || v < minValue || v > maxValue || remainder !== 0) {
            error = true;
            return;
        }
        error = false;
    }

    function handleIncrementValue() {
        const result = Math.min(maxValue, value + step);

        if (result > maxValue) {
            value = maxValue
        } else {
            value = result;
        }
        
    }

    function handleDecrementValue() {
        const result = Math.min(maxValue, value - step);

        if (result < minValue) {
            value = minValue
        } else {
            value = result;
        }
    }

</script>
<div class="input-container number" class:disabled={isDisabled}>
    <div class="label-wrapper">
        <label for={formatHandle(label)}>
            {#if children}
                <div class="icon">
                    {@render children?.()}
                </div>
            {/if}
            {label}
            {#if isMandatory}
                <span>*</span>
            {/if}
            {#if showInfo}
                <div class="info-hover">
                    <div class="icon">
                        {@html infoIcon}
                        <div class="hover-wrapper">
                            <p>Max: {maxValue}</p>
                            <p>Step: {step}</p>
                        </div>
                    </div>
                </div>
            {/if}
        </label>
    </div>
    <div class="input-number-container" class:error>
        <button
            onclick={() => {handleDecrementValue()}}
            disabled={value <= minValue || isDisabled}
            class:disabled={value <= minValue || isDisabled}
        >
            {@html minusIcon}
        </button>
        <input
            id={formatHandle(label)}
            type="number"
            class:error
            min={minValue}
            max={maxValue}
            step={step}
            style={`--size-m:${maxValueLenght}`}
            bind:value
            onchange={() => {handleChangeValue(value)}}
            oninput={() => {handleInputValue(value)}}
            autocomplete="off"
            autocorrect="off"
            autocapitalize="off"
        />
        <button
            onclick={() => {handleIncrementValue()}}
            disabled={value >= maxValue || isDisabled}
            class:disabled={value >= maxValue || isDisabled}
        >
            {@html plusIcon}
        </button>
    </div>
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .input-number-container {
        $padding: functions.rem(4);

        border-radius: functions.rem(variables.$input-radius);
        overflow: hidden;
        border: solid 1px var(--color-input-border);
        padding: $padding;

        @include mixins.displayFlex(row, 3, flex-start, flex-start, nowrap);
        @include mixins.transition;

        &.error {
            border-color: var(--color-input-text-error);
            box-shadow: 0 0 functions.rem(20) functions.rem(-14) functions.color(semantic, error);
        }
    
        input {
            // reset
            border: none;
            outline: none;

            width: calc(functions.rem(40) + (functions.rem(12) * var(--size-m)));
            min-width: functions.rem(60);
            height: calc(functions.rem(variables.$input-height) - ($padding * 2));
            padding: 0 functions.rem(variables.$input-padding);
            border-radius: functions.rem(variables.$input-radius);
            font-size: functions.rem(variables.$input-font-size);
            background: transparent;
            color: var(--color-input-text);
            text-align: center;

            @include mixins.transition;

            // Delete browser arrows
            &::-webkit-inner-spin-button,
            &::-webkit-outer-spin-button {
                -webkit-appearance: none;
                margin: 0;
            }

            &.error {
                box-shadow: 0 0 functions.rem(40) functions.rem(-24) var(--color-input-text-error) inset;
                color: var(--color-input-text-error);
            }
        }

        button {
            width: calc(functions.rem(variables.$input-height) - ($padding * 2));
            height: calc(functions.rem(variables.$input-height) - ($padding * 2));
            padding: functions.rem(12);
            border-radius: calc(functions.rem(variables.$input-radius) - $padding);
            background-color: var(--color-input-button-background);
            color: var(--color-input-button-light-top);
            cursor: pointer;
            will-change: opacity, box-shadow;
            box-shadow:
                0 functions.rem(2) functions.rem(4) functions.rem(-2) var(--color-input-button-light-top) inset,
                0 functions.rem(-2) functions.rem(6) functions.rem(1) var(--color-input-button-light-bottom) inset;

            @include mixins.displayFlex(row, 0, center, center, nowrap);
            @include mixins.transition;

            &:hover {
                color: var(--color-input-button-light-top);
                box-shadow:
                    0 functions.rem(-2) functions.rem(4) functions.rem(-2) var(--color-input-button-light-top) inset,
                    0 functions.rem(2) functions.rem(6) functions.rem(1) var(--color-input-button-light-bottom) inset;
            }

            &:disabled, &.disabled {
                opacity: .4;
                box-shadow: none;
            }
        }
    }
</style>