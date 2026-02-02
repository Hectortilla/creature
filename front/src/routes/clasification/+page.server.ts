import type { PageServerLoad } from './$types';
import {
	getAllElementsGet,
	getAllTypesGet,
	getAllCharactersGet
} from '$lib/api';
import { getAuthHeaders } from '$lib/server/auth';

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const [elementsRes, typesRes, charactersRes] = await Promise.all([
		getAllElementsGet({ headers }),
		getAllTypesGet({ headers }),
		getAllCharactersGet({ headers })
	]);

	return {
		elements: elementsRes.data ?? [],
		types: typesRes.data ?? [],
		characters: charactersRes.data ?? []
	};
};
