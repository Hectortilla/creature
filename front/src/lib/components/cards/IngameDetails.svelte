<script lang="ts">
	import type { IngameCardState } from '$lib/stores/hoveredCard';
	import Divider from '$lib/components/Divider.svelte';
	import healthIcon from '$lib/icons/health.svg?raw';

	interface Props {
		state: IngameCardState;
	}

	let { state }: Props = $props();
</script>

<div class="ingame-details">
	<Divider title="Estado en juego" hasMargins={false} />
	<div class="ingame-grid">
		<div class="row">
			<span class="label">Zona</span>
			<span class="value">{state.zone}</span>
		</div>
		<div class="row">
			<span class="label">Estado</span>
			<span class="value">{state.status}</span>
		</div>
		<div class="row">
			<span class="label">Vivo</span>
			<span class="value" class:bad={!state.isAlive}>{state.isAlive ? 'Sí' : 'No'}</span>
		</div>
		<div class="row">
			<span class="label">Turnos en zona</span>
			<span class="value">{state.turnsInZone}</span>
		</div>
		<div class="row">
			<span class="label">Atacó este turno</span>
			<span class="value" class:dim={!state.hasAttackedThisTurn}>{state.hasAttackedThisTurn ? 'Sí' : 'No'}</span>
		</div>
		<div class="row">
			<span class="label">Intercambió este turno</span>
			<span class="value" class:dim={!state.swappedThisTurn}>{state.swappedThisTurn ? 'Sí' : 'No'}</span>
		</div>
	</div>

	<Divider title="Capacidades" hasMargins={false} />
	<div class="capabilities">
		<span class="cap" class:disabled={!state.canAttack}>Atacar</span>
		<span class="cap" class:disabled={!state.canPromote}>Promover</span>
		<span class="cap" class:disabled={!state.canEvolve}>Evolucionar</span>
	</div>

	<Divider title="Vida actual" hasMargins={false} />
	<div class="health">
		<div class="icon">{@html healthIcon}</div>
		<p class="current" class:hurt={state.currentHealth < state.maxHealth}>{state.currentHealth}</p>
		<p class="separator">/</p>
		<p class="max">{state.maxHealth}</p>
	</div>
</div>

<style lang="scss">
	@use '$lib/styles/abstracts/variables' as variables;
	@use '$lib/styles/abstracts/mixins' as mixins;
	@use '$lib/styles/abstracts/functions' as functions;

	.ingame-details {
		width: 100%;
		@include mixins.displayFlex(column, 12, flex-start, flex-start, nowrap);
	}

	.ingame-grid {
		width: 100%;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: functions.rem(6) functions.rem(20);

		.row {
			@include mixins.displayFlex(row, 8, space-between, baseline, nowrap);

			.label {
				font-size: functions.rem(13);
				opacity: 0.5;
			}

			.value {
				font-family: variables.$font-number;
				font-size: functions.rem(14);

				&.dim { opacity: 0.4; }
				&.bad { color: functions.color(semantic, error, 80%, 60%); }
			}
		}
	}

	.capabilities {
		@include mixins.displayFlex(row, 8, flex-start, center, wrap);

		.cap {
			padding: functions.rem(4) functions.rem(10);
			border-radius: functions.rem(6);
			background-color: var(--color-pop-in-background);
			font-size: functions.rem(13);

			&.disabled {
				opacity: 0.35;
				text-decoration: line-through;
			}
		}
	}

	.health {
		@include mixins.displayFlex(row, 6, flex-start, center, nowrap);

		.icon {
			width: functions.rem(20);
			height: functions.rem(20);
		}

		p {
			font-family: variables.$font-number;
			font-size: functions.rem(22);
			line-height: 100%;
		}

		.current.hurt { color: functions.color(semantic, error, 80%, 60%); }
		.separator { opacity: 0.4; }
		.max { opacity: 0.6; }
	}
</style>
