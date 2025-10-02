<script lang="ts">
    import type { PageProps } from "./$types";

    // Components
    import CreatureCard360 from "$lib/components/creature/Card360.svelte"

    let { data }: PageProps = $props();
    console.log(data);

    /// Creature card
    let cardContainer = $state<HTMLElement>();
    let cardContainerPosition = $state(0);

</script>

<div class="home-container">
    <div class="last-info">
        <div class="info">
            <p>Cartas creadas: {data.cards.length}</p>
            <p>Ataques creados: {data.attacks.length}</p>
            <p>Habilidades creadas: {data.abilities.length}</p>
            <p>Asociaciones creadas: {data.associations.length}</p>
        </div>
    </div>
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .home-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);

        @include mixins.margins;

        .last-info {
            width: 100%;
            height: auto;
            padding: functions.rem(20);
            border-radius: functions.rem(32);
            //background-color: var(--color-button-secondary-background);
            grid-column: 1/3;
            box-shadow:
                0 functions.rem(2) functions.rem(4) functions.rem(-2) var(--color-input-button-light-top) inset,
                0 functions.rem(-2) functions.rem(6) functions.rem(1) var(--color-input-button-light-bottom) inset;

            @include mixins.displayFlex(row, 20, flex-start, flex-start, wrap);
        }
    }
</style>