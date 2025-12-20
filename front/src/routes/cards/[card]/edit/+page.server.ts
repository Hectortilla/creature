import type { PageServerLoad } from './$types';
import {
	getAllCardsCardsGet,
	getCardCardsValueGet,
	getAllElementsElementsGet,
	getAllTypesTypesGet,
	getAllCharactersCharactersGet,
	getAllAttacksAttacksGet,
	getAllAbilitiesAbilitiesGet,
	getAllAssociationsAssociationsGet
} from '$lib/api/config';

export const load: PageServerLoad = async ({ params }) => {
	const { card } = params;

	if (!card) {
		throw new Error("Card parameter is missing");
	}

	const [allCardsRes, cardsRes, elementsRes, typesRes, charactersRes, attacksRes, abilitiesRes, associationsRes] = await Promise.all([
		getAllCardsCardsGet(),
		getCardCardsValueGet({ path: { value: card } }),
		getAllElementsElementsGet(),
		getAllTypesTypesGet(),
		getAllCharactersCharactersGet(),
		getAllAttacksAttacksGet(),
		getAllAbilitiesAbilitiesGet(),
		getAllAssociationsAssociationsGet()
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
