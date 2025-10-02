<script lang="ts">
    import type { Element } from '$lib/types';
    import { ELEMENTAL_ATTACK_MODIFIER } from '$lib/constants';

    interface PageProps {
        elements?: Element[];
        showTitle?: boolean;
        showTable?: boolean;
        showSpecifications?: boolean;
    }

    let { elements, showTitle = true, showTable = true, showSpecifications = true, }: PageProps = $props();

    function findElement(id: number) {
        if (!id) return null;
        return elements?.find(e => e.id === id) ?? null;
    }

    let hoveredRow = $state<null | number>(null);
    let hoveredCol = $state<null | number>(null);

    function handleMouseEnter(row: number, col: number) {
        hoveredRow = row;
        hoveredCol = col;
    }

    function handleMouseLeave() {
        hoveredRow = null;
        hoveredCol = null;
    }

    function isActive(row: number, col: number) {
        return hoveredRow === row && hoveredCol === col;
    }

    /**
     * isHighlighted:
     * - Si hover es un header de columna (hoveredRow === 0) -> ilumina toda la columna (col === hoveredCol)
     * - Si hover es un header de fila   (hoveredCol === 0) -> ilumina toda la fila    (row === hoveredRow)
     * - Si hover es una celda normal    -> ilumina SOLO esa celda + sus headers (row=0,col=hoveredCol y col=0,row=hoveredRow)
     */
    function isHighlighted(row: number, col: number) {
        if (hoveredRow === null || hoveredCol === null) return false;

        // Hover en header de columna (fila 0): iluminar toda la columna
        if (hoveredRow === 0) {
            return col === hoveredCol || col === 0;
        }

        // Hover en header de fila (columna 0): iluminar toda la fila
        if (hoveredCol === 0) {
            return row === hoveredRow || row === 0;
        }

        // Hover en celda normal -> iluminar solo esa celda y los headers relacionados
        return (
            (row === hoveredRow && col === hoveredCol) || // la celda activa
            (row === 0 && col === hoveredCol) ||          // header de la columna
            (col === 0 && row === hoveredRow)             // header de la fila
        );
    }

    function isDimmed(row: number, col: number) {
        if (hoveredRow === null || hoveredCol === null) return false;
        return !isActive(row, col) && !isHighlighted(row, col);
    }
</script>

