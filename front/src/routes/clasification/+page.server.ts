import type { PageServerLoad } from './$types';
import {
	getAllElementsElementsGet,
	getAllTypesTypesGet,
	getAllCharactersCharactersGet
} from '$lib/api';
import { getAuthHeaders } from '$lib/server/auth';

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const [elementsRes, typesRes, charactersRes] = await Promise.all([
		getAllElementsElementsGet({ headers }),
		getAllTypesTypesGet({ headers }),
		getAllCharactersCharactersGet({ headers })
	]);

	return {
		elements: elementsRes.data ?? [],
		types: typesRes.data ?? [],
		characters: charactersRes.data ?? []
	};
};
