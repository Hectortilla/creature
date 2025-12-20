import type { PageServerLoad } from './$types';
import {
	getAttackAttacksValueGet,
	getCardsByAttackCardsByAttackAttackCodeGet
} from '$lib/api/config';

export const load: PageServerLoad = async ({ params }) => {
	const { attack } = params;

	if (!attack) {
		throw new Error("Attack parameter is missing");
	}

	const [attackRes, cardsRes] = await Promise.all([
		getAttackAttacksValueGet({ path: { value: attack } }),
		getCardsByAttackCardsByAttackAttackCodeGet({ path: { attack_code: Number(attack) } })
	]);

	return {
		params,
		attack: attackRes.data ?? null,
		cards_use_attack: cardsRes.data ?? []
	};
};
