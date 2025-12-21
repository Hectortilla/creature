<script lang="ts">
    import type { Association, Creature } from "$lib/types";
    import { onMount } from 'svelte';
    import { goto } from "$app/navigation";
    import { deleteAssociationAssociationsAssociationIdDelete } from '$lib/api';

    // Components
    import NarrativeText from '$lib/components/NarrativeText.svelte';
    import Divider from "$lib/components/Divider.svelte"
    import Card360 from '$lib/components/creature/Card360.svelte';
    import Button from "$lib/components/Button.svelte";

    interface PageProps {
        data: {
            params: {
                association?: string;
            };
            association?: Association | null;
            cards_use_association: Creature[]
        };
    }

    let { data }: PageProps = $props();
    console.log(data);

    let association = $derived.by(() => data.association ? data.association : null);

    // Container card position
    let cardContainer = $state<HTMLElement>();
    let cardContainerPosition = $state(0);

    const handleDeleteAssociation = async () => {
        if (!association) return;
        await deleteAssociationAssociationsAssociationIdDelete({ path: { association_id: association.id } });
        goto('/associations');
	};

    onMount (() => {
        cardContainerPosition = cardContainer?.getBoundingClientRect().top ?? 0;
    });

</script>
<div class="association-container">
    {#if association}
        <div class="association-info">
            <div class="info">
                <p class="name">{association.name}</p>
            </div>
            <Divider title={false} hasMargins={false}/>
            {#if association.description}
                <NarrativeText text={association.description}/>
            {/if}
            {#if data.cards_use_association.length > 0}
                <Divider title={`Cartas con esta asociación (${data.cards_use_association.length})`} hasMargins={false}/>
                <div class="cards-gallery">
                    {#each data.cards_use_association as card,i}
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
            <Button type="primary" text="Borrar asociación" onClick={handleDeleteAssociation} isDisabled={false} />
        </div>
    {/if}
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .association-container {
        @include mixins.displayFlex(column, 0, center, center, nowrap);
    }

    .association-info{
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
        }

        .cards-gallery {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            perspective: 1000px;
            gap: functions.rem(20);
        }
    }

</style>
