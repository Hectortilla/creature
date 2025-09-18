<script lang="ts">
    import type { Elements } from '$lib/types';
   interface PageProps {
        data: {
            elements?: Elements[];
        };
    }

    let { data }: PageProps = $props();
    console.log(data);

</script>

{#if data.elements && data.elements.length > 0}
    <h2>Elements</h2>
    <div class="gallery-elements">
    {#each data.elements as element}
        <a href={`/elements/${element.label}`} class="element" style="--color-element:#{element.color}">
            <img src={element.icon} alt={element.label} width="40" />
            <h2>{element.label}</h2>
        </a>
    {/each}
</div>
{:else}
    <p>No elements found in this section.</p>
{/if}

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;
    @use "$lib/styles/abstracts/functions" as functions;
    @use "$lib/styles/abstracts/variables" as variables;

    .gallery-elements {
        @include mixins.displayFlex(row, 6, flex-start, flex-start, wrap);
        @include mixins.margins;

        .element {
            padding: functions.rem(10);
            background-color: var(--color-nav-background);
            border-radius: functions.rem(10);
            overflow: hidden;

            @include mixins.displayFlex(row, 8, flex-start, center, wrap);

            h2 {
                font-size: functions.rem(16);
                font-weight: 400;
            }

            img {
                width: functions.rem(36);
                filter: drop-shadow(0 0 functions.rem(40) var(--color-element));
            }
        }
    }
</style>