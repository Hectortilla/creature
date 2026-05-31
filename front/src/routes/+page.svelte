<script lang="ts">
    import { onMount } from "svelte";
    import { parallax } from '$lib/actions/parallax';

    // Images
    import logoFill from "$lib/assets/logo/logo-fill.svg?raw"
    import logoLine from "$lib/assets/logo/logo-line.svg?raw"

    let isLoaded = $state(false);

    onMount(() => {
        // Staggered animation effect
        setTimeout(() => {
            isLoaded = true;
        }, 100);
    });

</script>

<div class="home-container">
    <div class="header">
        <h1 class="title">Alen TCG</h1>
        <div class="pos-center">
            <div class="logo" class:is-loaded={isLoaded}>
                {@html logoFill}
            </div>
        </div>
        
        <div class="pos-center">
            <img
                use:parallax={{ intensity: 25, reverse: false }}
                class:is-loaded={isLoaded}
                src="/images/iso/iso-base.png"
                alt="iso"
                draggable="false"
            />
        </div>
        
        <div class="pos-center">
            <div class="logo" class:is-loaded={isLoaded}>
                {@html logoLine}
            </div>
        </div>
    </div>
</div>

<style lang="scss">
    @use "../lib/styles/abstracts/mixins" as mixins;
	@use "../lib/styles/abstracts/functions" as functions;

    .home-container {
        @include mixins.margins;

        .header {
            position: relative;
            width: 100%;
            height: 100vh; // prevent browser
            height: 100dvh;
            user-select: none;

            h1 {
                width: 1px;
                height: 1px;
                overflow: hidden;
                position: absolute;
                top: -1px;
                left: -1px;
            }

            .pos-center {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                padding-top: functions.rem(20);

                @include mixins.displayFlex(column, 0, center, center, nowrap);
            }

            .logo {
                width: 80%;
                max-width: functions.rem(1200);
                height: auto;
                opacity: 0;
                transform: translateY(functions.rem(120));

                @include mixins.transition(.9s, all, .4s);

                &.is-loaded {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            img {
                width: 60%;
                max-width: functions.rem(900);
                height: auto;
                opacity: 0;

                @include mixins.transition(1s, opacity);

                &.is-loaded {
                    opacity: 1;
                }
            }
        }
    }
</style>