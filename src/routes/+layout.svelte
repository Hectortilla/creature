<script lang="ts">
	// Components
	import Nav from '$lib/components/Nav.svelte';
	import RollDice from '$lib/components/RollDice.svelte';

	// Icons
	import favicon from '$lib/icons/favicon.svg';

	// SCSS
	import "$lib/styles/main.scss";

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div id="menu">
	<Nav />
</div>

{@render children?.()}

<RollDice />

<style lang="scss">
	@use "$lib/styles/abstracts/variables" as variables;
	@use "$lib/styles/abstracts/functions" as functions;
	@use "$lib/styles/abstracts/mixins" as mixins;

	#menu {
		padding: functions.rem(20) functions.rem(20) functions.rem(80) functions.rem(20);

		@include mixins.displayFlex(row, 0, center, flex-start);
	}
</style>
