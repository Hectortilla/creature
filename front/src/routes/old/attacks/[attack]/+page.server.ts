import type { PageServerLoad } from './$types';
import {
	getAttackAttacksValueGet,
	getCardsByAttackCardsByAttackAttackCodeGet
} from '$lib/api';
import { getAuthHeaders } from '$lib/server/auth';

export const load: PageServerLoad = async ({ params, locals }) => {
	const headers = getAuthHeaders(locals);
	const { attack } = params;

	if (!attack) {
		throw new Error("Attack parameter is missing");
	}

	const [attackRes, cardsRes] = await Promise.all([
		getAttackAttacksValueGet({ path: { value: attack }, headers }),
		getCardsByAttackCardsByAttackAttackCodeGet({ path: { attack_code: Number(attack) }, headers })
	]);

	return {
		params,
		attack: attackRes.data ?? null,
		cards_use_attack: cardsRes.data ?? []
	};
};
