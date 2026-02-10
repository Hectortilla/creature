<script lang="ts">
    import { page } from '$app/state';
    import { blur } from 'svelte/transition';

    // Icons
	import arrowIcon from '$lib/assets/icons/arrow.svg?raw'

    interface NavLink {
        href?: string | null;
        label?: string;
        subMenu?: NavLink[] | null;
    }

    interface Props {
        label: string;
        isOpenMenu: boolean;
        subMenu?: NavLink[] | null;
        hideSubMenuOnClick?: () => void;
    }

    let {
        isOpenMenu = false,
        subMenu = [],
        label = "Menu",
        hideSubMenuOnClick,
    }: Props = $props();
</script>


<div class="dropdown-trigger">
    <div class="icon" class:active={isOpenMenu}>
        {@html arrowIcon}
    </div>
    {label}
</div>
{#if isOpenMenu}
    <div class="submenu-ul-wrapper">
        <ul class="submenu-ul" transition:blur>
            {#each subMenu as subItem }
                <li class="submenu-li">
                    <a
                        href={subItem.href}
                        class:active={page.url.pathname === subItem.href}
                        onclick={hideSubMenuOnClick} 
                    >{subItem.label}</a>
                </li>
            {/each}
        </ul>
    </div>
{/if}

<style lang="scss">
    @use "../../styles/abstracts/variables" as variables;
	@use "../../styles/abstracts/mixins" as mixins;
	@use "../../styles/abstracts/functions" as functions;

    .dropdown-trigger {
        position: relative;
        font-size: functions.rem(20);
        padding-top: functions.rem(4);
        cursor: default;

        @include mixins.fontProps("title", 400, 100, normal);
        @include mixins.displayFlex(row, 6, center, center, nowrap);

        .icon {
            width: functions.rem(16);
            height: functions.rem(16);
            margin-bottom: functions.rem(4);
            transform: rotate(0);
            color: var(--color-nav-dropdown-icon);

            @include mixins.transition();

            &.active {
                transform: rotate(-90deg);
            }
        }
	}

    .submenu-ul-wrapper {
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%) translateY(100%);
        padding-top: functions.rem(10);

        ul.submenu-ul {
            width: max-content;
            height: auto;
            background-color: var(--color-pop-in-background);
            border-radius: functions.rem(12);
            backdrop-filter: blur(functions.rem(12));
            overflow: hidden;

            @include mixins.displayFlex (column, 0, center, stretch, nowrap);

            li.submenu-li {
                flex: 1;
                border-top: solid 1px var(--color-pop-in-background);

                &:first-child {
                    border: none;
                }

                a {
                    display: block;
                    width: 100%;
                    padding: functions.rem(10) functions.rem(16);
                    text-align: center;
                    font-family: variables.$font-title;
                    font-size: functions.rem(20);
                    opacity: .6;

                    @include mixins.transition;

                    &:hover {
                        background-color: hsla(0deg,0%,40%,.2);
                    }

                    &.active {
                        opacity: .3;
                        pointer-events: none;
                    }
                }
            }
        }
    }
</style>