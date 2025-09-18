<script lang="ts">
    import type { Creature } from '$lib/types';

    // Components
    import Code from "$lib/components/creature/Code.svelte";
    import Icon from '$lib/components/creature/Icon.svelte';

    interface PageProps {
        data: Creature;
        key: number;
        showInfo: boolean;
        showCode: boolean;
    }

    let {
        data,
        key,
        showInfo = true,
        showCode = true
    }: PageProps = $props();

    // Parse element data
    const firstElement = JSON.parse(data.first_element);
    const secondElement = JSON.parse(data.second_element);
    const type = JSON.parse(data.type);
    const character = JSON.parse(data.character);
</script>

<div class="card-container">
    <a href="/cards/{data.code}" class="card-wrapper">
        {#if showCode}
            <div class="info">
                <Code code={data.code} />
            </div>
        {/if}
        {#if showInfo}
            <div class="hover-info">
                <div class="classification">
                    <Icon name={type.icon} size={23} isBackground={true} />
                    <Icon name={character.icon} size={23} isBackground={true} />
                </div>
                <div class="elements">
                    <div class="element">
                        <img src={firstElement.icon} alt={firstElement.label} />
                    </div>
                    {#if secondElement && secondElement !== "null"}
                        <div class="element">
                            <img src={secondElement.icon} alt={secondElement.label} />
                        </div>
                    {/if}
                </div>
            </div>
        {/if}
        {#if data.image && data.image !== null}
            <img src={data.image} alt={data.name} width="300" />
        {:else}
            <img src="/images/cards/placeholder.jpg" alt={data.name} width="300" />
        {/if}
        <div class="effects">
            <div class="finger-prints" style={`background: url('/images/finger-prints/${(key % 4) + 1}.jpg');`}></div>
        </div>
    
    </a>
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .card-container {
        position: relative;
        width: 100%;
        height: auto;
        mask-image: url("/images/card-mask.svg");
        mask-position: center;
        mask-size: 100% 100%;
        mask-repeat: no-repeat;
        transform-style: preserve-3d;

        @include mixins.displayFlex(column, 0, flex-start, flex-start, nowrap);
        @include mixins.transition();

        .card-wrapper {
            position: relative;
            width: 100%;
            height: auto;

            .effects {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                box-shadow:
                    0 functions.rem(2) functions.rem(6) functions.rem(-2) var(--color-creature-card-light-top) inset,
                    0 functions.rem(-2) functions.rem(8) functions.rem(1) var(--color-creature-card-light-bottom) inset;

                .finger-prints {
                    width: 100%;
                    height: 100%;
                    background: url("/images/finger-prints/1.jpg");
                    background-position: center;
                    background-repeat: no-repeat;
                    background-size: cover;
                    mix-blend-mode: plus-lighter;
                    opacity: 0.3;
                    will-change: opacity;

                    @include mixins.transition(opacity, 0.3s);
                }

                &::before, &::after {
                    content: "";
                    position: absolute;
                    left: 50%;
                    opacity: 0;
                    width: 100%;
                    height: 20%;
                    pointer-events: none;
                    filter: blur(functions.rem(30));
                    will-change: transform, opacity;

                    @include mixins.transition(all, 0.3s);
                }

                &::before {
                    top: 0;
                    transform: translateX(-50%) translateY(-100%);
                    background-color: var(--color-creature-card-reflection-one);
                    height: 20%;
                }
                &::after {
                    bottom: 30%;
                    transform: translateX(-50%) translateY(100%);
                    background-color: var(--color-creature-card-reflection-two);
                    height: 10%;
                }
            }

            img {
                width: 100%;
                height: auto;
            }

            .info {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                padding: functions.rem(12);
            }

            .hover-info {
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: auto;
                padding: functions.rem(12);
                opacity: 0;
                will-change: opacity;

                @include mixins.displayFlex(row, 20, space-between, flex-start, nowrap);
                @include mixins.transition(opacity, 0.3s);

                .elements, .classification {
                    position: relative;
                    width: max-content;
                    @include mixins.displayFlex(row, 4, flex-start, flex-start, nowrap);

                    &::before {
                        content: "";
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 140%;
                        background-color: black;
                        pointer-events: none;
                        filter: blur(functions.rem(14));
                        z-index: -1;
                    }
                }

                .elements .element {
                    flex-shrink: 0;
                    width: functions.rem(22);
                    height: functions.rem(22);

                    img {
                        flex-shrink: 0;
                        width: 100%;
                        height: 100%;
                    }
                }
            }
        }

        &:hover {
            transform: rotate3d(1, 0, 0, 8deg);
        }

        &:hover .card-wrapper .hover-info {
            opacity: 1;
        }

        &:hover .card-wrapper .effects {
            box-shadow:
                0 functions.rem(4) functions.rem(4) functions.rem(-2) var(--color-creature-card-light-top-hover) inset,
                0 functions.rem(-4) functions.rem(6) functions.rem(1) var(--color-creature-card-light-bottom-hover) inset;

            .finger-prints {
                opacity: 1;
            }

            &::before, &::after {
                opacity: 1;
            }
            &::before {
                transform: translateX(-70%) translateY(0);
            }
            &::after {
                transform: translateX(-50%) translateY(0);
            }
        }
    }
</style>