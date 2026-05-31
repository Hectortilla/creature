<script lang="ts">
	import { page } from '$app/state';
	import { parallax } from '$lib/actions/parallax';

	// Components
	import Nav from '$lib/components/menu/Nav.svelte';

	// Icons
	import favicon from '$lib/assets/icons/favicon.svg';

	// SCSS
	import "$lib/styles/main.scss";

	let { children } = $props();

	// Routes where nav should be hidden
	const hideNavRoutes = ['/login', '/register'];
	const shouldShowNav = $derived(!hideNavRoutes.includes(page.url.pathname));
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="pos-center">
	<img use:parallax={{ intensity: 10, reverse: true }} class="dust" src="/images/dust.jpg" alt=""/>
</div>

{#if shouldShowNav}
	<Nav />
{/if}

{@render children?.()}

<style lang="scss">
	@use "../lib/styles/abstracts/variables" as variables;
	@use "../lib/styles/abstracts/functions" as functions;
	@use "../lib/styles/abstracts/mixins" as mixins;

	.pos-center {
		position: fixed;
		top: 0;
		left: 0;
		width: 100vw;
		height: 100vh;
		z-index: 999;
		pointer-events: none;
		mix-blend-mode: screen;

		@include mixins.displayFlex(column, 0, center, center);
	}

	.dust {
		width: 116vw;
		max-width: none;
		height: 116vh;
		object-fit: cover;
		filter: contrast(1.8);
		opacity: .2;
	}
</style>
