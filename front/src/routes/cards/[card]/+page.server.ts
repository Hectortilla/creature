import type { PageServerLoad } from './$types';
import {
	getCardCardsValueGet,
	getAllElementsElementsGet
} from '$lib/api';

export const load: PageServerLoad = async ({ params }) => {
	const { card } = params;

	if (!card) {
		throw new Error("Card parameter is missing");
	}

	const [cardsRes, elementsRes] = await Promise.all([
		getCardCardsValueGet({ path: { value: card } }),
		getAllElementsElementsGet()
	]);

	const cards = cardsRes.data ?? [];
	// Get variants by fetching cards for each card's handle
	const variantPromises = cards.map(c => getCardCardsValueGet({ path: { value: c.handle } }));
	const variantResults = await Promise.all(variantPromises);
	const variants = variantResults.flatMap(r => r.data ?? []);

	return {
		params,
		cards,
		variants,
		elements: elementsRes.data ?? []
	};
};
