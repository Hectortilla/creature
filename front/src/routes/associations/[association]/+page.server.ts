import type { PageServerLoad } from './$types';
import {
	getAssociationAssociationsValueGet,
	getCardsByAssociationCardsByAssociationAssociationCodeGet
} from '$lib/api';

export const load: PageServerLoad = async ({ params }) => {
	const { association } = params;

	if (!association) {
		throw new Error("Association parameter is missing");
	}

	const [associationRes, cardsRes] = await Promise.all([
		getAssociationAssociationsValueGet({ path: { value: association } }),
		getCardsByAssociationCardsByAssociationAssociationCodeGet({ path: { association_code: Number(association) } })
	]);

	return {
		params,
		association: associationRes.data ?? null,
		cards_use_association: cardsRes.data ?? []
	};
};
