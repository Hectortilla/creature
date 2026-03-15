<script lang="ts">
    import { formatHandle } from '$lib/utils/formatHandle';

    interface Props {
        name?: string,
        data: { value:string, icon:string }[],
        group: string,
    }
    let {
        name = 'selector',
        data,
        group = $bindable(""),
    }: Props = $props();

</script>


<div class={`icon-selector`}>
    {#each data as {value, icon}}
        <div class="input-wrapper">
            <input
                type="radio"
                id={formatHandle(value)}
                name={name}
                bind:group={group}
                value={formatHandle(value)}  
                checked={group === formatHandle(value)} 
            />
            <label
                for={formatHandle(value)}
            >
                <span>
                    {@html icon}
                </span>
            </label>
        </div>
    {/each}
</div>

<style lang="scss">
    @use "../../styles/abstracts/variables" as variables;
	@use "../../styles/abstracts/mixins" as mixins;
	@use "../../styles/abstracts/functions" as functions;

    .icon-selector{
        $button-width: 32;
        $button-icon-size: 18;

        width: max-content;
        position: relative;
        background-color: black;
        border-radius: functions.rem(variables.$input-radius);
        overflow: hidden;

        @include mixins.displayFlex(row, 0, flex-start, center, nowrap);

        .input-wrapper {
            position: relative;

            // To have functional fillings
            &:first-child label {
                box-sizing: content-box;
                padding-left: functions.rem(6);
            }
            &:last-child label {
                box-sizing: content-box;
                padding-right: functions.rem(6);
            }

            input {
                position: absolute;
                top: 0;
                left: 0;
                width: 0;
                height: 0;
                pointer-events: none;
                opacity: 0;
            }

            label {
                display: block;
                width: functions.rem($button-width);
                height: functions.rem(variables.$input-height);
                color: var(--color-icon-button-color);
                filter: saturate(.4);
                opacity: .6;
                cursor: pointer;

                @include mixins.transition(all, .4s);
                @include mixins.displayFlex(row, 0, center, center, nowrap);

                span {
                    width: functions.rem($button-icon-size);
                    height: functions.rem($button-icon-size);
                }
            }

            input:checked ~label {
                cursor: default;
                pointer-events: none;
                filter: saturate(1);
                opacity: 1;
            }
        }
    }
</style>