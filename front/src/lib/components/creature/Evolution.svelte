<script lang="ts">
    // Icons
    import evolutionIcon from "$lib/assets/icons/evolution.svg?raw"

    interface PageProps {
        evolutionCode: number | null,
    }

    let {
        evolutionCode = null,
    }: PageProps = $props();
</script>

<div class="evolution-wrapper">
    <p>{evolutionCode}</p>
    <div class="icon">
        {@html evolutionIcon}
    </div>
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .evolution-wrapper {
        height: 68%;
        margin-top: 2%;
        aspect-ratio: 1/1;
        padding: 0 functions.rem(6) 0 functions.rem(10);
        border-radius: functions.rem(4);
        background: linear-gradient(
            110deg,
            var(--color-creature-evolution-background-gradient-0) 0%,
            var(--color-creature-evolution-background-gradient-50) 50%,
            var(--color-creature-evolution-background-gradient-100) 100%,

        );
        box-shadow:
            functions.rem(-2) functions.rem(2) functions.rem(2) functions.rem(-2) var(--color-creature-code-light-top) inset,
            functions.rem(2) functions.rem(-2) functions.rem(4) functions.rem(-1) var(--color-creature-code-light-bottom) inset,
            0 0 functions.rem(10) functions.rem(-4) var(--color-creature-evolution-background-gradient-100);

        @include mixins.displayFlex(row, 3, center, center, nowrap);

        .icon {
            height: 56%;
            aspect-ratio: 1/1;
            width: auto;
            color: var(--color-creature-evolution-icon);
            opacity: 1;
        }

        p {
            font-family: variables.$font-number;
            font-size: functions.rem(18);
            color: var(--color-creature-evolution-icon);
            text-shadow: functions.rem(-1) functions.rem(2) functions.rem(3) 0 var(--color-creature-evolution-text-shadow);
        }
    }
</style>