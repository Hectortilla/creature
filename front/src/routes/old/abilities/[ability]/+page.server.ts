import type { PageServerLoad } from "./$types";
import {
	getOneAbilitiesValueGet,
	getCardsByAbilityCardsByAbilityAbilityCodeGet,
} from "$lib/api";
import { getAuthHeaders } from "$lib/server/auth";

export const load: PageServerLoad = async ({ params, locals }) => {
	const headers = getAuthHeaders(locals);
	const { ability } = params;

	if (!ability) {
		throw new Error("Ability parameter is missing");
	}

	const [abilityRes, cardsRes] = await Promise.all([
		getOneAbilitiesValueGet({ path: { value: ability }, headers }),
		getCardsByAbilityCardsByAbilityAbilityCodeGet({
			path: { ability_code: Number(ability) },
			headers,
		}),
	]);

	return {
		params,
		ability: abilityRes.data ?? null,
		cards_use_ability: cardsRes.data ?? [],
	};
};
