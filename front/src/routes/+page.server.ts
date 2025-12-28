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
import { NO_AUTH_ROUTES } from '$lib/constants';

export const load: PageServerLoad = async ({ locals, url }) => {
	// Skip loading data for public routes (login/register)
	const isPublicRoute = NO_AUTH_ROUTES.some((route) => url.pathname === route || url.pathname.startsWith(route));
	if (isPublicRoute) {
		return {};
	}

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
