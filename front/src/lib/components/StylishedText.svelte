<script lang="ts">
  import { FONT_BASE_SIZE } from '$lib/constants';

  interface Props {
    text: string;
    fontSize?: number;
    htmlTag?: "p" | "h1" | "h2" | "h3" | "h4" | "h5" | "h6";
  }

  let {
    text = "Button",
    fontSize = 60,
    htmlTag = "p"
  }: Props = $props();
</script>

<div class="text-wrapper" style={`font-size:${fontSize / FONT_BASE_SIZE}rem;`}>
  {#if htmlTag === "p"}
    <p>{text}</p>
  {:else if htmlTag === "h1"}
    <h1>{text}</h1>
  {:else if htmlTag === "h2"}
    <h2>{text}</h2>
  {:else if htmlTag === "h3"}
    <h3>{text}</h3>
  {:else if htmlTag === "h4"}
    <h4>{text}</h4>
  {:else if htmlTag === "h5"}
    <h5>{text}</h5>
  {:else if htmlTag === "h6"}
    <h6>{text}</h6>
  {/if}
</div>

<style lang="scss">
  @use "../styles/abstracts/mixins" as mixins;
  @use "../styles/abstracts/functions" as functions;

  p, h1, h2, h3, h4, h5, h6 {
    $bevelSize: functions.rem(1);

    font-size: var(--font-size);

    @include mixins.fontProps("title", 400, 100, normal);
    @include mixins.stylishedText($bevelSize);
  }
</style>
