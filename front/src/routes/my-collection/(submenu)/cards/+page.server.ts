import type { PageServerLoad } from "./$types";
import {
	getAllCardsCardsGet,
	getAllElementsGet,
	getAllTypesGet,
	getAllCharactersGet,
} from "$lib/api";
import { getAuthHeaders } from "$lib/server/auth";

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const [cardsRes, elementsRes, typesRes, charactersRes] = await Promise.all([
		getAllCardsCardsGet({ headers, throwOnError: true }),
		getAllElementsGet({ headers, throwOnError: true }),
		getAllTypesGet({ headers, throwOnError: true }),
		getAllCharactersGet({ headers, throwOnError: true }),
	]);

	return {
		cards: cardsRes.data,
		elements: elementsRes.data,
		types: typesRes.data,
		characters: charactersRes.data,
	};
};
