import type { PageServerLoad } from './$types';
import {
	getAllCardsCardsGet,
	getAllElementsElementsGet,
	getAllTypesTypesGet,
	getAllCharactersCharactersGet,
	getAllAttacksAttacksGet,
	getAllAbilitiesAbilitiesGet,
	getAllAssociationsAssociationsGet
} from '$lib/api/config';

export const load: PageServerLoad = async () => {
	const [cardsRes, elementsRes, typesRes, charactersRes, attacksRes, abilitiesRes, associationsRes] = await Promise.all([
		getAllCardsCardsGet(),
		getAllElementsElementsGet(),
		getAllTypesTypesGet(),
		getAllCharactersCharactersGet(),
		getAllAttacksAttacksGet(),
		getAllAbilitiesAbilitiesGet(),
		getAllAssociationsAssociationsGet()
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
