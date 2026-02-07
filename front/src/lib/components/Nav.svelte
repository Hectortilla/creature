<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { blur } from 'svelte/transition';
	import { authStore } from '$lib/stores/auth.svelte';

	// Icons
	import arrowIcon from '$lib/icons/arrow.svg?raw'

	const navLinks = [
		{ href: '/', label: 'Inicio', subMenu: [] },
		{ 
			href: '',
			label: 'Crear',
			subMenu: [
				{ href: '/cards/create', label: 'Crear Carta' },
				{ href: '/attacks/create', label: 'Crear Ataque' },
				{ href: '/abilities/create', label: 'Crear Habilidad' },
				{ href: '/associations/create', label: 'Crear Asociación' }
			]
		},
		{ href: '/cards', label: 'Cartas', subMenu: [] },
		{ href: '/clasification', label: 'Clasificación', subMenu: [] },
		{ href: '/attacks', label: 'Ataques', subMenu: [] },
		{ href: '/abilities', label: 'Habilidades', subMenu: [] },
		{ href: '/associations', label: 'Asociaciones', subMenu: [] },
		{ href: '/decks', label: 'Mazos', subMenu: [] },
		{ href: '/debug', label: 'Debug', subMenu: [] },
		{ href: '/game', label: 'Jugar', subMenu: [] },
	];

	let shownIndex = $state<number | null>(null)

	function showSubItem(index: number) {
		shownIndex = index;
	}

	function hideItem() {
		shownIndex = null;
	}

	function handleLogout() {
		authStore.clearAuth();
		goto('/login');
	}
</script>

<nav>
	<ul class="item-ul">
		{#each navLinks as item, i}
			<li 
				class="item" 
				onmouseenter={() => {showSubItem(i)}} 
				onmouseleave={() => {hideItem()}} 
				onfocus={() => {showSubItem(i)}}
			>
				{#if item.subMenu.length !== 0 && item.href === ''}
					<div class="p">
						<div class="icon" class:active={shownIndex === i}>
							{@html arrowIcon}
						</div>
						{item.label}
					</div>
					{#if shownIndex === i}
						<div class="ul-wrapper">
							<ul class="subitem-ul" transition:blur>
								{#each item.subMenu as subItem }
									<li class="subitem">
										<a
											href={subItem.href}
											class:active={page.url.pathname === subItem.href}
											onclick={() => {hideItem()}} 
										>{subItem.label}</a>
									</li>
								{/each}
							</ul>
						</div>
					{/if}
					
				{:else}
					<a class="item" href={item.href} class:active={page.url.pathname === item.href}>{item.label}</a>
				{/if}
			</li>
		{/each}
	</ul>

	{#if authStore.isAuthenticated}
		<div class="user-section">
			<span class="username">{authStore.user?.username}</span>
			<button class="logout-btn" onclick={handleLogout}>Salir</button>
		</div>
	{/if}
</nav>

<style lang="scss">
	@use "$lib/styles/abstracts/variables" as variables;
	@use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

	nav {
		$padding: 6;
		$border-radius: 16;

		position: relative;
		width: 100%;
		padding: functions.rem($padding);
		border-radius: functions.rem($border-radius);
		z-index: 11;

		@include mixins.displayFlex(row, 0, space-between, center);

		ul.item-ul {
			position: relative;
			@include mixins.displayFlex(row, $padding, flex-start, flex-start);

			li.item {
				position: relative;
				@include mixins.displayFlex(row, 0, center, center);

				.p {
					font-family: variables.$font-title;
					font-size: functions.rem(20);
					position: relative;
					padding: functions.rem(6) functions.rem(10);
					opacity: .6;
					cursor: default;

					@include mixins.displayFlex(row, 2, center, center, nowrap);

					.icon {
						width: functions.rem(16);
						height: functions.rem(16);
						transform: rotate(-90deg);

						@include mixins.transition();

						&.active {
							transform: rotate(0);
						}
					}

				}

				a.item {
					font-family: variables.$font-title;
					font-size: functions.rem(20);
					position: relative;
					padding: functions.rem(6) functions.rem(10);
					border-radius: calc(functions.rem($border-radius) - functions.rem($padding));
					opacity: .6;

					@include mixins.transition();

					&:hover:not(.active) {
						opacity: 1;
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
						background-color: var(--color-nav-active-background);
						opacity: 1;
						text-shadow: 0 functions.rem(6) functions.rem(6) var(--color-nav-active-text-shadow);
						cursor: default;
						pointer-events: none;
						box-shadow:
							0 functions.rem(2) functions.rem(2) functions.rem(-2) var(--color-nav-active-light-top) inset,
							0 functions.rem(-2) functions.rem(8) functions.rem(1) var(--color-nav-active-light-bottom) inset;

						&::before {
							opacity: 1;
						}
					}
				}

				.ul-wrapper {
					position: absolute;
					bottom: 0;
					left: 50%;
					transform: translateX(-50%) translateY(100%);
					padding-top: functions.rem(10);

					ul.subitem-ul {
						width: max-content;
						height: auto;
						background-color: var(--color-pop-in-background);
						border-radius: functions.rem(12);
						backdrop-filter: blur(functions.rem(12));
						overflow: hidden;

						@include mixins.displayFlex (column, 0, center, stretch, nowrap);

						li.subitem {
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
			}
		}

		.user-section {
			@include mixins.displayFlex(row, 12, center, center);

			.username {
				font-family: variables.$font-title;
				font-size: functions.rem(18);
				opacity: 0.8;
			}

			.logout-btn {
				font-family: variables.$font-title;
				font-size: functions.rem(16);
				padding: functions.rem(6) functions.rem(14);
				border-radius: functions.rem(10);
				background-color: transparent;
				border: solid 1px var(--color-input-border);
				color: var(--color-input-text);
				cursor: pointer;
				opacity: 0.6;

				@include mixins.transition;

				&:hover {
					opacity: 1;
					background-color: var(--color-input-button-background);
				}
			}
		}
	}
</style>