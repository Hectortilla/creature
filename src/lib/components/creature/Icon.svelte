<script lang="ts">
    // Icons Types
    import primordial from '$lib/icons/primordial.svg?raw';
    import warrior from '$lib/icons/warrior.svg?raw';
    import wizard from '$lib/icons/wizard.svg?raw';
    import creature from '$lib/icons/creature.svg?raw';
    import weapon from '$lib/icons/weapon.svg?raw';
    import object from '$lib/icons/object.svg?raw';
    import field from '$lib/icons/field.svg?raw';

    // Icons Characters
    import ancestral from '$lib/icons/ancestral.svg?raw';
    import elemental from '$lib/icons/elemental.svg?raw';
    import leyend from '$lib/icons/leyend.svg?raw';
    import hero from '$lib/icons/hero.svg?raw';
    import magic from '$lib/icons/magic.svg?raw';
    import undead from '$lib/icons/undead.svg?raw';
    import common from '$lib/icons/common.svg?raw';

    // Icons Types
    import physical from "$lib/icons/physical-type.svg?raw";
    import magical from "$lib/icons/magical-type.svg?raw";

    // Tipado de props
    type IconName =
        string
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
        | "physical";

    interface PageProps {
        name: IconName;
        size: number;
        isBackground: boolean;
    }

    let {
        name = "primordial",
        size = 22,
        isBackground = false
    }: PageProps = $props();

    // Mapa de iconos
    const icons: Record<IconName, string> = {
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
        physical
    };

</script>
<div
    class="icon-wrap"
    class:has_background={isBackground}
    class:size={size > 0}
    style={`--size: ${size / 16}rem`}
>
    <div class="icon">
        {@html icons[name]}
    </div>
</div>

<style lang="scss">
    @use "sass:math";
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/functions" as functions;
    @use "$lib/styles/abstracts/mixins" as mixins;

    .icon-wrap {
        width: var(--size);
        height: var(--size);
        display: inline-block;

        @include mixins.displayFlex(column, 0, center, center, nowrap);

        &:not(.size) {
            height: 100%;
            width: fit-content;
            aspect-ratio: 1/1;
        }

        &.size {
            width: var(--size);
            height: var(--size);
        }

        &.has_background {
            padding: functions.rem(2);
            background: linear-gradient(
                110deg,
                var(--color-creature-classification-background-gradient-0) 0%,
                var(--color-creature-classification-background-gradient-50) 40%,
                var(--color-creature-classification-background-gradient-100) 100%,
            );
            border-radius: functions.rem(4);

            box-shadow:
				functions.rem(-1) functions.rem(2) functions.rem(2) functions.rem(-2) var(--color-creature-classification-light-top) inset,
				0 functions.rem(-2) functions.rem(4) functions.rem(1) var(--color-creature-classification-light-bottom) inset;

            .icon {
                width: 100%;
                height: 100%;
                color: var(--color-creature-foreground);
            }
        }
    }

</style>