<div class="elements-container">
    {#if showTitle}
        <p class="title">Tabla de elementos</p>
    {/if}
    <div class="tables-container">
        {#if elements && elements.length > 0}
            {#if showTable}
                <div class="table-elements" data-columns={elements.length + 1} style={`--columns:${elements.length + 1}`}>
                    <div class="cell"><p><span class="empty">VS</span></p></div>
                    {#each elements as element,col}
                        <div
                            class="cell element"
                            style="--color-element:#{element.color}44"
                            aria-label="Focus"
                            role="cell"
                            tabindex="0"
                            onmouseenter={() => handleMouseEnter(0, col + 1)}
                            onmouseleave={handleMouseLeave}
                            class:active={isActive(0, col + 1)}
                            class:highlighted={isHighlighted(0, col + 1)}
                            class:dimmed={isDimmed(0, col + 1)}
                        >
                            <img src={element.icon} alt={element.label} />
                        </div>
                    {/each}
                    {#each elements as element,row}
                        <div
                            class="cell element"
                            style="--color-element:#{element.color}44"
                            aria-label="Focus"
                            role="cell"
                            tabindex="0"
                            onmouseenter={() => handleMouseEnter(row + 1, 0)}
                            onmouseleave={handleMouseLeave}
                            class:active={isActive(row + 1, 0)}
                            class:highlighted={isHighlighted(row + 1, 0)}
                            class:dimmed={isDimmed(row + 1, 0)}
                        >
                            <img src={element.icon} alt={element.label} />
                        </div>
                        {#each elements as e, col}
                            <div
                                class="cell"
                                aria-label="Focus"
                                role="cell"
                                tabindex="0"
                                onmouseenter={() => handleMouseEnter(row + 1, col + 1)}
                                onmouseleave={handleMouseLeave}
                                class:active={isActive(row + 1, col + 1)}
                                class:highlighted={isHighlighted(row + 1, col + 1)}
                                class:dimmed={isDimmed(row + 1, col + 1)}
                            >
                                {#if element.weaknesses?.includes(col + 1) && !element.strengths?.includes(col + 1)}
                                    <p><span class="weaknesses">-{ELEMENTAL_ATTACK_MODIFIER}</span></p>
                                {:else if !element.weaknesses?.includes(col + 1) && element.strengths?.includes(col + 1)}
                                    <p><span class="strengths">+{ELEMENTAL_ATTACK_MODIFIER}</span></p>
                                {:else if element.weaknesses?.includes(col + 1) && element.strengths?.includes(col + 1)}
                                    <p><span class="strengths">+{ELEMENTAL_ATTACK_MODIFIER}</span></p>
                                {:else}
                                    <p><span class="empty">-</span></p>
                                {/if}
                            </div>
                        {/each}
                    {/each}
                </div>
            {/if}
            {#if showSpecifications}
                <div class="elements-specifications">
                    {#each elements as element}
                        <div class="row">
                            <img src={element.icon} alt={element.label} style="--color-element:#{element.color}44" />
                            <div class="item">
                                <p>Debil frente a:</p>
                                {#each element.weaknesses as weakness}
                                    <img
                                        src={findElement(weakness)?.icon}
                                        alt={findElement(weakness)?.label}
                                    />
                                {/each}
                            </div>
                            <div class="item">
                                <p>Fuerte frente a:</p>
                                {#each element.strengths as strength}
                                    <img
                                        src={findElement(strength)?.icon}
                                        alt={findElement(strength)?.label}
                                    />
                                {/each}
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        {:else}
            <p>No elements found.</p>
        {/if}
    </div>
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;
    @use "$lib/styles/abstracts/functions" as functions;
    @use "$lib/styles/abstracts/variables" as variables;

    .elements-container {
        width: 100%;
        @include mixins.displayFlex(column, 24, flex-start, center, nowrap);

        .tables-container {
            width: 100%;
            @include mixins.displayFlex(row, 10, center, flex-start, nowrap);

            @media (max-width:1200px) {
               @include mixins.displayFlex(column, 10, center, center, nowrap); 
            }
        }

        .title {
            font-family: variables.$font-title;
            font-size: functions.rem(32);
        }

        .table-elements {
            position: sticky;
            top: functions.rem(20);
            left: 0;
            width: auto;
            max-width: functions.rem(900);
            background-color: var(--color-pop-in-background);
            border-radius: functions.rem(10);
            overflow: hidden;
            padding: functions.rem(12);

            display: grid;
            grid-template-columns: repeat(var(--columns), 1fr);

            @media (max-width:1200px) {
                position: relative;
                top: inherit;
                left: inherit;
            }

            .cell {
                border-bottom: solid 1px var(--color-pop-in-background);
                border-left: solid 1px var(--color-pop-in-background);

                @include mixins.displayFlex(column, 0, center, center, wrap);
                @include mixins.transition;

                p, img {
                    cursor: default;
                    @include mixins.transition;
                }

                &.dimmed img, &.dimmed p {
                    opacity: 0.2;
                } 

                &.highlighted img, &.highlighted p {
                    opacity: 1;
                }

                &.active p {
                    transform: scale(1.1);
                    z-index: 1;
                }

                span.weaknesses {
                    color: functions.color(semantic, error, 80%, 60%);
                }

                span.strengths {
                    color: functions.color(semantic, success, 80%, 60%);
                }

                span.empty {
                    font-family: variables.$font-title;
                    opacity: .4;
                }

            }

            // Last /14 columns/ cells
            &[data-columns="14"] > .cell:nth-last-child(-n + 14) {
                border-bottom: 0;
            }
            // First cell eache /14 columns/ cells
            &[data-columns="14"] > .cell:nth-child(14n + 1) {
                border-left: 0;
            }

            .element {
                padding: functions.rem(10);

                img {
                    width: 100%;
                    filter: drop-shadow(0 0 functions.rem(20) var(--color-element));
                }
            }
        }

        .elements-specifications {
            position: sticky;
            top: functions.rem(20);
            left: 0;
            flex: none;
            background-color: var(--color-pop-in-background);
            border-radius: functions.rem(10);
            overflow: hidden;
            //padding: functions.rem(6);

            @include mixins.displayFlex(column, 0, flex-start, flex-start, nowrap);

            @media (max-width:1200px) {
                position: relative;
                top: inherit;
                left: inherit;
                width: 100%;
                max-width: functions.rem(900);
            }

            .row {
                width: 100%;
                padding: functions.rem(18);
                border-bottom: solid 1px var(--color-pop-in-background);

                @include mixins.displayFlex(row, 40, flex-start, center, nowrap);

                &:last-child {
                    border-bottom: 0;
                }

                img {
                    width: functions.rem(28);
                    filter: drop-shadow(0 0 functions.rem(20) var(--color-element));
                }

                .item {
                    flex: 1;

                    @include mixins.displayFlex(row, 12, flex-start, center, nowrap);

                    p {
                        white-space: nowrap;
                    }
                }

            }
        }
    }
</style>