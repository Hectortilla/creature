<script lang="ts">
    import type { Ability, Creature } from "$lib/types";
    import { onMount } from 'svelte';
    import { goto } from "$app/navigation";
    import { deleteAbilitiesItemIdDelete } from '$lib/api';

    // Components
    import NarrativeText from '$lib/components/NarrativeText.svelte';
    import Divider from "$lib/components/Divider.svelte"
    import Card360 from '$lib/components/creature/Card360.svelte';
    import Button from "$lib/components/Button.svelte";

    // Icons
    import physical from "$lib/icons/physical-type.svg?raw";
    import magical from "$lib/icons/magical-type.svg?raw";

    interface PageProps {
        data: {
            params: {
                ability?: string;
            };
            ability?: Ability | null;
            cards_use_ability: Creature[]
        };
    }

    // Tipado de props
    type IconName = string | "physical" | "magical";

    // Mapa de iconos
    const iconType: Record<IconName, string> = {
        physical,
        magical
    };

    let { data }: PageProps = $props();
    console.log(data);

    let ability = $derived.by(() => data.ability ? data.ability : null);

    // Container card position
    let cardContainer = $state<HTMLElement>();
    let cardContainerPosition = $state(0);

    const handleDeleteAbility = async () => {
        if (!ability) return;
        await deleteAbilitiesItemIdDelete({ path: { item_id: ability.id } });
        goto('/abilities');
	};

    onMount (() => {
        cardContainerPosition = cardContainer?.getBoundingClientRect().top ?? 0;
    });

</script>
<div class="ability-container">
    {#if ability}
        <div class="ability-info">
            <div class="info">
                <p class="name">{ability.name}</p>
                {#if ability.type}
                    <div class="item">
                        <div class="icon">{@html iconType[ability.type]}</div>
                    </div>
                {/if}
            </div>
            <Divider title={false} hasMargins={false}/>
            {#if ability.description}
                <NarrativeText text={ability.description}/>
            {/if}
            {#if data.cards_use_ability.length > 0}
                <Divider title={`Cartas con esta habilidad (${data.cards_use_ability.length})`} hasMargins={false}/>
                <div class="cards-gallery">
                    {#each data.cards_use_ability as card,i}
                        <Card360
                            data={card}
                            key={i}
                            showCode={true}
                            showInfo={true}
                            showEvolutionCode={true}
                            containerPos={cardContainerPosition}
                        />
                    {/each}
                </div>
            {/if}
            <Button type="primary" text="Borrar habilidad" onClick={handleDeleteAbility} isDisabled={false} />
        </div>
    {/if}
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .ability-container {
        @include mixins.displayFlex(column, 0, center, center, nowrap);
    }

    .ability-info{
        width: 100%;
        padding-top: functions.rem(60);
        max-width: functions.rem(800);

        @include mixins.displayFlex(column, 26, flex-start, flex-start, nowrap);
        @include mixins.margins;

        .info {
            width: 100%;
            @include mixins.displayFlex(row, 26, flex-start, center, wrap);

            p.name {
                flex: 1;
                font-size: functions.rem(32);
                font-family: variables.$font-title;
            }

            .item {
                @include mixins.displayFlex(row, 4, flex-start, center, wrap);

                .icon {
                    width: functions.rem(20);
                    height: functions.rem(20);
                }
            }

        }

        .cards-gallery {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            perspective: 1000px;
            gap: functions.rem(20);
        }
    }

</style>
