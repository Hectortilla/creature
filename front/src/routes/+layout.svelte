<script lang="ts">
	import { page } from '$app/state';

	// Components
	import Nav from '$lib/components/Nav.svelte';
	import RollDice from '$lib/components/RollDice.svelte';

	// Icons
	import favicon from '$lib/icons/favicon.svg';

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

{#if shouldShowNav}
	<div id="menu">
		<Nav />
	</div>
{/if}

{@render children?.()}

{#if shouldShowNav}
	<RollDice />
{/if}

<style lang="scss">
	@use "$lib/styles/abstracts/variables" as variables;
	@use "$lib/styles/abstracts/functions" as functions;
	@use "$lib/styles/abstracts/mixins" as mixins;

	#menu {
		padding: functions.rem(20) functions.rem(20) functions.rem(80) functions.rem(20);

		@include mixins.displayFlex(row, 0, center, flex-start);
	}
</style>
