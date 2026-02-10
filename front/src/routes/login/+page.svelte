<script lang="ts">
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth.svelte';
	import { loginApi, getMeApi } from '$lib/api';
	import Button from '$lib/components/Button.svelte';

	let username = $state('');
	let password = $state('');
	let error = $state<string | null>(null);
	let isLoading = $state(false);

	async function handleLogin(e: Event) {
		e.preventDefault();
		error = null;
		isLoading = true;

		try {
			// Get token
			const tokenResponse = await loginApi(username, password);
			const token = tokenResponse.access_token;

			// Get user info
			const user = await getMeApi(token);

			// Store auth state
			authStore.setAuth(token, user);

			// Redirect to home
			goto('/');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Login failed';
		} finally {
			isLoading = false;
		}
	}
</script>

<svelte:head>
	<title>Login - Creature</title>
</svelte:head>

<div class="login-container">
	<div class="login-card">
		<div class="login-header">
			<h1>Creature</h1>
			<p>Sign in to your account</p>
		</div>

		<form onsubmit={handleLogin}>
			{#if error}
				<div class="error-message">
					{error}
				</div>
			{/if}

			<div class="input-group">
				<label for="username">Username</label>
				<input
					id="username"
					type="text"
					bind:value={username}
					placeholder="Enter your username"
					required
					autocomplete="username"
				/>
			</div>

			<div class="input-group">
				<label for="password">Password</label>
				<input
					id="password"
					type="password"
					bind:value={password}
					placeholder="Enter your password"
					required
					autocomplete="current-password"
				/>
			</div>

			<div class="button-container">
				<Button type="primary" text={isLoading ? 'Signing in...' : 'Sign In'} isDisabled={isLoading} />
			</div>
		</form>

		<div class="register-link">
			<p>Don't have an account? <a href="/register">Register</a></p>
		</div>
	</div>
</div>

<style lang="scss">
	@use '../../lib/styles/abstracts/variables' as variables;
	@use '../../lib/styles/abstracts/mixins' as mixins;
	@use '../../lib/styles/abstracts/functions' as functions;

	.login-container {
		width: 100%;
		min-height: 100vh;
		padding: functions.rem(40);

		@include mixins.displayFlex(column, 0, center, center);
	}

	.login-card {
		width: 100%;
		max-width: functions.rem(420);
		padding: functions.rem(40);
		border-radius: functions.rem(24);
		background-color: var(--color-card-background);
		box-shadow:
			0 functions.rem(4) functions.rem(6) functions.rem(-2) var(--color-input-button-light-top)
				inset,
			0 functions.rem(-4) functions.rem(12) functions.rem(2) var(--color-input-button-light-bottom)
				inset;
	}

	.login-header {
		text-align: center;
		margin-bottom: functions.rem(32);

		h1 {
			font-family: variables.$font-title;
			font-size: functions.rem(48);
			margin-bottom: functions.rem(8);
			background: linear-gradient(
				135deg,
				var(--color-button-primary-background) 0%,
				var(--color-input-button-light-top) 100%
			);
			-webkit-background-clip: text;
			-webkit-text-fill-color: transparent;
			background-clip: text;
		}

		p {
			font-size: functions.rem(16);
			opacity: 0.6;
		}
	}

	form {
		@include mixins.displayFlex(column, 20, stretch, stretch);
	}

	.error-message {
		padding: functions.rem(12) functions.rem(16);
		border-radius: functions.rem(12);
		background-color: functions.color(semantic, error, 80%, 20%);
		color: functions.color(semantic, error, 80%, 70%);
		font-size: functions.rem(14);
		text-align: center;
	}

	.input-group {
		@include mixins.displayFlex(column, 8, stretch, stretch);

		label {
			font-family: variables.$font-title;
			font-size: functions.rem(18);
			color: var(--color-input-label);
		}

		input {
			border: none;
			outline: none;
			width: 100%;
			height: functions.rem(variables.$input-height);
			padding: 0 functions.rem(variables.$input-padding);
			border-radius: functions.rem(variables.$input-radius);
			font-size: functions.rem(variables.$input-font-size);
			background: transparent;
			color: var(--color-input-text);
			border: solid 1px var(--color-input-border);

			@include mixins.transition;

			&::placeholder {
				color: var(--color-input-placeholder);
			}

			&:focus {
				border-color: var(--color-button-primary-background);
				box-shadow: 0 0 functions.rem(20) functions.rem(-10)
					var(--color-button-primary-background);
			}
		}
	}

	.button-container {
		margin-top: functions.rem(12);

		:global(button) {
			width: 100%;
		}
	}

	.register-link {
		margin-top: functions.rem(24);
		text-align: center;

		p {
			font-size: functions.rem(14);
			opacity: 0.6;

			a {
				color: var(--color-button-primary-background);
				text-decoration: underline;

				&:hover {
					opacity: 0.8;
				}
			}
		}
	}
</style>

