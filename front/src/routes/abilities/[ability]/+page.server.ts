import type { PageServerLoad } from './$types';
import {
	getAbilityAbilitiesValueGet,
	getCardsByAbilityCardsByAbilityAbilityCodeGet
} from '$lib/api';

export const load: PageServerLoad = async ({ params }) => {
	const { ability } = params;

	if (!ability) {
		throw new Error("Ability parameter is missing");
	}

	const [abilityRes, cardsRes] = await Promise.all([
		getAbilityAbilitiesValueGet({ path: { value: ability } }),
		getCardsByAbilityCardsByAbilityAbilityCodeGet({ path: { ability_code: Number(ability) } })
	]);

	return {
		params,
		ability: abilityRes.data ?? null,
		cards_use_ability: cardsRes.data ?? []
	};
};
