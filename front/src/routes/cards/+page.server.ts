import type { PageServerLoad } from './$types';
import {
	getAllCardsCardsGet,
	getAllElementsElementsGet,
	getAllTypesTypesGet,
	getAllCharactersCharactersGet
} from '$lib/api';
import { getAuthHeaders } from '$lib/server/auth';

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const [cardsRes, elementsRes, typesRes, charactersRes] = await Promise.all([
		getAllCardsCardsGet({ headers }),
		getAllElementsElementsGet({ headers }),
		getAllTypesTypesGet({ headers }),
		getAllCharactersCharactersGet({ headers })
	]);

	return {
		cards: cardsRes.data ?? [],
		elements: elementsRes.data ?? [],
		types: typesRes.data ?? [],
		characters: charactersRes.data ?? []
	};
};
