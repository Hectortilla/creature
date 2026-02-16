<script lang="ts">
	import { page } from '$app/state';

	// Constants
	import { NAV_LINKS } from "$lib/constants";

	// Icons
	import isoType from '$lib/assets/icons/iso-type.svg?raw';

	// Components
	import Dropdown from '$lib/components/menu/Dropdown.svelte';
	import Feature from '$lib/components/menu/Feature.svelte';

	let shownIndex = $state<number | null>(null)

	function showSubItem(index: number) {
		shownIndex = index;
	}

	function hideItem() {
		shownIndex = null;
	}
</script>

<nav class="variables">
	<div class="nav-wrapper">
		<a class="iso-type" href="/" class:active={page.url.pathname === '/'}>
			{@html isoType}
		</a>
		<ul class="nav-ul">
			{#each NAV_LINKS as item, i}
				<li 
					class="nav-li" 
					onmouseenter={() => {showSubItem(i)}} 
					onmouseleave={() => {hideItem()}} 
					onfocus={() => {showSubItem(i)}}
				>
					{#if item.subMenu}
						<Dropdown 
							label={item.label}
							isOpenMenu={shownIndex === i} 
							subMenu={item.subMenu} 
							hideSubMenuOnClick={() => {hideItem()}}
						/>
					{:else}
						<a
							class="nav-link"
							href={item.href}
							class:active={page.url.pathname === item.href}
						>{item.label}</a>
					{/if}
				</li>
			{/each}
		</ul>
	</div>
	<Feature />
</nav>

<style lang="scss">
	@use "../../styles/abstracts/variables" as variables;
	@use "../../styles/abstracts/mixins" as mixins;
	@use "../../styles/abstracts/functions" as functions;

	.variables {
		--padding: #{
			calc(functions.rem(variables.$margin-page-desktop) - functions.rem(10))
			functions.rem(variables.$margin-page-desktop)
			0
			functions.rem(variables.$margin-page-desktop)
		};
	}

	nav {
		$border-radius: 16;

		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		padding: var(--padding);
		z-index: 999;

		@include mixins.displayFlex(row, 18, space-between, center);

		.nav-wrapper {
			width: max-content;

			@include mixins.transition();
			@include mixins.displayFlex(row, 46, flex-start, center);

			.iso-type {
				width: functions.rem(36);
				height: functions.rem(36);

				&.active {
					pointer-events: none;
				}

				&:not(.active):hover {
					color: var(--color-nav-active-color);
				}
			}

			ul.nav-ul {
				position: relative;
				@include mixins.displayFlex(row, 40, flex-start, flex-start);

				li.nav-li {
					position: relative;
					@include mixins.displayFlex(row, 0, center, center);

					a.nav-link {
						position: relative;
						font-size: functions.rem(20);
						padding-top: functions.rem(4);
						
						@include mixins.fontProps("title", 400, 100, normal);
						@include mixins.transition();

						&:hover:not(.active) {
							color: var(--color-nav-active-color);
						}

						&::before {
							content: "";
							position: absolute;
							top: 0%;
							left: 50%;
							transform: translate(-50%, -50%);
							width: functions.rem(40);
							height: functions.rem(40);
							border-radius: 50%;
							background-color: var(--color-nav-active-point-light);
							filter: blur(functions.rem(38));
							z-index: -1;
							opacity: 0;
							
							@include mixins.transition();
						}

						&.active {
							color: var(--color-nav-active-color);
							text-shadow: 0 functions.rem(6) functions.rem(6) var(--color-nav-active-text-shadow);
							cursor: default;
							pointer-events: none;
							box-shadow:
								0 functions.rem(2) functions.rem(2) functions.rem(-2) var(--color-nav-active-light-top) inset,
								0 functions.rem(-2) functions.rem(8) functions.rem(1) var(--color-nav-active-light-bottom) inset;


							&::before {
								opacity: .4;
							}
						}
					}
				}
			}
		}
	}
</style>