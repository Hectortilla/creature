import type { PageServerLoad } from "./$types";
import {
	getOneAssociationsValueGet,
	getCardsByAssociationCardsByAssociationAssociationCodeGet,
} from "$lib/api";
import { getAuthHeaders } from "$lib/server/auth";

export const load: PageServerLoad = async ({ params, locals }) => {
	const headers = getAuthHeaders(locals);
	const { association } = params;

	if (!association) {
		throw new Error("Association parameter is missing");
	}

	const [associationRes, cardsRes] = await Promise.all([
		getOneAssociationsValueGet({ path: { value: association }, headers }),
		getCardsByAssociationCardsByAssociationAssociationCodeGet({
			path: { association_code: Number(association) },
			headers,
		}),
	]);

	return {
		params,
		association: associationRes.data ?? null,
		cards_use_association: cardsRes.data ?? [],
	};
};
