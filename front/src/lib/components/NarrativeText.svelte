<script lang="ts">
    interface PageProps {
        text: string;
    }

    let {
        text,
    }: PageProps = $props();

    // Icons Types
    import primordial from '$lib/assets/icons/primordial.svg?raw';
    import warrior from '$lib/assets/icons/warrior.svg?raw';
    import wizard from '$lib/assets/icons/wizard.svg?raw';
    import creature from '$lib/assets/icons/creature.svg?raw';
    import weapon from '$lib/assets/icons/weapon.svg?raw';
    import object from '$lib/assets/icons/object.svg?raw';
    import field from '$lib/assets/icons/field.svg?raw';

    // Icons Characters
    import ancestral from '$lib/assets/icons/ancestral.svg?raw';
    import elemental from '$lib/assets/icons/elemental.svg?raw';
    import leyend from '$lib/assets/icons/leyend.svg?raw';
    import hero from '$lib/assets/icons/hero.svg?raw';
    import magic from '$lib/assets/icons/magic.svg?raw';
    import undead from '$lib/assets/icons/undead.svg?raw';
    import common from '$lib/assets/icons/common.svg?raw';

    // Icons Types
    import physical from "$lib/assets/icons/physical-type.svg?raw";
    import magical from "$lib/assets/icons/magical-type.svg?raw";

    // Icons others
    import dice from "$lib/assets/icons/dice-rolls.svg?raw";
    import health from "$lib/assets/icons/health.svg?raw";

    type IconName =
        | "primordial"
        | "warrior"
        | "wizard"
        | "creature"
        | "weapon"
        | "object"
        | "field"
        | "ancestral"
        | "elemental"
        | "leyend"
        | "hero"
        | "magic"
        | "undead"
        | "common"
        | "magical"
        | "physical"
        | "dice"
        | "health";

    type TextPart =
        | { type: "text"; value: string }
        | { type: "number"; value: string; sign: "positive" | "negative" | "neutral" }
        | { type: "element"; name: string }
        | { type: "icon";  name: IconName }
        | { type: "italic"; value: string }
        | { type: "fontNumber"; value: string }


    // Mapa de iconos
    const icons: Record<string, string> = {
        primordial,
        warrior,
        wizard,
        creature,
        weapon,
        object,
        field,
        ancestral,
        elemental,
        leyend,
        hero,
        magic,
        undead,
        common,
        magical,
        physical,
        dice,
        health
    };

    const ICON_NAMES = new Set([
        "primordial","warrior","wizard","creature","weapon","object",
        "field","ancestral","elemental","leyend","hero","magic","undead",
        "common","magical","physical", "dice", "health"
    ]);

    function parseText(text: string): TextPart[] {
        const parts: TextPart[] = [];
        const regex = /([+-]?\d+)|<i>(.*?)<\/i>|<n>(.*?)<\/n>|<([a-z]+)>/gi;
        let lastIndex = 0;

        let match: RegExpExecArray | null;
        while ((match = regex.exec(text)) !== null) {
            const [fullMatch, number, italic, fontNumber, element] = match;
            const offset = match.index;

            // Texto antes del match
            if (offset > lastIndex) {
                parts.push({ type: "text", value: text.slice(lastIndex, offset) });
            }

            if (number) {
                let sign: "positive" | "negative" | "neutral" = "positive";
                if (number.startsWith("+")) sign = "positive";
                else if (number.startsWith("-")) sign = "negative";
                else if (number === "0") sign = "neutral";

                parts.push({
                    type: "number",
                    value: number,
                    sign,
                });
            } else if (italic) {
                parts.push({ type: "italic", value: italic });
            } else if (fontNumber) {
                parts.push({ type: "fontNumber", value: fontNumber });
            } else if (element) {
                if (ICON_NAMES.has(element)) {
                    parts.push({ type: "icon", name: element as IconName });
                } else {
                    parts.push({ type: "element", name: element });
                }
            }

            lastIndex = offset + fullMatch.length;
        }

        // Texto restante
        if (lastIndex < text.length) {
            parts.push({ type: "text", value: text.slice(lastIndex) });
        }

        return parts;
    }



    let parsed = $derived.by(() => parseText(text));
</script>

<p class="effect">
  {#each parsed as part}
    {#if part.type === "text"}
      {part.value}
    {:else if part.type === "number"}
        <span class={part.sign}>{part.value}</span>
    {:else if part.type === "element"}
      <img
        class="icon-formatted"
        src={`/images/elements/${part.name}.png`}
        alt={part.name}
      />
    {:else if part.type === "italic"}
        <span class="italic">{part.value}</span>
    {:else if part.type === "fontNumber"}
        <span class="number">{part.value}</span>
    {:else if part.type === "icon"}
        <span class="icon-formatted">
            {@html icons[part.name] ?? `<svg><text>?</text></svg>`}
        </span>
    {/if}
  {/each}
</p>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    p.effect {
        color: var(--color-effect-text);
    }

    span.negative {
        color: functions.color(semantic, error, 80%, 60%);
    }
    span.positive {
        color: functions.color(semantic, success, 80%, 60%);
    }
    span.neutral {
        color: var(--color-button-primary-background);
    }
    span.italic {
        font-family: variables.$font-title;
        font-size: functions.rem(19);
    }
    span.number {
        font-family: variables.$font-number;
        font-size: functions.rem(19);
    }
    .icon-formatted {
        display: inline-block;
        width: functions.rem(20);
        height: functions.rem(20);
        margin: 0 functions.rem(2) functions.rem(-4) functions.rem(2);
    }
</style>
