import type { PageServerLoad } from './$types';
import {
	getAllCardsCardsGet,
	getAllElementsElementsGet,
	getAllTypesTypesGet,
	getAllCharactersCharactersGet,
	getAllAttacksAttacksGet,
	getAllAbilitiesAbilitiesGet,
	getAllAssociationsAssociationsGet
} from '$lib/api';
import { getAuthHeaders } from '$lib/server/auth';

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const [cardsRes, elementsRes, typesRes, charactersRes, attacksRes, abilitiesRes, associationsRes] = await Promise.all([
		getAllCardsCardsGet({ headers }),
		getAllElementsElementsGet({ headers }),
		getAllTypesTypesGet({ headers }),
		getAllCharactersCharactersGet({ headers }),
		getAllAttacksAttacksGet({ headers }),
		getAllAbilitiesAbilitiesGet({ headers }),
		getAllAssociationsAssociationsGet({ headers })
	]);

	return {
		cards: cardsRes.data ?? [],
		elements: elementsRes.data ?? [],
		types: typesRes.data ?? [],
		characters: charactersRes.data ?? [],
		attacks: attacksRes.data ?? [],
		abilities: abilitiesRes.data ?? [],
		associations: associationsRes.data ?? []
	};
};
