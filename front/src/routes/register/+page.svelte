<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth.svelte';
	import { registerApi, loginApi, getMeApi } from '$lib/api';
	import Button from '$lib/components/Button.svelte';

	let username = $state('');
	let email = $state('');
	let fullName = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let error = $state<string | null>(null);
	let isLoading = $state(false);

	async function handleRegister(e: Event) {
		e.preventDefault();
		error = null;

		// Validate passwords match
		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}

		isLoading = true;

		try {
			// Register user
			await registerApi({
				username,
				password,
				email: email || undefined,
				full_name: fullName || undefined
			});

			// Auto-login after registration
			const tokenResponse = await loginApi(username, password);
			const token = tokenResponse.access_token;

			// Get user info
			const user = await getMeApi(token);

			// Store auth state
			auth.setAuth(token, user);

			// Redirect to home
			goto('/');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Registration failed';
		} finally {
			isLoading = false;
		}
	}
</script>

<svelte:head>
	<title>Register - Creature</title>
</svelte:head>

<div class="register-container">
	<div class="register-card">
		<div class="register-header">
			<h1>Creature</h1>
			<p>Create your account</p>
		</div>

		<form onsubmit={handleRegister}>
			{#if error}
				<div class="error-message">
					{error}
				</div>
			{/if}

			<div class="input-group">
				<label for="username">Username <span class="required">*</span></label>
				<input
					id="username"
					type="text"
					bind:value={username}
					placeholder="Choose a username"
					required
					autocomplete="username"
				/>
			</div>

			<div class="input-group">
				<label for="email">Email</label>
				<input
					id="email"
					type="email"
					bind:value={email}
					placeholder="your@email.com"
					autocomplete="email"
				/>
			</div>

			<div class="input-group">
				<label for="fullName">Full Name</label>
				<input
					id="fullName"
					type="text"
					bind:value={fullName}
					placeholder="Your full name"
					autocomplete="name"
				/>
			</div>

			<div class="input-group">
				<label for="password">Password <span class="required">*</span></label>
				<input
					id="password"
					type="password"
					bind:value={password}
					placeholder="Choose a password"
					required
					autocomplete="new-password"
				/>
			</div>

			<div class="input-group">
				<label for="confirmPassword">Confirm Password <span class="required">*</span></label>
				<input
					id="confirmPassword"
					type="password"
					bind:value={confirmPassword}
					placeholder="Confirm your password"
					required
					autocomplete="new-password"
				/>
			</div>

			<div class="button-container">
				<Button
					type="primary"
					text={isLoading ? 'Creating account...' : 'Create Account'}
					isDisabled={isLoading}
				/>
			</div>
		</form>

		<div class="login-link">
			<p>Already have an account? <a href="/login">Sign in</a></p>
		</div>
	</div>
</div>

<style lang="scss">
	@use '$lib/styles/abstracts/variables' as variables;
	@use '$lib/styles/abstracts/mixins' as mixins;
	@use '$lib/styles/abstracts/functions' as functions;

	.register-container {
		width: 100%;
		min-height: 100vh;
		padding: functions.rem(40);

		@include mixins.displayFlex(column, 0, center, center);
	}

	.register-card {
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

	.register-header {
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
		@include mixins.displayFlex(column, 16, stretch, stretch);
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

			.required {
				color: functions.color(semantic, error, 80%, 60%);
			}
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

	.login-link {
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

