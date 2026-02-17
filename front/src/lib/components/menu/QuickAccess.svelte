<script lang="ts">
    import { page } from "$app/state";
    import { goto } from "$app/navigation";
    import { afterNavigate } from '$app/navigation';
    import { onMount } from 'svelte';
    import { tick } from 'svelte';
	import { FONT_BASE_SIZE } from "$lib/constants";

    // Components
    import IconButton from "$lib/components/buttons/IconButton.svelte";

    // Icons
    import Arrow from "$lib/assets/icons/arrow.svg?raw";

    interface Menu {
        label: string,
        submenu_label: string,
        amount_label: string,
        image: string,
        path: string,
    }

    interface Props {
        menu: Menu[],
        maxWidth?: number | null;
    }

    let {
        menu,
        maxWidth = null,
    }: Props = $props();

    let currentMenuIndex = $derived.by(() => {
        return menu.findIndex((m) => m.path === page.url.pathname);
    })
    let ulEl = $state<HTMLElement>();
    let translateX = $state(0);

    async function correctSelectedPosition() {
        if (!ulEl) return;
        await tick();

        const activeLi = ulEl.querySelector('li a.active')?.parentElement as HTMLElement;
        if (!activeLi) return;

        const viewport = ulEl.parentElement as HTMLElement;
        if (!viewport) return;

        const viewportWidth = viewport.offsetWidth;
        const ulWidth = ulEl.scrollWidth;

        const liLeft = activeLi.offsetLeft;

        const viewportStyle = getComputedStyle(viewport);

        const viewportPaddingLeft = parseFloat(viewportStyle.paddingLeft || '0');
        const viewportPaddingRight = parseFloat(viewportStyle.paddingRight || '0');

        let target = -liLeft + viewportPaddingRight;

        const maxTranslate = viewportWidth - ulWidth - (viewportPaddingRight + viewportPaddingLeft);
        if (target < maxTranslate) target = maxTranslate;

        if (target > 0) target = 0;

        translateX = target;
    }


    function changeSubPage(mov: number) {
        if (currentMenuIndex === -1) return;

        const nextIndex = currentMenuIndex + mov;

        if (nextIndex < 0 || nextIndex >= menu.length) return;

        const nextPath = menu[nextIndex].path;

        if (nextPath === page.url.pathname) return;

        goto(nextPath, { keepFocus: true });
    }

    onMount(() => {
        correctSelectedPosition();
    });

    afterNavigate(() => {
        correctSelectedPosition();
    });
</script>

<div class="collection-quick-menu variables">
    <div class="menu-items">
        <IconButton
            onClick={() => changeSubPage(-1)}
            rotateIcon={90}
            isDisabled={currentMenuIndex === 0}
            ariaLabel={currentMenuIndex === 0 ? 'Disabled': `Go to ${menu[currentMenuIndex - 1].submenu_label}`}
        >
            {@html Arrow}
        </IconButton>
        <div class="scroll-wrapper" style={`--max-width:${maxWidth ? maxWidth / FONT_BASE_SIZE + 'rem' : 'none'}`}>
            <ul bind:this={ulEl} style={`transform: translateX(${translateX}px)`}>
                {#each menu as {submenu_label, path}}
                    <li>
                        <a
                            class:active={page.url.pathname === path}
                            href={path}
                        >
                            {submenu_label}
                        </a>
                    </li>
                {/each}
            </ul>
        </div>
        <IconButton
            onClick={() => changeSubPage(+1)}
            rotateIcon={-90}
            isDisabled={currentMenuIndex === menu.length - 1}
            ariaLabel={currentMenuIndex === menu.length - 1 ? 'Disabled': `Go to ${menu[currentMenuIndex + 1].submenu_label}`}
        >
            {@html Arrow}
        </IconButton>
    </div>
</div>


<style lang="scss">
    @use "../../../lib/styles/abstracts/variables" as variables;
    @use "../../../lib/styles/abstracts/mixins" as mixins;
	@use "../../../lib/styles/abstracts/functions" as functions;

    .variables {
		--padding: #{
			0
			functions.rem(variables.$margin-page-desktop)
		};
	}

    .collection-quick-menu {
        position: absolute;
        top: functions.rem(140);
        left: 0;
        width: 100%;
        padding: var(--padding);
        z-index: 1;

        .menu-items {
            @include mixins.displayFlex(row, 0, flex-start, center, nowrap);

            .scroll-wrapper {
                width: max-content;
                max-width: var(--max-width);
                height: auto;
                overflow: hidden;
                padding: 0 functions.rem(18);

                -webkit-mask-image: linear-gradient(to right, transparent, black 10%, black 90%, transparent);
                -webkit-mask-repeat: no-repeat;
                -webkit-mask-size: 100% 100%;
                mask-image: linear-gradient(to right, transparent, black 10%, black 90%, transparent);
                mask-repeat: no-repeat;
                mask-size: 100% 100%;

                ul {
                    width: max-content;
                    height: functions.rem(50);
                    will-change: transform;

                    @include mixins.displayFlex(row, 0, flex-start, baseline, nowrap);
                    @include mixins.transition(.4s, transform);

                    li {
                        position: relative;
                        height: functions.rem(50);

                        @include mixins.displayFlex(row, 0, center, center, nowrap);

                        a {
                            font-size: functions.rem(24);
                            color: var(--color-submenu-color);
                            padding: functions.rem(6) functions.rem(10) 0 functions.rem(10);

                            @include mixins.fontProps('title', 400, 100, normal);
                            @include mixins.transition(.3s);
                            

                            &:not(.active) {
                                opacity: .4;

                                &:hover {
                                    opacity: .7¡6;
                                }
                            }

                            &.active {
                                font-size: functions.rem(32);
                                opacity: 1;
                                pointer-events: none;

                                @include mixins.stylishedText();
                            }
                        }
                    }
                }
            }
        }
    }
</style>