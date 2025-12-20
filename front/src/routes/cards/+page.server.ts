import type { PageServerLoad } from './$types';
import {
	getAllCardsCardsGet,
	getAllElementsElementsGet,
	getAllTypesTypesGet,
	getAllCharactersCharactersGet
} from '$lib/api/config';

export const load: PageServerLoad = async () => {
	const [cardsRes, elementsRes, typesRes, charactersRes] = await Promise.all([
		getAllCardsCardsGet(),
		getAllElementsElementsGet(),
		getAllTypesTypesGet(),
		getAllCharactersCharactersGet()
	]);

	return {
		cards: cardsRes.data ?? [],
		elements: elementsRes.data ?? [],
		types: typesRes.data ?? [],
		characters: charactersRes.data ?? []
	};
};
