<script lang="ts">
    import { blur } from "svelte/transition"

    // Components
    import Button from "$lib/components/Button.svelte";

    // Icons
    import diceIcon from "$lib/assets/icons/dice-rolls.svg?raw";

    let isOpenRollDiceScreen = $state<boolean>(false);
    let diceNumber = $state<number | null>(null);
    let rolling = $state<boolean>(false);

    function handleRollDiceScreen() {
        isOpenRollDiceScreen = !isOpenRollDiceScreen;

        if (isOpenRollDiceScreen) {
            rollDice();
        }
    }

    function rollDice() {
        if (rolling) return;

        rolling = true;
        const finalNumber = rollWeightedDice();
        let currentNumber = diceNumber ?? 0;
        let cycles = 0; // contar cuántas vueltas completas hemos dado
        const maxCycles = 5; // número de ciclos antes de parar

        const interval = setInterval(() => {
            // avanzar al siguiente número cíclicamente
            currentNumber = (currentNumber % 3) + 1;
            diceNumber = currentNumber;

            // si hemos llegado al número final después de suficientes ciclos
            if (cycles >= maxCycles && currentNumber === finalNumber) {
                clearInterval(interval);
                rolling = false;
            }

            // aumentar ciclo cuando pasamos del 3 al 1
            if (currentNumber === 3) cycles++;
        }, 150); // velocidad de cambio de número
    }

    function rollWeightedDice(): number {
        const random = Math.random(); // número entre 0 y 1

        if (random < 3 / 6) {
            return 1; // 0 - 0.5
        } else if (random < 5 / 6) {
            return 2; // 0.5 - 0.8333
        } else {
            return 3; // 0.8333 - 1
        }
    }
</script>

<button
    class="roll-dice"
    aria-label="Tirar dado"
    onclick={handleRollDiceScreen}
>
    {@html diceIcon}
</button>

{#if isOpenRollDiceScreen}
    <div transition:blur class="modal-dice">
        <div class="dice-number" class:rolling transition:blur>{diceNumber}</div>
        <p class="info"><span>1 = 3/6</span><span>2 = 2/6</span><span>3 = 1/6</span></p>
        <div class="btn-wrapper">
            <Button type="primary" text="Tirar el dado" isDisabled={rolling} onClick={rollDice} />
            <Button type="secondary" text="Salir" isDisabled={rolling} onClick={handleRollDiceScreen} />
        </div>
    </div>
{/if}


<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
	@use "$lib/styles/abstracts/functions" as functions;
	@use "$lib/styles/abstracts/mixins" as mixins;

    .roll-dice {
        position: fixed;
        right: functions.rem(20);
        bottom: functions.rem(20);
        width: functions.rem(42);
        height: functions.rem(42);
        border-radius: functions.rem(20);
        padding: functions.rem(8);
        background-color: functions.color(base, 100, 50%, 20%, .8);
        backdrop-filter: blur(functions.rem(10));
        box-shadow:
                0 functions.rem(2) functions.rem(4) functions.rem(-2) var(--color-input-button-light-top) inset,
                0 functions.rem(-2) functions.rem(6) functions.rem(1)var(--color-input-button-light-bottom) inset;
        cursor: pointer;
        will-change: background-color, box-shadow;

        @include mixins.transition;

        &:hover {
            background-color: functions.color(base, 100, 50%, 20%, .8);
            box-shadow:
                0 functions.rem(-2) functions.rem(4) functions.rem(-2) var(--color-input-button-light-top) inset,
                0 functions.rem(2) functions.rem(6) functions.rem(1)var(--color-input-button-light-bottom) inset;
        }
    }

    .modal-dice {
        position: fixed;
        top: 0;
        left: 0;
        width: 100dvw;
        height: 100dvh;
        background-color: var(--color-pop-in-background);
        backdrop-filter: blur(functions.rem(10));
        z-index: 11;

        @include mixins.displayFlex(column, 40, center, center, nowrap);

        .dice-number {
            width: functions.rem(160);
            height: functions.rem(160);
            font-size: functions.rem(120);
            font-family: variables.$font-number;
            background-color: var(--color-button-secondary-background);
            border-radius: functions.rem(40);
            cursor: default;
            pointer-events: none;
            background: linear-gradient(
                110deg,
                var(--color-creature-code-background-gradient-0) 0%,
                var(--color-creature-code-background-gradient-50) 50%,
                var(--color-creature-code-background-gradient-100) 100%,

            );
            box-shadow:
                functions.rem(1) functions.rem(2) functions.rem(12) functions.rem(-2) var(--color-creature-code-light-top) inset,
                functions.rem(-1) functions.rem(-2) functions.rem(12) functions.rem(-1) var(--color-creature-code-light-bottom) inset;

            text-align: center;
            color: var(--color-creature-foreground);
            z-index: 2;
            text-shadow: functions.rem(-1) functions.rem(2) functions.rem(3) var(--color-creature-code-text-shadow);
            
            @include mixins.transition;
            @include mixins.displayFlex(column, 0, center, center, nowrap);

            &.rolling {
                transform: scale(1.2);
            }
        }

        p.info {
            font-size: functions.rem(14);
            opacity: .6;

            @include mixins.displayFlex(row, 8, center, center, nowrap);

            span {
                padding: functions.rem(2) functions.rem(6);
                background-color: var(--color-button-secondary-background);
                border-radius: functions.rem(6);
            }
        }

        .btn-wrapper {
            @include mixins.displayFlex(column, 12, center, center, nowrap);
        }
    }
</style>