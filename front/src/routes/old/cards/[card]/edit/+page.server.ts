import type { PageServerLoad } from './$types';
import {
	getAllCardsCardsGet,
	getCardCardsValueGet,
	getAllElementsGet,
	getAllTypesGet,
	getAllCharactersGet,
	getAllAttacksAttacksGet,
	getAllAbilitiesGet,
	getAllAssociationsGet
} from '$lib/api';
import { getAuthHeaders } from '$lib/server/auth';

export const load: PageServerLoad = async ({ params, locals }) => {
	const headers = getAuthHeaders(locals);
	const { card } = params;

	if (!card) {
		throw new Error("Card parameter is missing");
	}

	const [allCardsRes, cardsRes, elementsRes, typesRes, charactersRes, attacksRes, abilitiesRes, associationsRes] = await Promise.all([
		getAllCardsCardsGet({ headers }),
		getCardCardsValueGet({ path: { value: card }, headers }),
		getAllElementsGet({ headers }),
		getAllTypesGet({ headers }),
		getAllCharactersGet({ headers }),
		getAllAttacksAttacksGet({ headers }),
		getAllAbilitiesGet({ headers }),
		getAllAssociationsGet({ headers })
	]);

	return {
		params,
		all_cards: allCardsRes.data ?? [],
		cards: cardsRes.data ?? [],
		elements: elementsRes.data ?? [],
		types: typesRes.data ?? [],
		characters: charactersRes.data ?? [],
		attacks: attacksRes.data ?? [],
		abilities: abilitiesRes.data ?? [],
		associations: associationsRes.data ?? []
	};
};
