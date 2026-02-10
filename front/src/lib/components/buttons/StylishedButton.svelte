<script lang="ts">

    interface Props {
        label: string;
        link?: string;
        onClick?: () => void;
    }

    let {
        label = "Menu",
        link,
        onClick,
    }: Props = $props();

</script>

<svelte:element
    this={link ? "a" : "button"}
    href={link}
    aria-label={label}
    role="button"
    tabindex="0"
    onclick={onClick}
>
    <picture>
        <source 
            type="image/webp"
            srcset="
                /images/button/button-bg.webp 1x,
                /images/button/button-bg@2x.webp 2x,
                /images/button/button-bg@3x.webp 3x
            "
        >
            
        <img 
            src="/images/button/button-bg.png"
            srcset="
                /images/button/button-bg.png 1x,
                /images/button/button-bg@2x.png 2x,
                /images/button/button-bg@3x.png 3x
            "
            alt=""
            width="auto"
            height="52"
            loading="lazy"
            decoding="async"
        >
    </picture>
    <p>{label}</p>
</svelte:element>

<style lang="scss">
    @use "../../styles/abstracts/variables" as variables;
	@use "../../styles/abstracts/mixins" as mixins;
	@use "../../styles/abstracts/functions" as functions;

    button, a {
        $color: #{var(--color-button-stylished-background)};

        position: relative;
        background-color: transparent;
        border: none;
        padding: 0;
        height: functions.rem(52);
        cursor: pointer;
        
        @include mixins.fontProps("title", 400, 100, normal);
        @include mixins.transition();
        @include mixins.displayFlex(row, 0, center, center, nowrap);

        img {
            display: block;
            height: 100%;
            width: auto;

            @include mixins.transition();
        }

        p {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            font-size: functions.rem(24);
            padding-top: functions.rem(4);
            color: var(--color-button-stylished-color);
            text-shadow: 0 0 functions.rem(10) rgba(0,0,0,0.5);

            @include mixins.displayFlex(row, 0, center, center, nowrap);
            @include mixins.fontProps("title", 400, 100, normal);
        }

        &:hover {
            img {
                filter: brightness(1.2);
            }
        }
    }

    

</style>