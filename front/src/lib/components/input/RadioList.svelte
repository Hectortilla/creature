<script lang="ts">
    import { formatHandle } from "$lib/utils/formatHandle"

    // Icons
    import physical from "$lib/icons/physical-type.svg?raw"
    import magical from "$lib/icons/magical-type.svg?raw"

    // Tipado de props
    type IconName = string | "physical" | "magical";

    interface Props {
        label: string;
        group: boolean | string,
        list: { label: string; value: boolean | string, icon?: IconName }[];
        isMandatory: boolean;
    }

    let {
        label,
        group = $bindable(false),
        list,
        isMandatory = false
    }: Props = $props();

    // Mapa de iconos
    const icons: Record<IconName, string> = {
        physical,
        magical
    };

</script>

<div class="input-container">
    <div class="label-wrapper">
        <label for={formatHandle(label)}>
            {label}
            {#if isMandatory}
                <span>*</span>
            {/if}
        </label>
    </div>
    <div class="input-wrapper">
        {#each list as item}
            <input
                type="radio"
                name={formatHandle(item.label)}
                id={formatHandle(item.label)}
                value={item.value}
                bind:group={group}
            >
            <label for={formatHandle(item.label)}>
                {#if item.icon}
                    <span class="icon">
                        {@html icons[item.icon]}
                    </span>
                {/if}
                {item.label}
            </label>
        {/each}
    </div>
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .input-wrapper {
        @include mixins.displayFlex(row, 6, flex-start, flex-end, nowrap);

        input {display:none;}
        label {
            width: auto;
            min-width: functions.rem(80);
            height: functions.rem(variables.$input-height);
            padding: 0 functions.rem(variables.$input-padding);
            background-color: var(--color-input-button-background);
            border-radius: functions.rem(variables.$input-radius);
            will-change: background-color;
            cursor: pointer;

            @include mixins.displayFlex(row, 4, center, center, nowrap);
            @include mixins.transition;

            &:hover {
                box-shadow:
                    0 functions.rem(2) functions.rem(4) functions.rem(-2) var(--color-input-button-light-top) inset,
                    0 functions.rem(-2) functions.rem(6) functions.rem(1) var(--color-input-button-light-bottom) inset;
            }

            span.icon {
                width: functions.rem(16);
                height: functions.rem(16);
            }
        }

        input:checked + label {
            background-color: var(--color-input-border);
            pointer-events: none;
        }
    }
</style>