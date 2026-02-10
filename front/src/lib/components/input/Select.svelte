<script lang="ts">
    import type { Element, Type, Character } from "$lib/types";
    import { formatHandle } from "$lib/utils/formatHandle"
    import { slide } from "svelte/transition"
    import { onMount } from "svelte";

    // Components
    import Icon from "$lib/components/creature/Icon.svelte";

    // Icons
    import arrowIcon from "$lib/assets/icons/arrow.svg?raw";

    interface Props {
        label: string;
        noSelectText?: string;
        group: number | null,
        list: Element[] | Type[] | Character[];
        iconType: string;
        isMandatory: boolean;
        isDisabled: boolean;
        showLabel?: boolean;
    }

    let {
        label,
        noSelectText = "No seleccionado",
        group = $bindable(1),
        list,
        iconType,
        isMandatory = false,
        isDisabled = false,
        showLabel = true
    }: Props = $props();

    let isOpenDropdown = $state(false);
    let dropdownEl: HTMLElement | null = null;

    let selectedItem = $derived.by(() => {
        if(!group) return showLabel ? noSelectText : label;

        const getAllData = list.find(item => item.id === group);
        return {
            id: getAllData?.id,
            label: getAllData?.label,
            icon: getAllData?.icon
        }
    });

    /**
     * Open dropdown
     */
    function toggleDropdown() {
        isOpenDropdown = !isOpenDropdown;
    }

    function handleClickOutside(event: MouseEvent) {
        if (isOpenDropdown && dropdownEl && !dropdownEl.contains(event.target as Node)) {
            isOpenDropdown = false;
        }
    }

    onMount(() => {
        if (typeof document !== "undefined") {
            document.addEventListener("click", handleClickOutside);
        }

        return () => {
            if (typeof document !== "undefined") {
                document.removeEventListener("click", handleClickOutside);
            }
        };
    });

</script>

<div class="input-container" class:disabled={isDisabled} bind:this={dropdownEl}>
    {#if showLabel}
        <div class="label-wrapper">
            <label for={formatHandle(label)}>
                {label}
                {#if isMandatory}
                    <span>*</span>
                {/if}
            </label>
        </div>
    {/if}
    <div class="select-wrapper">
        <button
            type="button"
            aria-label={`Cambiar ${label.toLowerCase}`}
            onclick={() => {toggleDropdown()}}
            class:filter={!showLabel}
            >
            <span class="info">
                {#if typeof selectedItem === 'object' && selectedItem.label}
                    {#if iconType === 'image' && selectedItem.icon !== ''}
                        <img src={selectedItem.icon} alt={selectedItem.label} />
                    {:else}
                        <Icon
                            name={selectedItem.icon ? selectedItem.icon : "primordial"}
                            size={26}
                            isBackground={selectedItem.icon !== 'physical' && selectedItem.icon !== 'magical'}
                        />
                    {/if}
                    <p>{selectedItem.label}</p>
                {:else}
                    <span class="no-selected">{selectedItem}</span>
                {/if}
            </span>
            <span class="icon" class:open={isOpenDropdown}>
                {@html arrowIcon}
            </span>
        </button>
        {#if isOpenDropdown}
            <ul transition:slide class="dropdown-wrapper">
                <li>
                    <input
                        type="radio"
                        name={formatHandle(label)}
                        id={showLabel ? formatHandle(noSelectText) : label}
                        value={null}
                        bind:group={group}
                        onchange={() => {toggleDropdown()}}
                    >
                    <label
                        for={showLabel ? formatHandle(noSelectText) : label}
                        class:active={showLabel ? selectedItem === noSelectText : selectedItem === label}
                    >
                        <p>{noSelectText}</p>
                    </label>
                </li>
                {#each list as item}
                <li>
                    <input
                        type="radio"
                        name={formatHandle(label)}
                        id={`${formatHandle(item.label)}-${formatHandle(label)}`}
                        value={item.id}
                        bind:group={group}
                        onchange={() => {toggleDropdown()}}
                    >
                    <label
                        for={`${formatHandle(item.label)}-${formatHandle(label)}`}
                        class:active={typeof selectedItem === 'object' ? selectedItem.id === item.id : false}
                    >
                        {#if iconType === 'image'}
                            <img src={item.icon} alt={item.label} />
                        {:else if item.icon}
                            <Icon
                                name={item.icon}
                                size={26}
                                isBackground={item.icon !== 'physical' && item.icon !== 'magical'}
                            />
                        {/if}
                        <p>{item.label}</p>
                    </label>
                </li>
                {/each}
            </ul>
        {/if}
    </div>
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .input-container {
        width: functions.rem(180);

        .select-wrapper {
            position: relative;
            width: 100%;

            button {
                width: 100%;
                height: functions.rem(variables.$input-height);
                border-radius: functions.rem(variables.$input-radius);
                padding: 0 functions.rem(variables.$input-padding);
                border: solid 1px var(--color-input-border);
                cursor: pointer;

                @include mixins.displayFlex(row, 8, space-between, center, nowrap);

                &.filter {
                    background: var(--color-input-search-background);
                    backdrop-filter: blur(functions.rem(10));
                    border: none;
                }

                .info {
                    @include mixins.displayFlex(row, 8, flex-start, center, nowrap);
                }

                img {
                    width: functions.rem(26);
                    height: functions.rem(26);
                }

                p {
                    color: var(--color-input-text);
                }

                .icon {
                    width: functions.rem(18);
                    height: functions.rem(18);
                    will-change: transform;

                    @include mixins.transition;

                    &.open {
                        transform: rotate(180deg);
                    }
                }

                span.no-selected {
                    color: var(--color-input-placeholder);
                }
            }

            .dropdown-wrapper {
                position: absolute;
                width: 100%;
                top: functions.rem(variables.$input-height);
                background-color: var(--color-input-search-background);
                border-radius: functions.rem(variables.$input-radius);
                backdrop-filter: blur(functions.rem(12));
                max-height: functions.rem(200);
                overflow-y: auto;
                overflow-x: auto;
                z-index: 1;

                &::-webkit-scrollbar {
                    display: none;
                }

                li {
                    input {display: none;}
                    label {
                        width: 100%;
                        padding: functions.rem(variables.$input-padding);
                        border-radius: functions.rem(variables.$input-radius);
                        cursor: pointer;

                        @include mixins.displayFlex(row, 8, flex-start, center, nowrap);
                        @include mixins.transition;

                        img {
                            width: functions.rem(26);
                            height: functions.rem(26);
                        }

                        p {
                            color: var(--color-input-text);
                        }

                        &:hover {
                            background-color: functions.color(base, 200, 10%, 30%);
                        }

                        &.active {
                            pointer-events: none;
                            opacity: .4;
                        }
                    }
                }
            }
        }
    }
</style>