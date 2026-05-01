import type { AttackDefinition } from '../game/models';

export interface AttackFormatLines {
	title: string;
	stats: string;
	id: string;
	cost: string | null;
	effect: string | null;
	description: string | null;
}

export function formatAttackLines(atk: AttackDefinition): AttackFormatLines {
	const cost = atk.necessary_force && atk.necessary_force.length > 0
		? atk.necessary_force.map(e => `e${e.element_id}:${e.amount}`).join(', ')
		: null;

	let id = `id: ${atk.attack_id}`;
	if (atk.dice_rolls != null) id += ` | dice: ${atk.dice_rolls}`;

	return {
		title: `ATK: ${atk.name ?? 'Attack'}`,
		stats: `${atk.damage ?? '?'} dmg | ${atk.type} | elem ${atk.element_id}`,
		id,
		cost: cost ? `Cost: ${cost}` : null,
		effect: atk.effect ? `Effect: ${atk.effect}` : null,
		description: atk.description ?? null,
	};
}
