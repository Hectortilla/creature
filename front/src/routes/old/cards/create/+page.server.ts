import type { PageServerLoad } from "./$types";
import {
	getAllCardsCardsGet,
	getAllElementsGet,
	getAllTypesGet,
	getAllCharactersGet,
	getAllAttacksAttacksGet,
	getAllAbilitiesGet,
	getAllAssociationsGet,
} from "$lib/api";
import { getAuthHeaders } from "$lib/server/auth";

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const [
		cardsRes,
		elementsRes,
		typesRes,
		charactersRes,
		attacksRes,
		abilitiesRes,
		associationsRes,
	] = await Promise.all([
		getAllCardsCardsGet({ headers }),
		getAllElementsGet({ headers }),
		getAllTypesGet({ headers }),
		getAllCharactersGet({ headers }),
		getAllAttacksAttacksGet({ headers }),
		getAllAbilitiesGet({ headers }),
		getAllAssociationsGet({ headers }),
	]);

	return {
		cards: cardsRes.data ?? [],
		elements: elementsRes.data ?? [],
		types: typesRes.data ?? [],
		characters: charactersRes.data ?? [],
		attacks: attacksRes.data ?? [],
		abilities: abilitiesRes.data ?? [],
		associations: associationsRes.data ?? [],
	};
};
