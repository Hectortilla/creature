import type { PageServerLoad } from './$types';
import {
	getCardCardsValueGet,
	getAllElementsGet
} from '$lib/api';
import { getAuthHeaders } from '$lib/server/auth';

export const load: PageServerLoad = async ({ params, locals }) => {
	const headers = getAuthHeaders(locals);
	const { card } = params;

	if (!card) {
		throw new Error("Card parameter is missing");
	}

	const [cardsRes, elementsRes] = await Promise.all([
		getCardCardsValueGet({ path: { value: card }, headers }),
		getAllElementsGet({ headers })
	]);

	const cards = cardsRes.data ?? [];
	// Get variants by fetching cards for each card's handle
	const variantPromises = cards.map(c => getCardCardsValueGet({ path: { value: c.handle }, headers }));
	const variantResults = await Promise.all(variantPromises);
	const variants = variantResults.flatMap(r => r.data ?? []);

	return {
		card,
		cards,
		variants,
		elements: elementsRes.data ?? []
	};
};
