<script lang="ts">
    interface Props {
        title: string | boolean,
        hasMargins: boolean,
    }
    let { title, hasMargins = false }: Props = $props();
</script>

<div class="divider-wrapper" class:margin={hasMargins}>
    <div class="bar"></div>
    {#if title}
        <p>{title}</p>
        <div class="bar"></div>
    {/if}
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .divider-wrapper {
        width: 100%;
        height: auto;

        @include mixins.displayFlex(row, 10, flex-start, center, nowrap);

        &.margin {
            margin: functions.rem(10);
        }

        .bar {
            flex: 1;
            height: 1px;
            background-color: var(--color-divider-bar);
        }

        p {
            font-family: variables.$font-title;
            font-size: functions.rem(16);
            color: var(--color-divider-text);
        }
    }
</style>