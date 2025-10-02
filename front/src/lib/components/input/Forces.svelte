<script lang="ts">
    import type { Element } from "$lib/types";
    import { slide } from "svelte/transition"

    // Components
    import InputNumber from "$lib/components/input/Number.svelte";
    import Select from "$lib/components/input/Select.svelte"
    import Button from "$lib/components/Button.svelte"

    // Icons
    import closeIcon from "$lib/icons/plus.svg?raw";

    interface Forces {
        element: number;
        value: number;
    }

    interface Props {
        forces: Forces[];
        elements: Element[];
    }

    let {
        forces = $bindable([]),
        elements

    }: Props = $props();

    const maxTotalForces = 8;
    let totalForcesAdded = $state(0);

    // Estado temporal para crear un nuevo force
    let newForceValue = $state<number>(0);
    let newForceElementId = $state<number | null>(null);

    function addForce() {
        if (newForceElementId === null) return;

        // Si ya existe un force con el mismo elemento → lo filtramos fuera
        forces = [
            ...forces.filter(f => f.element !== newForceElementId),
            { element: newForceElementId, value: newForceValue }
        ];

        // Reset después de añadir
        newForceValue = 0;
        newForceElementId = null;
    }

    function removeForce(index: number) {
        forces = forces.filter((_, i) => i !== index);
    }

    $effect(() => {
        totalForcesAdded = forces.reduce((acc, force) => acc + force.value, 0);
    });

</script>


<div class="forces-container">
    <div class="add-force">
        <InputNumber
            label="Fuerza"
            bind:value={newForceValue}
            error={false}
            minValue={1}
            maxValue={maxTotalForces - totalForcesAdded}
            step={1}
            isMandatory={true}
            isDisabled={totalForcesAdded === maxTotalForces}
            showInfo={true}
        />
        <Select
            label="Elemento de fuerza"
            list={elements}
            iconType="image"
            isMandatory={true}
            isDisabled={totalForcesAdded === maxTotalForces}
            bind:group={newForceElementId}
        />
        <Button
            type="secondary"
            text="Añadir fuerza"
            onClick={addForce}
            isDisabled={newForceValue <= 0 || typeof newForceElementId !== 'number' }
        />
    </div>
    {#if forces.length > 0}
        <div transition:slide class="foces-added-wrapper">
            <p class="title">Fuerzas añadidas {totalForcesAdded}/{maxTotalForces}</p>
            <ul class="forces-added">
                {#each forces as force, i}
                    <li style={`--element-color:#${elements.find(e => e.id === force.element)?.color}26;`}>
                        <img src={elements.find(e => e.id === force.element)?.icon} alt={elements.find(e => e.id === force.element)?.label}/>
                        <p>{force.value}</p>
                        <button
                            type="reset"
                            onclick={() => removeForce(i)}
                            aria-label={`Eliminar fuerza ${elements.find(e => e.id === force.element)?.label}`}
                        >
                            <span>{@html closeIcon}</span>
                        </button>
                    </li>
                {/each}
            </ul>
        </div>
    {/if}
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .forces-container {
        width: 100%;
        @include mixins.displayFlex(column, 40, flex-start, flex-start, nowrap);

        .add-force {
            width: 100%;
            @include mixins.displayFlex(row, 20, flex-start, flex-end, wrap);
        }

        .title {
            font-size: functions.rem(14);
            color: var(--color-divider-text);
            padding: 0 functions.rem(10);
        }

        .foces-added-wrapper {
            width: 100%;
            @include mixins.displayFlex(column, 10, flex-start, flex-start, nowrap);

            ul.forces-added {
                width: 100%;
                border-radius: functions.rem(16);
                padding: functions.rem(12);
                background-color: var(--color-pop-in-background);

                @include mixins.displayFlex(row, 10, flex-start, flex-end, wrap);

                li {
                    border-radius: functions.rem(8);
                    padding: functions.rem(6) functions.rem(6);
                    background-color: var(--element-color);
                    box-shadow:
                        0 functions.rem(2) functions.rem(4) functions.rem(-2) var(--element-color) inset,
                        0 functions.rem(-2) functions.rem(6) functions.rem(1) var(--element-color) inset;

                    @include mixins.displayFlex(row, 0, flex-start, center, wrap);

                    img {
                        width: functions.rem(30);
                        height: functions.rem(30);
                    }

                    p {
                        font-size: functions.rem(18);
                        padding: 0 functions.rem(10);
                    }

                    button {
                        width: functions.rem(30);
                        height: functions.rem(30);
                        padding: functions.rem(6);
                        background: transparent;
                        border: 0;
                        outline: 0;
                        opacity: .4;
                        cursor: pointer;

                        @include mixins.transition;

                        &:hover {
                            opacity: 1;
                        }

                        span {
                            position: relative;
                            display: block;
                            transform: rotate(45deg);
                        }
                    }
                }
            }
        }
    }
</style>